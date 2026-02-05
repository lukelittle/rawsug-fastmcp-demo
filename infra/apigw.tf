# HTTP API Gateway
resource "aws_apigatewayv2_api" "chatbot" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]  # For demo - lock down to CloudFront domain in production
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.chatbot.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.chatbot.invoke_arn

  payload_format_version = "2.0"
}

# POST /chat Route
resource "aws_apigatewayv2_route" "chat" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# GET /tools Route
resource "aws_apigatewayv2_route" "tools" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "GET /tools"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# GET /health Route
resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Default Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.chatbot.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
    })
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7
}
