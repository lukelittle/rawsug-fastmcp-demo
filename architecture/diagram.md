# Architecture Diagram

## High-Level Architecture

```mermaid
graph TB
    User[User Browser]
    CF[CloudFront Distribution]
    S3Web[S3 Website Bucket<br/>Private]
    APIGW[API Gateway<br/>HTTP API]
    Lambda[Lambda Function<br/>Python 3.11]
    S3Data[S3 Data Bucket<br/>discogs.csv]
    CW[CloudWatch Logs]
    Bedrock[AWS Bedrock<br/>Claude 3.5 Haiku<br/>Optional]
    
    User -->|HTTPS| CF
    CF -->|OAC| S3Web
    User -->|API Calls| APIGW
    APIGW -->|Invoke| Lambda
    Lambda -->|Read CSV| S3Data
    Lambda -->|Logs| CW
    Lambda -.->|Optional| Bedrock
    
    style Bedrock stroke-dasharray: 5 5
    style S3Web fill:#f9f,stroke:#333
    style Lambda fill:#ff9,stroke:#333
    style APIGW fill:#9f9,stroke:#333
```

## Component Architecture

```mermaid
graph TB
    subgraph "Frontend (Static)"
        UI[Chatbot UI<br/>HTML/CSS/JS]
        Config[config.js<br/>API URL]
    end
    
    subgraph "Backend (Lambda)"
        Handler[Lambda Handler<br/>server.py]
        FastMCP[FastMCP Registry]
        Router[Deterministic Router]
        Tools[Tool Implementations]
        Discogs[Discogs CSV Reader]
        BedrockClient[Bedrock Client<br/>Optional]
        
        Handler --> Router
        Handler --> FastMCP
        Router --> FastMCP
        FastMCP --> Tools
        Tools --> Discogs
        Router -.-> BedrockClient
    end
    
    UI --> Handler
    Config --> UI
    
    style BedrockClient stroke-dasharray: 5 5
```

## Request Flow - Deterministic Mode

```mermaid
sequenceDiagram
    participant User
    participant CloudFront
    participant S3
    participant APIGW as API Gateway
    participant Lambda
    participant FastMCP
    participant S3Data as S3 Data

    User->>CloudFront: Load UI
    CloudFront->>S3: Get static files
    S3-->>CloudFront: HTML/CSS/JS
    CloudFront-->>User: Render UI
    
    User->>APIGW: POST /chat {"message": "..."}
    APIGW->>Lambda: Invoke
    Lambda->>S3Data: Get discogs.csv (cached)
    S3Data-->>Lambda: CSV data
    Lambda->>Lambda: Deterministic Router<br/>Detect intent
    Lambda->>FastMCP: Call tool with args
    FastMCP->>FastMCP: Validate params
    FastMCP->>Lambda: Execute tool
    Lambda->>Lambda: Format response
    Lambda-->>APIGW: Response JSON
    APIGW-->>User: Display results
```

## Request Flow - Bedrock Mode (Optional)

```mermaid
sequenceDiagram
    participant User
    participant APIGW as API Gateway
    participant Lambda
    participant Bedrock
    participant FastMCP
    participant S3Data as S3 Data

    User->>APIGW: POST /chat {"message": "..."}
    APIGW->>Lambda: Invoke
    Lambda->>S3Data: Get discogs.csv (cached)
    S3Data-->>Lambda: CSV data
    Lambda->>Bedrock: Select tool<br/>(message + tool schemas)
    Bedrock-->>Lambda: Tool name + args
    Lambda->>FastMCP: Call tool with args
    FastMCP->>FastMCP: Validate params
    FastMCP->>Lambda: Execute tool
    Lambda->>Bedrock: Generate response<br/>(message + tool results)
    Bedrock-->>Lambda: Conversational answer
    Lambda-->>APIGW: Response JSON
    APIGW-->>User: Display results
```

## Data Flow

```mermaid
graph LR
    Discogs[Discogs Export] -->|Upload| S3Data[S3 Data Bucket]
    S3Data -->|Read| Lambda[Lambda Function]
    Lambda -->|Parse| CSV[CSV Parser]
    CSV -->|Query| Tools[FastMCP Tools]
    Tools -->|Results| Response[API Response]
    Response -->|Display| UI[Chatbot UI]
```

## Security Architecture

```mermaid
graph TB
    subgraph "Public Internet"
        User[User]
    end
    
    subgraph "AWS Account"
        subgraph "Edge"
            CF[CloudFront<br/>HTTPS Only]
        end
        
        subgraph "Private Resources"
            S3Web[S3 Website<br/>Private + OAC]
            S3Data[S3 Data<br/>Private]
        end
        
        subgraph "Compute"
            APIGW[API Gateway<br/>CORS Enabled]
            Lambda[Lambda<br/>Least Privilege IAM]
        end
        
        subgraph "Logging"
            CW[CloudWatch Logs]
        end
    end
    
    User -->|HTTPS| CF
    CF -->|OAC| S3Web
    User -->|HTTPS| APIGW
    APIGW -->|Invoke| Lambda
    Lambda -->|Read| S3Data
    Lambda -->|Write| CW
    APIGW -->|Write| CW
    
    style S3Web fill:#f99,stroke:#333
    style S3Data fill:#f99,stroke:#333
    style Lambda fill:#9f9,stroke:#333
```

## Infrastructure Components

### Frontend Layer
- **CloudFront Distribution**: CDN for global low-latency access
- **S3 Website Bucket**: Private bucket with static assets (HTML, CSS, JS)
- **Origin Access Control (OAC)**: Secure access from CloudFront to S3

### API Layer
- **API Gateway (HTTP API)**: RESTful API with CORS support
  - POST /chat: Process chat messages
  - GET /tools: List available tools
  - GET /health: Health check
- **CloudWatch Logs**: Structured JSON access logs

### Compute Layer
- **Lambda Function**: Python 3.11 runtime
  - FastMCP tool registry
  - Deterministic router
  - Optional Bedrock integration
  - CSV processing
- **CloudWatch Logs**: Function execution logs

### Data Layer
- **S3 Data Bucket**: Stores discogs.csv
  - Private access
  - Versioning enabled
  - Lambda read permissions

### Security Layer
- **IAM Roles**: Least-privilege permissions
  - Lambda execution role
  - S3 read access (data bucket)
  - CloudWatch write access
  - Optional Bedrock invoke access
- **S3 Bucket Policies**: CloudFront OAC access
- **Public Access Block**: All S3 buckets private

## Deployment Flow

```mermaid
graph LR
    Dev[Developer] -->|terraform apply| TF[Terraform]
    TF -->|Create| S3[S3 Buckets]
    TF -->|Build & Deploy| Lambda[Lambda Function]
    TF -->|Configure| APIGW[API Gateway]
    TF -->|Create| CF[CloudFront]
    TF -->|Upload| Web[Website Assets]
    TF -->|Output| URLs[URLs & Instructions]
    Dev -->|Upload| CSV[discogs.csv]
    CSV -->|To| S3Data[S3 Data Bucket]
```

## Cost Optimization

- **CloudFront**: Caching reduces origin requests
- **Lambda**: Pay per invocation, 512MB memory
- **S3**: Minimal storage costs for static assets and CSV
- **API Gateway**: HTTP API (cheaper than REST API)
- **Bedrock**: Optional, pay per token when enabled

## Scalability

- **CloudFront**: Global edge locations, automatic scaling
- **API Gateway**: Handles 10,000 requests/second by default
- **Lambda**: Automatic scaling, 1000 concurrent executions default
- **S3**: Unlimited storage and requests

## Monitoring

- **CloudWatch Logs**: Lambda execution logs, API Gateway access logs
- **CloudWatch Metrics**: Lambda invocations, errors, duration
- **API Gateway Metrics**: Request count, latency, errors
- **CloudFront Metrics**: Cache hit ratio, requests

## Demo Features

1. **FastMCP Integration**: Tool definitions with automatic schema generation
2. **Deterministic Routing**: Works without LLM, cost-effective
3. **Optional Bedrock**: Enhanced conversational responses
4. **Production-Ready**: Proper IAM, logging, error handling
5. **Infrastructure-as-Code**: Complete Terraform deployment
6. **Serverless**: No servers to manage, automatic scaling
