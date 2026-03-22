variable "project" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "eks_node_security_group_id" { type = string }
variable "db_instance_class" { type = string default = "db.t3.micro" }
variable "allocated_storage" { type = number default = 20 }
variable "multi_az" { type = bool default = false }
variable "backup_retention_period" { type = number default = 1 }
variable "skip_final_snapshot" { type = bool default = true }
variable "deletion_protection" { type = bool default = false }
variable "db_name" { type = string }
variable "db_username" { type = string }
variable "db_password" { type = string sensitive = true }
variable "tags" { type = map(string) default = {} }
