# Build Lambda deployment package
resource "null_resource" "lambda_build" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      echo "Building Lambda deployment package..."
      
      # Clean build directory
      rm -rf ${path.module}/build
      mkdir -p ${path.module}/build
      
      # Install dependencies for Linux Lambda runtime (Python 3.11)
      echo "Installing dependencies for Python 3.11 on Linux x86_64..."
      pip3 install \
        fastmcp \
        boto3 \
        -t ${path.module}/build/ \
        --platform manylinux2014_x86_64 \
        --python-version 3.11 \
        --only-binary=:all: \
        --implementation cp \
        --quiet \
        --upgrade \
        --no-cache-dir
      
      # Copy application code
      cp ${path.module}/../app/*.py ${path.module}/build/
      cp -r ${path.module}/../app/vinyl ${path.module}/build/
      
      # Remove unnecessary files to reduce size
      find ${path.module}/build -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
      find ${path.module}/build -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
      find ${path.module}/build -name "*.pyc" -delete 2>/dev/null || true
      find ${path.module}/build -name "*.pyo" -delete 2>/dev/null || true
      
      # Remove boto3/botocore (already in Lambda runtime)
      rm -rf ${path.module}/build/boto3* ${path.module}/build/botocore* 2>/dev/null || true
      
      # Strip binary files to reduce size
      find ${path.module}/build -name "*.so" -exec strip {} + 2>/dev/null || true
      find ${path.module}/build -name "*.a" -delete 2>/dev/null || true
      
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
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
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

# Archive the Lambda package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build"
  output_path = "${path.module}/lambda.zip"

  depends_on = [null_resource.lambda_build]
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
