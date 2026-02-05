# Requirements Document

## Introduction

This document specifies the requirements for a production-ready FastMCP vinyl collection chatbot demo on AWS. The system enables users to interact with their Discogs vinyl collection through a natural language chatbot interface, demonstrating Model Context Protocol (MCP) and FastMCP integration on AWS infrastructure. The demo showcases serverless agentic AI patterns with real web UI, API Gateway + Lambda backend, and S3-based data storage.

## Glossary

- **System**: The complete vinyl collection chatbot application including frontend, backend, and infrastructure
- **FastMCP**: The Python library used for MCP tool definition, schema validation, and registry
- **Chatbot_UI**: The web-based user interface for interacting with the vinyl collection
- **Backend_API**: The Lambda-based API that processes chat requests and executes tools
- **Tool_Registry**: The FastMCP-managed collection of available tools and their schemas
- **Discogs_CSV**: The CSV file containing the user's vinyl collection exported from Discogs
- **Deterministic_Router**: The rules-based component that infers tool usage without LLM reasoning
- **Bedrock_Mode**: Optional mode using AWS Bedrock Claude 3.5 Haiku for tool selection and response generation
- **CloudFront_Distribution**: The CDN serving the static web UI
- **Data_Bucket**: The S3 bucket storing the Discogs CSV file
- **Website_Bucket**: The private S3 bucket containing static web assets

## Requirements

### Requirement 1: Infrastructure Deployment

**User Story:** As a developer, I want to deploy the complete system using Terraform, so that I can provision all AWS resources with infrastructure-as-code.

#### Acceptance Criteria

1. THE System SHALL provision all infrastructure using Terraform exclusively
2. WHEN Terraform is applied, THE System SHALL create a private S3 bucket for website origin
3. WHEN Terraform is applied, THE System SHALL create a CloudFront distribution with Origin Access Control
4. WHEN Terraform is applied, THE System SHALL create an HTTP API Gateway with POST /chat, GET /tools, and GET /health routes
5. WHEN Terraform is applied, THE System SHALL create a Python 3.11 Lambda function with CloudWatch logging
6. WHEN Terraform is applied, THE System SHALL create a separate S3 bucket for Discogs CSV storage
7. WHEN Terraform is applied, THE System SHALL configure CORS on API Gateway to allow CloudFront origin
8. WHEN Terraform is applied, THE System SHALL output the CloudFront URL and API Gateway URL
9. WHEN Lambda code changes, THE System SHALL package dependencies and application code into a deployment zip
10. WHEN static assets are deployed, THE System SHALL inject API base URL into frontend configuration

### Requirement 2: FastMCP Tool Integration

**User Story:** As a system architect, I want to use FastMCP for all tool definitions and validation, so that the system follows MCP standards and provides reliable schema-based tool execution.

#### Acceptance Criteria

1. THE Backend_API SHALL instantiate a FastMCP object for tool management
2. THE Backend_API SHALL register all tools using @mcp.tool() decorators
3. WHEN a tool is registered, THE FastMCP SHALL generate JSON schemas from type hints and docstrings
4. WHEN a tool is invoked, THE FastMCP SHALL validate input parameters against generated schemas
5. WHEN GET /tools is called, THE Backend_API SHALL return tool definitions from the FastMCP registry
6. THE Backend_API SHALL invoke tools exclusively through the FastMCP tool registry
7. THE Backend_API SHALL NOT bypass FastMCP validation or manually implement schemas

### Requirement 3: Vinyl Collection Tools

**User Story:** As a user, I want to query my vinyl collection using natural language, so that I can find records by artist, title, label, year, and other attributes.

#### Acceptance Criteria

1. THE Tool_Registry SHALL provide a query_vinyl_collection tool accepting query_type, search_term, and limit parameters
2. WHEN query_vinyl_collection is called with query_type "artist", THE System SHALL return records matching the artist name case-insensitively
3. WHEN query_vinyl_collection is called with query_type "title", THE System SHALL return records matching the title case-insensitively
4. WHEN query_vinyl_collection is called with query_type "label", THE System SHALL return records matching the label name case-insensitively
5. WHEN query_vinyl_collection is called with query_type "year", THE System SHALL return records matching the specified year
6. WHEN query_vinyl_collection is called with query_type "all", THE System SHALL search across artist, title, and label fields
7. WHEN query_vinyl_collection is called with a limit parameter, THE System SHALL constrain results between 1 and 50 records
8. THE Tool_Registry SHALL provide a list_artists tool accepting starts_with and limit parameters
9. WHEN list_artists is called, THE System SHALL return unique artist names sorted alphabetically
10. WHEN list_artists is called with starts_with parameter, THE System SHALL filter artists beginning with the specified string case-insensitively
11. WHEN list_artists is called with a limit parameter, THE System SHALL constrain results between 1 and 100 artists
12. THE Tool_Registry SHALL provide a stats_summary tool returning collection statistics
13. WHEN stats_summary is called, THE System SHALL return total_records, unique_artists, unique_labels, year_min, year_max, top_artists, and top_labels
14. THE Tool_Registry SHALL provide a filter_records tool accepting artist, label, year_from, year_to, and limit parameters
15. WHEN filter_records is called with multiple criteria, THE System SHALL return records matching all specified filters
16. WHEN filter_records is called with year_from and year_to, THE System SHALL return records within the inclusive year range

### Requirement 4: Discogs CSV Processing

**User Story:** As a user, I want the system to read my Discogs CSV export, so that my vinyl collection data is available for querying.

#### Acceptance Criteria

1. WHEN Lambda starts, THE Backend_API SHALL download the Discogs CSV from the Data_Bucket
2. WHEN the CSV is downloaded, THE Backend_API SHALL cache it within the Lambda invocation
3. WHEN parsing the CSV, THE System SHALL use csv.DictReader for parsing
4. WHEN parsing the CSV, THE System SHALL normalize field values by stripping whitespace and converting to lowercase for comparisons
5. WHEN a required column is missing, THE System SHALL log a warning and continue with partial functionality
6. THE System SHALL support Discogs export columns including Catalog#, Artist, Title, Label, Format, Rating, Released, release_id, CollectionFolder, Date Added, Collection Media Condition, and Collection Sleeve Condition
7. WHEN the CSV contains "Released" column with year values, THE System SHALL parse the year as an integer for filtering
8. WHEN the "Released" column contains empty values, THE System SHALL handle missing years gracefully in year-based queries
9. WHEN field access fails, THE System SHALL handle missing values gracefully without raising exceptions
10. WHEN artist names contain disambiguation numbers in parentheses, THE System SHALL support searching with or without the disambiguation
11. WHEN the CSV contains duplicate entries with the same release_id, THE System SHALL include all entries in query results
12. WHEN Collection Media Condition or Collection Sleeve Condition fields are empty, THE System SHALL treat them as ungraded records

### Requirement 5: Chat API Contract

**User Story:** As a frontend developer, I want a well-defined API contract, so that I can integrate the chatbot UI with the backend reliably.

#### Acceptance Criteria

1. WHEN POST /chat receives a request, THE Backend_API SHALL accept a JSON body with message, sessionId, and mode fields
2. WHEN POST /chat receives a request without a message field, THE Backend_API SHALL return an error response
3. WHEN POST /chat processes a request, THE Backend_API SHALL return JSON with answer, toolUsed, toolName, toolArgs, toolResults, requestId, and model fields
4. WHEN GET /tools is called, THE Backend_API SHALL return a JSON array of tool definitions with names, descriptions, and JSON schemas
5. WHEN GET /health is called, THE Backend_API SHALL return a 200 status with JSON indicating service health
6. WHEN a tool is executed, THE Backend_API SHALL include the tool name in the toolName response field
7. WHEN a tool is executed, THE Backend_API SHALL include the tool arguments in the toolArgs response field
8. WHEN a tool is executed, THE Backend_API SHALL include the tool results in the toolResults response field
9. WHEN no tool is executed, THE Backend_API SHALL set toolUsed to false and toolName to null

### Requirement 6: Deterministic Routing

**User Story:** As a user, I want the chatbot to understand my queries without requiring an LLM, so that the system works reliably and cost-effectively.

#### Acceptance Criteria

1. WHEN a message contains "what do I have by <artist>", THE Deterministic_Router SHALL select query_vinyl_collection with query_type "artist"
2. WHEN a message contains "do I have anything on <label>", THE Deterministic_Router SHALL select query_vinyl_collection with query_type "label"
3. WHEN a message contains "records from <year>", THE Deterministic_Router SHALL select query_vinyl_collection with query_type "year"
4. WHEN a message contains "between <year> and <year>", THE Deterministic_Router SHALL select filter_records with year_from and year_to parameters
5. WHEN a message contains "how many records" or "stats" or "summary", THE Deterministic_Router SHALL select stats_summary
6. WHEN a message contains "list artists", THE Deterministic_Router SHALL select list_artists
7. WHEN a message contains "search <term>", THE Deterministic_Router SHALL select query_vinyl_collection with query_type "all"
8. WHEN no tool intent is detected, THE Deterministic_Router SHALL return a polite response suggesting example queries
9. WHEN extracting parameters from user messages, THE Deterministic_Router SHALL infer search terms and numeric values using pattern matching

### Requirement 7: Optional Bedrock Integration

**User Story:** As a system operator, I want optional Bedrock integration for enhanced conversational responses, so that I can demonstrate LLM-powered tool selection while maintaining a working fallback.

#### Acceptance Criteria

1. WHEN USE_BEDROCK environment variable is false, THE System SHALL use deterministic routing exclusively
2. WHEN USE_BEDROCK environment variable is true, THE System SHALL use AWS Bedrock for tool selection and response generation
3. WHERE Bedrock is enabled, THE System SHALL use Claude 3.5 Haiku model
4. WHERE Bedrock is enabled, THE System SHALL read BEDROCK_MODEL_ID from environment with default "anthropic.claude-3-5-haiku-20241022-v1:0"
5. WHERE Bedrock is enabled, THE System SHALL read BEDROCK_REGION from environment with default from Lambda region
6. WHERE Bedrock is enabled, WHEN tool selection occurs, THE System SHALL invoke Bedrock to choose tool and arguments from FastMCP schemas
7. WHERE Bedrock is enabled, WHEN tool execution completes, THE System SHALL invoke Bedrock to draft a conversational response grounded in tool output
8. WHERE Bedrock is enabled, WHEN a response is generated, THE System SHALL include "claude-3.5-haiku" in the model response field
9. WHEN USE_BEDROCK is false, THE System SHALL set the model response field to null
10. WHERE Bedrock is enabled, THE System SHALL execute tools through FastMCP registry regardless of selection method

### Requirement 8: Security and IAM

**User Story:** As a security engineer, I want least-privilege IAM policies and secure resource access, so that the system follows AWS security best practices.

#### Acceptance Criteria

1. THE System SHALL create IAM roles with least-privilege permissions for Lambda execution
2. THE Lambda_Role SHALL include permissions to read from the Data_Bucket
3. THE Lambda_Role SHALL include permissions to write CloudWatch logs
4. WHERE Bedrock is enabled, THE Lambda_Role SHALL include bedrock:InvokeModel permission scoped to Claude 3.5 Haiku model ARN
5. THE Lambda_Role SHALL NOT include wildcard bedrock:* permissions
6. THE Website_Bucket SHALL be private with no public access
7. THE CloudFront_Distribution SHALL access the Website_Bucket using Origin Access Control
8. THE System SHALL NOT expose AWS credentials or secrets in the frontend
9. THE API_Gateway SHALL enforce CORS policies to restrict cross-origin requests

### Requirement 9: Chatbot User Interface

**User Story:** As a user, I want an intuitive web interface to chat about my vinyl collection, so that I can interact with the system naturally.

#### Acceptance Criteria

1. THE Chatbot_UI SHALL display a transcript panel showing user and bot messages
2. THE Chatbot_UI SHALL provide an input field and send button for user messages
3. WHEN a tool is used, THE Chatbot_UI SHALL display a tool indicator showing the tool name
4. WHEN a tool returns results, THE Chatbot_UI SHALL display tool results in an expandable/collapsible section
5. WHEN a request is processing, THE Chatbot_UI SHALL display a loading state
6. WHEN an error occurs, THE Chatbot_UI SHALL display the error message to the user
7. THE Chatbot_UI SHALL provide an examples panel with clickable example queries
8. THE Chatbot_UI SHALL include example queries for artist search, label search, year filtering, stats summary, and artist listing
9. WHEN an example is clicked, THE Chatbot_UI SHALL populate the input field with the example text
10. WHEN the frontend loads, THE Chatbot_UI SHALL read API base URL from window.__CONFIG__.API_BASE_URL
11. WHEN sending a message, THE Chatbot_UI SHALL POST to ${API_BASE_URL}/chat with JSON payload
12. WHERE Bedrock is used, THE Chatbot_UI SHALL optionally display which model generated the response

### Requirement 10: Error Handling and Logging

**User Story:** As a system operator, I want comprehensive error handling and logging, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. WHEN a tool execution fails, THE Backend_API SHALL log the error to CloudWatch
2. WHEN a tool execution fails, THE Backend_API SHALL return a safe error message to the client without exposing internal details
3. WHEN the Discogs CSV cannot be loaded, THE Backend_API SHALL return an error response indicating data unavailability
4. WHEN API Gateway receives requests, THE System SHALL log access logs in structured JSON format
5. WHEN Lambda executes, THE System SHALL log invocation details to CloudWatch
6. WHEN parameter validation fails, THE FastMCP SHALL return validation errors with field-specific messages
7. WHEN an unexpected exception occurs, THE Backend_API SHALL catch it and return a generic error response
8. THE System SHALL NOT expose stack traces or sensitive information in client-facing error messages

### Requirement 11: Testing and Quality Assurance

**User Story:** As a developer, I want comprehensive automated tests, so that I can verify system correctness without deploying to AWS.

#### Acceptance Criteria

1. THE System SHALL include pytest-based unit tests for all components
2. THE System SHALL test Discogs CSV parsing with sample data
3. THE System SHALL test query_vinyl_collection behavior including case-insensitivity, limits, and no-match scenarios
4. THE System SHALL test stats_summary correctness on sample CSV data
5. THE System SHALL test Deterministic_Router intent detection and parameter inference
6. THE System SHALL test Backend_API handler end-to-end with mocked S3
7. WHEN tests run, THE System SHALL mock all AWS service calls using botocore Stubber or moto
8. WHERE Bedrock code exists, THE System SHALL mock Bedrock calls entirely without network requests
9. THE System SHALL run all tests locally without requiring AWS credentials

### Requirement 12: Deployment and Configuration

**User Story:** As a developer, I want clear deployment instructions and configuration management, so that I can deploy the system quickly and reliably.

#### Acceptance Criteria

1. THE System SHALL provide a README with step-by-step deployment instructions
2. THE System SHALL provide a terraform.tfvars.example file with required variables
3. WHEN deploying, THE System SHALL document how to upload Discogs CSV to the Data_Bucket
4. WHEN deploying, THE System SHALL document expected CSV column names
5. THE System SHALL configure Lambda environment variables for DISCOGS_BUCKET, DISCOGS_KEY, USE_BEDROCK, BEDROCK_MODEL_ID, and BEDROCK_REGION
6. WHEN Terraform generates frontend config, THE System SHALL use templatefile to inject API_BASE_URL
7. THE System SHALL provide architecture documentation with diagrams
8. THE System SHALL include a .gitignore file excluding Terraform state, Python cache, and build artifacts
