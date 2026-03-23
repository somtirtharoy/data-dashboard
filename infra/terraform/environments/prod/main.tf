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
    key            = "prod/terraform.tfstate"
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
  env         = "prod"
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
  vpc_cidr           = "10.2.0.0/16"
  azs                = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}d"]
  private_subnets    = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
  public_subnets     = ["10.2.101.0/24", "10.2.102.0/24", "10.2.103.0/24"]
  single_nat_gateway = false  # one NAT Gateway per AZ for high availability
  tags               = local.common_tags
}

module "eks" {
  source             = "../../modules/eks"
  project            = var.project
  environment        = local.env
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_instance_type = "t3.large"
  node_min_size      = 2
  node_max_size      = 6
  node_desired_size  = 2
  tags               = local.common_tags
}

module "rds" {
  source                     = "../../modules/rds"
  project                    = var.project
  environment                = local.env
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  eks_node_security_group_id = module.eks.cluster_name
  db_instance_class          = "db.t3.medium"
  allocated_storage          = 50
  multi_az                   = true   # standby replica in a second AZ
  backup_retention_period    = 7
  skip_final_snapshot        = false  # keep a snapshot on destroy
  deletion_protection        = true   # prevents accidental terraform destroy
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
