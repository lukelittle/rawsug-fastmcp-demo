# Implementation Plan: Vinyl Collection Chatbot

## Overview

This implementation plan breaks down the vinyl collection chatbot into incremental, testable steps. The approach follows a bottom-up strategy: build core data handling first, then tools, then routing logic, then API layer, and finally infrastructure. Each step includes implementation and testing tasks to validate functionality early.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: app/, app/vinyl/, app/tests/, web/, infra/, architecture/
  - Create app/requirements.txt with dependencies: fastmcp, boto3, pytest, hypothesis, moto, python-dotenv
  - Create app/__init__.py and app/vinyl/__init__.py
  - Create .gitignore for Python, Terraform, and build artifacts
  - Create README.md with project overview and deployment instructions
  - _Requirements: 12.1, 12.7_

- [ ] 2. Implement Discogs CSV reader
  - [x] 2.1 Create DiscogsCollection class in app/vinyl/discogs.py
    - Implement __init__ with bucket and key parameters
    - Implement load() method to download CSV from S3 and parse with csv.DictReader
    - Implement _normalize() helper for case-insensitive string comparison
    - Implement _parse_year() helper to extract year from Released field
    - Implement _format_record() helper to format records as display strings
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7_
  
  - [x] 2.2 Implement query methods in DiscogsCollection
    - Implement query() method supporting artist, title, label, year, and all query types
    - Implement filter_records() method with artist, label, year_from, year_to parameters
    - Implement get_artists() method with starts_with and limit parameters
    - Implement get_stats() method returning collection statistics
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.9, 3.10, 3.13, 3.15, 3.16_
  
  - [x]* 2.3 Write unit tests for DiscogsCollection
    - Test CSV parsing with complete data
    - Test CSV parsing with missing columns
    - Test year extraction from various formats
    - Test case-insensitive matching
    - Test record formatting
    - Test empty collection handling
    - _Requirements: 11.2, 4.5, 4.8, 4.9, 4.12_
  
  - [ ]* 2.4 Write property test for case-insensitive search
    - **Property 3: Case-Insensitive Search Consistency**
    - **Validates: Requirements 3.2, 3.3, 3.4**
  
  - [ ]* 2.5 Write property test for year parsing
    - **Property 12: Year Parsing Correctness**
    - **Validates: Requirements 4.7**
  
  - [ ]* 2.6 Write property test for duplicate preservation
    - **Property 14: Duplicate Preservation**
    - **Validates: Requirements 4.11**

- [ ] 3. Implement FastMCP tools
  - [x] 3.1 Create FastMCP instance and tool registry in app/vinyl/tools.py
    - Import FastMCP and create mcp instance
    - Create get_collection() helper to initialize DiscogsCollection from environment
    - _Requirements: 2.1, 2.2_
  
  - [x] 3.2 Implement query_vinyl_collection tool
    - Define @mcp.tool() decorator with type hints for query_type, search_term, limit
    - Add comprehensive docstring with parameter descriptions and examples
    - Implement limit bounds validation (1-50)
    - Call collection.query() and format results
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [x] 3.3 Implement list_artists tool
    - Define @mcp.tool() decorator with type hints for starts_with, limit
    - Add comprehensive docstring
    - Implement limit bounds validation (1-100)
    - Call collection.get_artists() and return sorted unique list
    - _Requirements: 3.8, 3.9, 3.10, 3.11_
  
  - [x] 3.4 Implement stats_summary tool
    - Define @mcp.tool() decorator with no parameters
    - Add comprehensive docstring
    - Call collection.get_stats() and return complete statistics dictionary
    - _Requirements: 3.12, 3.13_
  
  - [x] 3.5 Implement filter_records tool
    - Define @mcp.tool() decorator with type hints for artist, label, year_from, year_to, limit
    - Add comprehensive docstring
    - Implement limit bounds validation (1-50)
    - Call collection.filter_records() and format results
    - _Requirements: 3.14, 3.15, 3.16_
  
  - [ ]* 3.6 Write unit tests for all tools
    - Test each tool with valid inputs
    - Test limit bounds clamping
    - Test no results scenarios
    - Test error handling
    - _Requirements: 11.3_
  
  - [ ]* 3.7 Write property test for limit parameter bounds
    - **Property 6: Limit Parameter Bounds**
    - **Validates: Requirements 3.7, 3.11**
  
  - [ ]* 3.8 Write property test for year query accuracy
    - **Property 4: Year Query Accuracy**
    - **Validates: Requirements 3.5**
  
  - [ ]* 3.9 Write property test for multi-field search coverage
    - **Property 5: Multi-Field Search Coverage**
    - **Validates: Requirements 3.6**
  
  - [ ]* 3.10 Write property test for artist list uniqueness and ordering
    - **Property 7: Artist List Uniqueness and Ordering**
    - **Validates: Requirements 3.9**
  
  - [ ]* 3.11 Write property test for artist prefix filtering
    - **Property 8: Artist Prefix Filtering**
    - **Validates: Requirements 3.10**
  
  - [ ]* 3.12 Write property test for stats response completeness
    - **Property 9: Stats Response Completeness**
    - **Validates: Requirements 3.13**
  
  - [ ]* 3.13 Write property test for multi-criteria filter conjunction
    - **Property 10: Multi-Criteria Filter Conjunction**
    - **Validates: Requirements 3.15**
  
  - [ ]* 3.14 Write property test for year range inclusivity
    - **Property 11: Year Range Inclusivity**
    - **Validates: Requirements 3.16**
  
  - [ ]* 3.15 Write property test for artist disambiguation flexibility
    - **Property 13: Artist Disambiguation Flexibility**
    - **Validates: Requirements 4.10**

- [ ] 4. Checkpoint - Ensure core data and tools work
  - Run all tests for DiscogsCollection and tools
  - Verify CSV parsing with sample data from data/discogs.csv
  - Verify all tools execute correctly with test data
  - Ask the user if questions arise

- [ ] 5. Implement deterministic router
  - [x] 5.1 Create router classes in app/vinyl/router.py
    - Define Intent enum with all intent types
    - Define RouterResult dataclass with tool_name, tool_args, fallback_response, confidence
    - Define DeterministicRouter class with route() method
    - _Requirements: 6.8_
  
  - [x] 5.2 Implement intent detection patterns
    - Implement _detect_intent() method with regex patterns for each intent type
    - Support artist query patterns: "what do I have by", "records by", "show me"
    - Support label query patterns: "anything on", "records on", "releases"
    - Support year query patterns: "records from", "releases", "stuff from"
    - Support year range patterns: "between X and Y", "from X to Y"
    - Support stats patterns: "how many", "stats", "summary"
    - Support list artists patterns: "list artists", "show artists", "what artists"
    - Support search patterns: "search", "find"
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [x] 5.3 Implement parameter extraction
    - Implement _extract_params() method to extract search terms and numeric values
    - Support case-insensitive extraction
    - Handle artist names with disambiguation numbers
    - Extract year values from various formats
    - _Requirements: 6.9, 4.10_
  
  - [x] 5.4 Implement fallback response generation
    - Generate polite fallback messages for unknown intents
    - Include example queries in fallback responses
    - _Requirements: 6.8_
  
  - [x]* 5.5 Write unit tests for router
    - Test each intent pattern with 10+ variations
    - Test parameter extraction accuracy
    - Test case-insensitive matching
    - Test fallback responses
    - _Requirements: 11.5_
  
  - [ ]* 5.6 Write property test for artist query intent detection
    - **Property 16: Artist Query Intent Detection**
    - **Validates: Requirements 6.1, 6.9**
  
  - [ ]* 5.7 Write property test for label query intent detection
    - **Property 17: Label Query Intent Detection**
    - **Validates: Requirements 6.2, 6.9**
  
  - [ ]* 5.8 Write property test for year query intent detection
    - **Property 18: Year Query Intent Detection**
    - **Validates: Requirements 6.3, 6.9**
  
  - [ ]* 5.9 Write property test for year range intent detection
    - **Property 19: Year Range Intent Detection**
    - **Validates: Requirements 6.4, 6.9**
  
  - [ ]* 5.10 Write property test for stats intent detection
    - **Property 20: Stats Intent Detection**
    - **Validates: Requirements 6.5**
  
  - [ ]* 5.11 Write property test for list artists intent detection
    - **Property 21: List Artists Intent Detection**
    - **Validates: Requirements 6.6**
  
  - [ ]* 5.12 Write property test for search intent detection
    - **Property 22: Search Intent Detection**
    - **Validates: Requirements 6.7, 6.9**
  
  - [ ]* 5.13 Write property test for fallback response
    - **Property 23: Fallback Response for Unknown Intent**
    - **Validates: Requirements 6.8**

- [ ] 6. Implement optional Bedrock client
  - [ ] 6.1 Create BedrockClient class in app/vinyl/bedrock.py
    - Define __init__ with model_id and region parameters
    - Initialize boto3 bedrock-runtime client
    - _Requirements: 7.2, 7.4, 7.5_
  
  - [ ] 6.2 Implement tool selection with Bedrock
    - Implement select_tool() method to invoke Bedrock with message and tool schemas
    - Format tool schemas for Bedrock API
    - Parse Bedrock response to extract tool name and arguments
    - Handle Bedrock errors gracefully
    - _Requirements: 7.6_
  
  - [ ] 6.3 Implement response generation with Bedrock
    - Implement generate_response() method to create conversational responses
    - Ground responses in tool results
    - Handle Bedrock errors gracefully
    - _Requirements: 7.7_
  
  - [ ]* 6.4 Write unit tests for Bedrock client with mocking
    - Mock boto3 bedrock-runtime client
    - Test tool selection with various messages
    - Test response generation with tool results
    - Test error handling
    - _Requirements: 11.8_

- [ ] 7. Implement Lambda handler
  - [x] 7.1 Create configuration loading in app/server.py
    - Define LambdaConfig dataclass
    - Implement from_env() class method to load from environment variables
    - Support DISCOGS_BUCKET, DISCOGS_KEY, USE_BEDROCK, BEDROCK_MODEL_ID, BEDROCK_REGION
    - _Requirements: 12.5, 7.4, 7.5_
  
  - [x] 7.2 Implement request routing in lambda_handler
    - Parse API Gateway event to extract HTTP method and path
    - Route POST /chat to handle_chat()
    - Route GET /tools to handle_tools()
    - Route GET /health to handle_health()
    - Return API Gateway response format with statusCode, headers, body
    - _Requirements: 5.1, 5.4, 5.5_
  
  - [x] 7.3 Implement handle_chat function
    - Parse request body JSON
    - Validate required message field
    - Determine mode (auto, deterministic, bedrock)
    - If deterministic mode: use DeterministicRouter
    - If bedrock mode: use BedrockClient (with fallback to deterministic)
    - Execute tool through FastMCP registry
    - Format response with answer, toolUsed, toolName, toolArgs, toolResults, requestId, model
    - _Requirements: 5.2, 5.3, 5.9, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 7.2, 7.8, 7.9, 7.10_
  
  - [x] 7.4 Implement handle_tools function
    - Call mcp.list_tools() to get tool definitions from FastMCP
    - Return JSON array with tool names, descriptions, and input schemas
    - _Requirements: 2.5_
  
  - [x] 7.5 Implement handle_health function
    - Return JSON with status "healthy" and current timestamp
    - _Requirements: 5.5_
  
  - [x] 7.6 Implement error handling and logging
    - Wrap all handlers in try-except blocks
    - Log errors to CloudWatch with structured logging
    - Return safe error messages without stack traces or sensitive details
    - Handle validation errors, data errors, tool errors, and external service errors
    - _Requirements: 10.1, 10.2, 10.3, 10.7, 10.8_
  
  - [ ]* 7.7 Write unit tests for Lambda handler
    - Test POST /chat with valid message
    - Test POST /chat with missing message field
    - Test POST /chat with invalid JSON
    - Test POST /chat with deterministic mode
    - Test POST /chat with bedrock mode (mocked)
    - Test GET /tools returns all schemas
    - Test GET /health returns 200
    - Test error handling for all error types
    - _Requirements: 11.6_
  
  - [ ]* 7.8 Write property test for tool schema completeness
    - **Property 1: Tool Schema Completeness**
    - **Validates: Requirements 2.3**
  
  - [ ]* 7.9 Write property test for parameter validation enforcement
    - **Property 2: Parameter Validation Enforcement**
    - **Validates: Requirements 2.4, 10.6**
  
  - [ ]* 7.10 Write property test for chat response structure completeness
    - **Property 15: Chat Response Structure Completeness**
    - **Validates: Requirements 5.3**
  
  - [ ]* 7.11 Write property test for error message safety
    - **Property 24: Error Message Safety**
    - **Validates: Requirements 10.2, 10.8**

- [ ] 8. Checkpoint - Ensure backend API works end-to-end
  - Run all tests for Lambda handler
  - Test with mocked S3 and sample CSV
  - Verify all API endpoints return correct responses
  - Verify error handling works correctly
  - Ask the user if questions arise

- [ ] 9. Create frontend chatbot UI
  - [x] 9.1 Create HTML structure in web/index.html
    - Create page layout with header, transcript panel, input area, examples panel
    - Add semantic HTML elements for accessibility
    - Include meta tags for responsive design
    - _Requirements: 9.1, 9.2_
  
  - [x] 9.2 Create CSS styling in web/styles.css
    - Style transcript panel with user and bot message bubbles
    - Style input field and send button
    - Style tool indicator and expandable tool results
    - Style loading state and error display
    - Style examples panel with clickable buttons
    - Implement responsive design for mobile and desktop
    - _Requirements: 9.4, 9.5, 9.6_
  
  - [x] 9.3 Create JavaScript application logic in web/app.js
    - Implement sendMessage() function to POST to /chat endpoint
    - Implement getTools() function to GET from /tools endpoint
    - Implement checkHealth() function to GET from /health endpoint
    - Implement renderMessage() to display user and bot messages
    - Implement renderToolResults() to display expandable tool results
    - Implement showLoading() and hideLoading() for loading states
    - Implement showError() for error display
    - Implement example button click handlers
    - _Requirements: 9.3, 9.4, 9.5, 9.6, 9.11_
  
  - [x] 9.4 Create configuration template in web/config.js.tmpl
    - Define window.__CONFIG__ object with API_BASE_URL placeholder
    - Add comments explaining Terraform will inject the actual URL
    - _Requirements: 9.10_
  
  - [x] 9.5 Add example queries to UI
    - "What records do I have by Grimes?"
    - "Do I have anything on 4AD?"
    - "Show me records from 2016"
    - "Give me a quick stats summary"
    - "List some artists"
    - _Requirements: 9.7, 9.8, 9.9_

- [ ] 10. Create Terraform infrastructure
  - [x] 10.1 Create Terraform configuration files in infra/
    - Create providers.tf with AWS provider configuration
    - Create variables.tf with input variables (region, project_name, environment)
    - Create terraform.tfvars.example with example values
    - _Requirements: 1.1, 12.2_
  
  - [x] 10.2 Create S3 buckets in infra/s3.tf
    - Create private S3 bucket for website origin with versioning
    - Create S3 bucket for Discogs CSV data
    - Block all public access on both buckets
    - Add bucket policies for CloudFront OAC and Lambda access
    - _Requirements: 1.2, 1.6, 8.6_
  
  - [x] 10.3 Create CloudFront distribution in infra/cloudfront.tf
    - Create Origin Access Control for S3 website bucket
    - Create CloudFront distribution with S3 origin
    - Set default root object to index.html
    - Configure cache behavior for static assets
    - Enable HTTPS only
    - _Requirements: 1.3, 8.7_
  
  - [x] 10.4 Create IAM roles and policies in infra/iam.tf
    - Create Lambda execution role with least-privilege permissions
    - Add policy for S3 read access to data bucket
    - Add policy for CloudWatch Logs write access
    - Conditionally add policy for Bedrock InvokeModel scoped to Claude 3.5 Haiku ARN
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 10.5 Create Lambda function in infra/lambda.tf
    - Create null_resource to build Lambda deployment package
    - Use local-exec to pip install requirements to build/ directory
    - Use local-exec to copy app code to build/ directory
    - Use local-exec to zip build/ into lambda.zip
    - Create Lambda function resource with Python 3.11 runtime
    - Set environment variables: DISCOGS_BUCKET, DISCOGS_KEY, USE_BEDROCK, BEDROCK_MODEL_ID, BEDROCK_REGION
    - Configure CloudWatch log group
    - _Requirements: 1.5, 12.5_
  
  - [x] 10.6 Create API Gateway in infra/apigw.tf
    - Create HTTP API Gateway
    - Create POST /chat route with Lambda integration
    - Create GET /tools route with Lambda integration
    - Create GET /health route with Lambda integration
    - Configure CORS to allow CloudFront origin
    - Enable access logging in structured JSON format
    - _Requirements: 1.4, 1.7, 1.8_
  
  - [x] 10.7 Create website deployment in infra/website.tf
    - Use templatefile to generate config.js from config.js.tmpl with API Gateway URL
    - Upload index.html, app.js, styles.css, config.js to S3 website bucket
    - Set correct content types for each file
    - _Requirements: 1.10_
  
  - [x] 10.8 Create outputs in infra/outputs.tf
    - Output CloudFront distribution URL
    - Output API Gateway URL
    - Output data bucket name for CSV upload
    - _Requirements: 1.8, 12.3_
  
  - [x] 10.9 Create main.tf to tie everything together
    - Reference all module files
    - Set up dependencies between resources
    - _Requirements: 1.1_

- [ ] 11. Create documentation
  - [x] 11.1 Create architecture diagram in architecture/diagram.md
    - Create Mermaid diagram showing all AWS components
    - Show data flow from user to CloudFront to API Gateway to Lambda to S3
    - Show optional Bedrock integration
    - _Requirements: 12.7_
  
  - [x] 11.2 Update README.md with complete documentation
    - Add project overview and demo story
    - Add architecture overview with link to diagram
    - Add prerequisites (AWS account, Terraform, Python 3.11)
    - Add deployment instructions step-by-step
    - Add instructions for uploading Discogs CSV
    - Add instructions for enabling Bedrock mode
    - Add testing instructions
    - Add troubleshooting section
    - Add cleanup instructions
    - _Requirements: 12.1, 12.3, 12.4_

- [ ] 12. Final integration and testing
  - [ ]* 12.1 Write integration tests in app/tests/test_integration.py
    - Test end-to-end flow from message to response
    - Test S3 CSV loading with moto
    - Test multiple tool executions
    - Test error propagation
    - _Requirements: 11.6_
  
  - [ ]* 12.2 Write edge case tests in app/tests/test_edge_cases.py
    - Test empty CSV file
    - Test CSV with only headers
    - Test malformed CSV rows
    - Test missing columns
    - Test unicode characters
    - Test special characters in queries
    - Test boundary values
    - _Requirements: 11.2_
  
  - [ ]* 12.3 Write error handling tests in app/tests/test_errors.py
    - Test S3 bucket not found
    - Test S3 access denied
    - Test CSV parsing errors
    - Test tool execution exceptions
    - Test Bedrock errors (mocked)
    - Test stack trace sanitization
    - _Requirements: 11.6, 10.8_
  
  - [ ] 12.4 Run full test suite and verify coverage
    - Run pytest with coverage report
    - Verify >90% code coverage
    - Verify all 24 property tests pass
    - Verify >150 total tests pass
    - _Requirements: 11.1, 11.9_
  
  - [x] 12.5 Create sample Discogs CSV for testing
    - Copy data/discogs.csv to app/tests/fixtures/sample.csv
    - Document expected CSV format in README
    - _Requirements: 12.4_

- [ ] 13. Final checkpoint - System ready for deployment
  - Verify all tests pass
  - Verify Terraform configuration is valid
  - Verify documentation is complete
  - Ask the user if ready to deploy or if any changes needed

## Notes

- Tasks marked with `*` are optional test tasks that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples, edge cases, and error conditions
- The implementation follows a bottom-up approach: data layer → tools → routing → API → infrastructure
- All AWS services are mocked in tests for local execution without credentials
