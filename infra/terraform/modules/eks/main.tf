module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.project}-${var.environment}"
  cluster_version = "1.31"

  vpc_id                   = var.vpc_id
  subnet_ids               = var.private_subnet_ids
  control_plane_subnet_ids = var.private_subnet_ids

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      min_size     = var.environment == "prod" ? 2 : 1
      max_size     = var.environment == "prod" ? 6 : 3
      desired_size = var.environment == "prod" ? 2 : 1

      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"
    }
  }

  # Allow cluster to pull from ECR
  node_security_group_additional_rules = {
    egress_all = {
      description = "Node all egress"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "egress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  tags = var.tags
}
