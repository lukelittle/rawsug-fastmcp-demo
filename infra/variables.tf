variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "vinyl-chatbot"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "demo"
}

variable "use_bedrock" {
  description = "Enable Bedrock integration for enhanced responses"
  type        = bool
  default     = false
}

variable "bedrock_model_id" {
  description = "Bedrock model ID or inference profile ID to use"
  type        = string
  default     = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
}

variable "bedrock_region" {
  description = "AWS region for Bedrock (defaults to aws_region if not specified)"
  type        = string
  default     = ""
}
