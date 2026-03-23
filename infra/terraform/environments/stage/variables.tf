variable "project" {
  type    = string
  default = "data-dashboard"
}

variable "aws_region" {
  type    = string
  default = "ca-central-1"
}

variable "db_username" {
  type    = string
  default = "dashboard"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "lambda_zip_path" {
  type    = string
  default = "../../../../lambda/processor/function.zip"
}
