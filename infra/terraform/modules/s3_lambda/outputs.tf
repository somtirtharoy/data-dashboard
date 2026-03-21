output "bucket_name" { value = aws_s3_bucket.uploads.id }
output "lambda_function_name" { value = aws_lambda_function.processor.function_name }
output "lambda_security_group_id" { value = aws_security_group.lambda.id }
