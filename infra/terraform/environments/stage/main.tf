terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "bcgov-data-dashboard-tfstate"
    key            = "stage/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "bcgov-data-dashboard-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  env         = "stage"
  common_tags = {
    Project     = var.project
    Environment = local.env
    ManagedBy   = "Terraform"
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  project            = var.project
  environment        = local.env
  vpc_cidr           = "10.1.0.0/16"
  azs                = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets    = ["10.1.1.0/24", "10.1.2.0/24"]
  public_subnets     = ["10.1.101.0/24", "10.1.102.0/24"]
  single_nat_gateway = true   # single NAT to save cost; stage doesn't need AZ-level NAT HA
  tags               = local.common_tags
}

module "eks" {
  source             = "../../modules/eks"
  project            = var.project
  environment        = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_instance_type = "t3.medium"
  node_min_size      = 1
  node_max_size      = 4
  node_desired_size  = 1
  tags               = local.common_tags
}

module "rds" {
  source                     = "../../modules/rds"
  project                    = var.project
  environment                = local.env
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  eks_node_security_group_id = module.eks.cluster_name
  db_instance_class          = "db.t3.small"
  allocated_storage          = 30
  multi_az                   = false
  backup_retention_period    = 3
  skip_final_snapshot        = true
  deletion_protection        = false
  db_name                    = "dashboard"
  db_username                = var.db_username
  db_password                = var.db_password
  tags                       = local.common_tags
}

module "s3_lambda" {
  source             = "../../modules/s3_lambda"
  project            = var.project
  environment        = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  lambda_zip_path    = var.lambda_zip_path
  db_host            = module.rds.db_endpoint
  db_name            = "dashboard"
  db_username        = var.db_username
  db_password        = var.db_password
  tags               = local.common_tags
}
