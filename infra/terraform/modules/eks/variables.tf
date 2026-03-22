variable "project" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "node_instance_type" { type = string default = "t3.medium" }
variable "node_min_size" { type = number default = 1 }
variable "node_max_size" { type = number default = 3 }
variable "node_desired_size" { type = number default = 1 }
variable "tags" { type = map(string) default = {} }
