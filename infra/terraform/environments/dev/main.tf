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
    key            = "dev/terraform.tfstate"
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
  common_tags = {
    Project     = var.project
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

module "vpc" {
  source      = "../../modules/vpc"
  project     = var.project
  environment = "dev"
  vpc_cidr    = "10.0.0.0/16"
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  tags            = local.common_tags
}

module "eks" {
  source             = "../../modules/eks"
  project            = var.project
  environment        = "dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  tags               = local.common_tags
}

module "rds" {
  source                     = "../../modules/rds"
  project                    = var.project
  environment                = "dev"
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  eks_node_security_group_id = module.eks.cluster_name  # pass correct SG in practice
  db_name                    = "dashboard"
  db_username                = var.db_username
  db_password                = var.db_password
  tags                       = local.common_tags
}

module "s3_lambda" {
  source             = "../../modules/s3_lambda"
  project            = var.project
  environment        = "dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  lambda_zip_path    = var.lambda_zip_path
  db_host            = module.rds.db_endpoint
  db_name            = "dashboard"
  db_username        = var.db_username
  db_password        = var.db_password
  tags               = local.common_tags
}
