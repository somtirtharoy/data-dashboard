output "cluster_name" { value = module.eks.cluster_name }
output "rds_endpoint" { value = module.rds.db_endpoint }
output "s3_bucket" { value = module.s3_lambda.bucket_name }
