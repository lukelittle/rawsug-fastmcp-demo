# Build Lambda deployment package
resource "null_resource" "lambda_build" {
  triggers = {
    # Rebuild when source code changes
    source_hash = sha256(join("", [
      for f in fileset("${path.module}/../app", "**/*.py") :
      filesha256("${path.module}/../app/${f}")
    ]))
    requirements_hash = filesha256("${path.module}/../app/requirements.txt")
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      echo "Building Lambda deployment package..."
      
      # Clean build directory
      rm -rf ${path.module}/build
      mkdir -p ${path.module}/build
      
      # Install dependencies
      pip install -r ${path.module}/../app/requirements.txt -t ${path.module}/build/ --quiet
      
      # Copy application code
      cp -r ${path.module}/../app/*.py ${path.module}/build/
      cp -r ${path.module}/../app/vinyl ${path.module}/build/
      
      # Create zip
      cd ${path.module}/build
      zip -r ${path.module}/lambda.zip . -q
      
      echo "Lambda package built successfully"
    EOT
  }
}

# Lambda Function
resource "aws_lambda_function" "chatbot" {
  filename         = "${path.module}/lambda.zip"
  function_name    = "${var.project_name}-chatbot-${var.environment}"
  role            = aws_iam_role.lambda.arn
  handler         = "server.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      DISCOGS_BUCKET   = aws_s3_bucket.data.id
      DISCOGS_KEY      = "discogs.csv"
      USE_BEDROCK      = var.use_bedrock ? "true" : "false"
      BEDROCK_MODEL_ID = var.bedrock_model_id
      BEDROCK_REGION   = var.bedrock_region != "" ? var.bedrock_region : var.aws_region
    }
  }

  depends_on = [
    null_resource.lambda_build,
    aws_iam_role_policy.lambda_logs,
    aws_iam_role_policy.lambda_s3_data
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.chatbot.function_name}"
  retention_in_days = 7
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.chatbot.execution_arn}/*/*"
}
