output "cloudfront_url" {
  description = "CloudFront distribution URL for the chatbot UI"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "data_bucket_name" {
  description = "S3 bucket name for uploading discogs.csv"
  value       = aws_s3_bucket.data.id
}

output "website_bucket_name" {
  description = "S3 bucket name for website assets"
  value       = aws_s3_bucket.website.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.chatbot.function_name
}

output "deployment_instructions" {
  description = "Next steps after deployment"
  value       = <<-EOT
    
    ✅ Deployment Complete!
    
    Next Steps:
    
    1. Upload your Discogs CSV:
       aws s3 cp /path/to/discogs.csv s3://${aws_s3_bucket.data.id}/discogs.csv
    
    2. Access the chatbot:
       https://${aws_cloudfront_distribution.website.domain_name}
    
    3. Test the API:
       curl ${aws_apigatewayv2_stage.default.invoke_url}/health
    
    4. View Lambda logs:
       aws logs tail /aws/lambda/${aws_lambda_function.chatbot.function_name} --follow
    
    Enjoy your vinyl collection chatbot! 🎵
  EOT
}
