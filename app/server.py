"""Lambda handler for vinyl collection chatbot."""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import boto3

from vinyl.router import DeterministicRouter
from vinyl.tools import mcp

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@dataclass
class LambdaConfig:
    """Lambda environment configuration."""
    discogs_bucket: str
    discogs_key: str = "discogs.csv"
    use_bedrock: bool = False
    bedrock_model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0"
    bedrock_region: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LambdaConfig":
        """
        Load configuration from environment variables.

        Returns:
            LambdaConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        bucket = os.environ.get("DISCOGS_BUCKET")
        if not bucket:
            raise ValueError("DISCOGS_BUCKET environment variable is required")

        return cls(
            discogs_bucket=bucket,
            discogs_key=os.environ.get("DISCOGS_KEY", "discogs.csv"),
            use_bedrock=os.environ.get("USE_BEDROCK", "false").lower() == "true",
            bedrock_model_id=os.environ.get(
                "BEDROCK_MODEL_ID",
                "anthropic.claude-3-5-haiku-20241022-v1:0"
            ),
            bedrock_region=os.environ.get("BEDROCK_REGION")
        )


# Global instances (cached across Lambda invocations)
_config: Optional[LambdaConfig] = None
_router: Optional[DeterministicRouter] = None
_bedrock_client: Optional[Any] = None


def get_config() -> LambdaConfig:
    """Get or initialize configuration."""
    global _config
    if _config is None:
        _config = LambdaConfig.from_env()
    return _config


def get_router() -> DeterministicRouter:
    """Get or initialize router."""
    global _router
    if _router is None:
        _router = DeterministicRouter()
    return _router


def get_bedrock_client():
    """Get or initialize Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        config = get_config()
        region = config.bedrock_region if config.bedrock_region else os.environ.get('AWS_REGION', 'us-east-1')
        logger.info(f"Initializing Bedrock client in region: {region}")
        _bedrock_client = boto3.client('bedrock-runtime', region_name=region)
    return _bedrock_client


def call_bedrock_with_tools(message: str, tools: list[dict]) -> dict:
    """
    Call Bedrock with tool definitions to handle the user query.
    
    Args:
        message: User's message
        tools: List of tool definitions
        
    Returns:
        dict with answer, toolUsed, toolName, toolArgs, etc.
    """
    config = get_config()
    client = get_bedrock_client()
    
    try:
        # Build the request for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "tools": tools,
            "system": (
                "You are a helpful assistant for querying a vinyl record collection. "
                "You have access to tools to search the collection. "
                "Use the tools when the user asks about their vinyl records. "
                "If the user asks about something unrelated to vinyl records, "
                "politely explain that you can only help with vinyl collection queries."
            )
        }
        
        logger.info(f"Calling Bedrock with model: {config.bedrock_model_id}")
        
        response = client.invoke_model(
            modelId=config.bedrock_model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        logger.info(f"Bedrock response: {response_body}")
        
        # Parse response
        stop_reason = response_body.get('stop_reason')
        content = response_body.get('content', [])
        
        if stop_reason == 'tool_use':
            # Claude wants to use a tool
            for block in content:
                if block.get('type') == 'tool_use':
                    tool_name = block.get('name')
                    tool_args = block.get('input', {})
                    
                    logger.info(f"Bedrock selected tool: {tool_name} with args: {tool_args}")
                    
                    # Execute the tool
                    import asyncio
                    tool = asyncio.run(mcp.get_tool(tool_name))
                    tool_results = tool.fn(**tool_args)
                    
                    # Format response
                    if isinstance(tool_results, list):
                        if len(tool_results) == 0:
                            answer = "No results found."
                        else:
                            answer = f"Found {len(tool_results)} result(s):\n\n" + "\n".join(tool_results)
                    elif isinstance(tool_results, dict):
                        answer = format_stats(tool_results)
                    else:
                        answer = str(tool_results)
                    
                    return {
                        "answer": answer,
                        "toolUsed": True,
                        "toolName": tool_name,
                        "toolArgs": tool_args,
                        "toolResults": tool_results if isinstance(tool_results, list) else [str(tool_results)],
                        "model": config.bedrock_model_id
                    }
        
        # No tool use - just return Claude's text response
        text_response = ""
        for block in content:
            if block.get('type') == 'text':
                text_response += block.get('text', '')
        
        return {
            "answer": text_response or "I'm not sure how to help with that.",
            "toolUsed": False,
            "toolName": None,
            "toolArgs": None,
            "toolResults": None,
            "model": config.bedrock_model_id
        }
        
    except Exception as e:
        logger.error(f"Bedrock invocation failed: {e}", exc_info=True)
        raise


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Main Lambda entry point.

    Routes:
    - POST /chat: Process chat message
    - GET /tools: Return tool definitions
    - GET /health: Health check

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response format
    """
    try:
        # Parse request
        http_method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path", "")

        logger.info(f"Request: {http_method} {path}")

        # Route request
        if http_method == "POST" and path == "/chat":
            body = json.loads(event.get("body", "{}"))
            response_body = handle_chat(body)
            status_code = 200

        elif http_method == "GET" and path == "/tools":
            response_body = handle_tools()
            status_code = 200

        elif http_method == "GET" and path == "/health":
            response_body = handle_health()
            status_code = 200

        else:
            response_body = {"error": "Not found"}
            status_code = 404

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(response_body)
        }

    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "requestId": str(uuid.uuid4())
            })
        }


def handle_chat(body: dict) -> dict:
    """
    Process chat request.

    Args:
        body: { message: str, sessionId?: str, mode?: str }

    Returns:
        {
            answer: str,
            toolUsed: bool,
            toolName: str | None,
            toolArgs: dict | None,
            toolResults: list[str] | None,
            requestId: str,
            model: str | None
        }
    """
    request_id = str(uuid.uuid4())

    try:
        # Validate request
        message = body.get("message")
        if not message:
            return {
                "answer": "Error: Message is required",
                "toolUsed": False,
                "toolName": None,
                "toolArgs": None,
                "toolResults": None,
                "requestId": request_id,
                "model": None
            }

        mode = body.get("mode", "auto")
        config = get_config()

        # Determine routing mode
        if mode == "auto":
            use_bedrock = config.use_bedrock
        elif mode == "bedrock":
            use_bedrock = config.use_bedrock
        else:
            use_bedrock = False

        # For now, always use deterministic routing
        # Bedrock integration can be added later
        router = get_router()
        result = router.route(message)

        # If no tool selected, check if we should use Bedrock
        if result.tool_name is None:
            if use_bedrock:
                # Use Bedrock to handle the query
                try:
                    import asyncio
                    tools_dict = asyncio.run(mcp.get_tools())
                    tools = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.parameters
                        }
                        for tool in tools_dict.values()
                    ]
                    
                    bedrock_result = call_bedrock_with_tools(message, tools)
                    bedrock_result["requestId"] = request_id
                    return bedrock_result
                    
                except Exception as e:
                    logger.error(f"Bedrock fallback failed: {e}", exc_info=True)
                    # Fall through to deterministic fallback
            
            # Return deterministic fallback
            return {
                "answer": result.fallback_response,
                "toolUsed": False,
                "toolName": None,
                "toolArgs": None,
                "toolResults": None,
                "requestId": request_id,
                "model": None
            }

        # Execute tool through FastMCP
        logger.info(f"Executing tool: {result.tool_name} with args: {result.tool_args}")

        try:
            # Call tool through FastMCP - get_tool is async
            import asyncio
            tool = asyncio.run(mcp.get_tool(result.tool_name))
            
            # Call the tool function directly
            tool_results = tool.fn(**result.tool_args)

            # Format response
            if isinstance(tool_results, list):
                if len(tool_results) == 0:
                    answer = "No results found."
                else:
                    answer = f"Found {len(tool_results)} result(s):\n\n" + "\n".join(tool_results)
            elif isinstance(tool_results, dict):
                # Stats summary
                answer = format_stats(tool_results)
            else:
                answer = str(tool_results)

            return {
                "answer": answer,
                "toolUsed": True,
                "toolName": result.tool_name,
                "toolArgs": result.tool_args,
                "toolResults": tool_results if isinstance(tool_results, list) else [str(tool_results)],
                "requestId": request_id,
                "model": "deterministic-router"
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "answer": "I encountered an error while searching your collection. Please try rephrasing your query.",
                "toolUsed": False,
                "toolName": result.tool_name,
                "toolArgs": result.tool_args,
                "toolResults": None,
                "requestId": request_id,
                "model": None
            }

    except Exception as e:
        logger.error(f"Error handling chat: {e}", exc_info=True)
        return {
            "answer": "An unexpected error occurred. Please try again.",
            "toolUsed": False,
            "toolName": None,
            "toolArgs": None,
            "toolResults": None,
            "requestId": request_id,
            "model": None
        }


def handle_tools() -> list[dict]:
    """
    Return FastMCP tool definitions.

    Returns:
        [{ name: str, description: str, inputSchema: dict }]
    """
    try:
        # FastMCP get_tools() is async, but we need sync for Lambda
        # Use asyncio.run to call it
        import asyncio
        tools_dict = asyncio.run(mcp.get_tools())
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            for tool in tools_dict.values()
        ]
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        return []


def handle_health() -> dict:
    """
    Health check endpoint.

    Returns:
        { status: str, timestamp: str }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


def format_stats(stats: dict) -> str:
    """
    Format stats summary as readable text.

    Args:
        stats: Stats dictionary from stats_summary tool

    Returns:
        Formatted string
    """
    lines = [
        "📊 Collection Statistics:",
        "",
        f"Total Records: {stats.get('total_records', 0)}",
        f"Unique Artists: {stats.get('unique_artists', 0)}",
        f"Unique Labels: {stats.get('unique_labels', 0)}",
    ]

    year_min = stats.get('year_min')
    year_max = stats.get('year_max')
    if year_min and year_max:
        lines.append(f"Year Range: {year_min} - {year_max}")

    top_artists = stats.get('top_artists', [])
    if top_artists:
        lines.append("")
        lines.append("Top Artists:")
        for item in top_artists[:5]:
            lines.append(f"  • {item['artist']}: {item['count']} records")

    top_labels = stats.get('top_labels', [])
    if top_labels:
        lines.append("")
        lines.append("Top Labels:")
        for item in top_labels[:5]:
            lines.append(f"  • {item['label']}: {item['count']} records")

    return "\n".join(lines)
