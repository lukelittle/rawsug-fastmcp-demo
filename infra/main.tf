# Main Terraform Configuration
# This file ties together all infrastructure components

# All resources are defined in their respective files:
# - providers.tf: AWS provider configuration
# - variables.tf: Input variables
# - s3.tf: S3 buckets for website and data
# - iam.tf: IAM roles and policies
# - lambda.tf: Lambda function and build process
# - apigw.tf: API Gateway configuration
# - cloudfront.tf: CloudFront distribution
# - website.tf: Website deployment
# - outputs.tf: Output values

# Resource dependencies are managed through implicit references
# Terraform will automatically determine the correct order of operations
