# FastMCP Vinyl Collection Chatbot

A production-ready serverless chatbot demonstrating Model Context Protocol (MCP) and FastMCP on AWS. Built for live AWS User Group demo in Richmond.

## Overview

This project showcases:
- **MCP**: Universal contract for agent-to-tool integration
- **FastMCP**: Easy tool authoring with schemas, validation, and registry
- **AWS Serverless**: S3 + CloudFront for web UI, API Gateway + Lambda for backend
- **Agentic AI**: Deterministic routing with optional Bedrock enhancement

Chat naturally about your vinyl collection:
- "What records do I have by Grimes?"
- "Do I have anything on 4AD?"
- "Show me records from 2016"
- "Give me a quick stats summary"

## Architecture

```
User Browser
    ↓ HTTPS
CloudFront Distribution
    ↓ OAC
S3 Website Bucket (Private)

User Browser
    ↓ API Calls
API Gateway (HTTP API)
    ↓ Invoke
Lambda Function (Python 3.11)
    ↓ Read CSV
S3 Data Bucket (discogs.csv)
    ↓ Logs
CloudWatch Logs
    ↓ Optional
AWS Bedrock (Claude 3.5 Haiku)
```

See [architecture/diagram.md](architecture/diagram.md) for detailed diagrams.

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.5.0
- Python 3.11
- AWS CLI configured with credentials
- Discogs CSV export of your vinyl collection

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd vinyl-collection-chatbot
pip install -r app/requirements.txt
```

### 2. Run Tests

```bash
cd app
pytest -v
```

### 3. Deploy Infrastructure

```bash
cd infra

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your AWS region and project name

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### 4. Upload Your Discogs CSV

After deployment, Terraform outputs the data bucket name:

```bash
# Get bucket name from Terraform output
DATA_BUCKET=$(terraform output -raw data_bucket_name)

# Upload your Discogs CSV
aws s3 cp /path/to/your/discogs.csv s3://${DATA_BUCKET}/discogs.csv
```

### 5. Access the Chatbot

Terraform outputs the CloudFront URL:

```bash
terraform output cloudfront_url
```

Open this URL in your browser to start chatting!

## Discogs CSV Format

Export your collection from Discogs. The system expects these columns:
- `Catalog#` - Catalog number
- `Artist` - Artist name
- `Title` - Album/release title
- `Label` - Record label
- `Format` - Format (Vinyl, CD, etc.)
- `Rating` - Your rating
- `Released` - Release year
- `release_id` - Discogs release ID
- `CollectionFolder` - Folder name
- `Date Added` - Date added to collection
- `Collection Media Condition` - Media condition
- `Collection Sleeve Condition` - Sleeve condition

Missing columns are handled gracefully with partial functionality.

## Optional: Enable Bedrock Mode

By default, the system uses deterministic routing. To enable Bedrock for enhanced conversational responses:

1. Ensure your AWS account has access to Claude 3.5 Haiku in Bedrock
2. Update Lambda environment variables in `infra/lambda.tf`:
   ```hcl
   environment {
     variables = {
       USE_BEDROCK = "true"
       BEDROCK_MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"
       BEDROCK_REGION = "us-east-1"
       # ... other variables
     }
   }
   ```
3. Redeploy: `terraform apply`

## Development

### Project Structure

```
├── app/                    # Backend application
│   ├── server.py          # Lambda handler
│   ├── requirements.txt   # Python dependencies
│   ├── vinyl/             # Core modules
│   │   ├── discogs.py    # CSV reader
│   │   ├── router.py     # Deterministic router
│   │   └── tools.py      # FastMCP tools
│   └── tests/            # Test suite
├── web/                   # Frontend
│   ├── index.html        # Chatbot UI
│   ├── app.js            # Application logic
│   ├── styles.css        # Styling
│   └── config.js.tmpl    # Config template
├── infra/                # Terraform infrastructure
│   ├── main.tf
│   ├── providers.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── iam.tf
│   ├── apigw.tf
│   ├── lambda.tf
│   ├── s3.tf
│   ├── cloudfront.tf
│   └── website.tf
└── architecture/         # Documentation
    └── diagram.md
```

### Running Tests Locally

```bash
cd app
pytest -v                    # Run all tests
pytest -v -k test_discogs   # Run specific test file
pytest -v --cov=vinyl       # Run with coverage
```

All tests use mocked AWS services (moto) and run without credentials.

### API Endpoints

- `POST /chat` - Process chat message
  - Request: `{ "message": "string", "sessionId": "string", "mode": "auto|deterministic|bedrock" }`
  - Response: `{ "answer": "string", "toolUsed": bool, "toolName": "string", ... }`
- `GET /tools` - List available tools and schemas
- `GET /health` - Health check

## Tools

The chatbot provides four FastMCP tools:

1. **query_vinyl_collection** - Query by artist, title, label, year, or all fields
2. **list_artists** - List unique artists with optional prefix filter
3. **stats_summary** - Get collection statistics
4. **filter_records** - Filter by multiple criteria with year ranges

## Troubleshooting

### Lambda can't read CSV
- Verify CSV is uploaded to the data bucket
- Check Lambda IAM role has S3 read permissions
- Check CloudWatch logs for detailed errors

### Frontend can't reach API
- Verify CORS is configured on API Gateway
- Check CloudFront distribution is deployed
- Verify config.js has correct API_BASE_URL

### Tests failing
- Ensure Python 3.11 is installed
- Install all dependencies: `pip install -r app/requirements.txt`
- Check that moto is properly installed for AWS mocking

## Cleanup

To remove all AWS resources:

```bash
cd infra
terraform destroy
```

Note: S3 buckets with content may need to be emptied first.

## License

MIT License - See LICENSE file for details

## Demo Notes

This is a production-ready demo showcasing:
- FastMCP tool definitions with automatic schema generation
- Serverless AWS architecture with least-privilege IAM
- Deterministic routing that works without LLMs
- Optional Bedrock integration for enhanced responses
- Comprehensive testing with property-based tests
- Infrastructure-as-code with Terraform

Perfect for demonstrating modern agentic AI patterns on AWS!
