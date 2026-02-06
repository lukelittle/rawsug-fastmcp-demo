# Lambda Execution Role
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs Policy
resource "aws_iam_role_policy" "lambda_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-*"
      }
    ]
  })
}

# S3 Data Bucket Read Policy
resource "aws_iam_role_policy" "lambda_s3_data" {
  name = "s3-data-read"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      }
    ]
  })
}

# Bedrock Policy (Conditional)
resource "aws_iam_role_policy" "lambda_bedrock" {
  count = var.use_bedrock ? 1 : 0

  name = "bedrock-invoke"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/*",
          "arn:aws:bedrock:us-east-2::foundation-model/*",
          "arn:aws:bedrock:us-west-2::foundation-model/*",
          "arn:aws:bedrock:us-east-1:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          "arn:aws:bedrock:us-east-2:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          "arn:aws:bedrock:us-west-2:${data.aws_caller_identity.current.account_id}:inference-profile/*"
        ]
      }
    ]
  })
}
