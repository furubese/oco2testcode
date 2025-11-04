"""
Lambda Handler for CO2 Anomaly Reasoning API

This Lambda function handles API requests to generate AI reasoning for CO2 anomalies
using AWS Bedrock Nova Pro with DynamoDB caching.

Environment Variables:
    DYNAMODB_TABLE_NAME: Name of DynamoDB cache table
    BEDROCK_MODEL_ID: Bedrock model ID (default: us.amazon.nova-pro-v1:0)
    AWS_REGION: AWS region for Bedrock (default: us-east-1)
    CACHE_TTL_DAYS: Cache TTL in days (default: 90)
    ENVIRONMENT: Deployment environment (dev, staging, prod)
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""

import json
import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

import boto3

# Configure logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL))

# AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_region = os.environ.get('AWS_REGION', 'us-east-1')
bedrock_client = boto3.client('bedrock-runtime', region_name=bedrock_region)

# Environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.amazon.nova-pro-v1:0')
CACHE_TTL_DAYS = int(os.environ.get('CACHE_TTL_DAYS', '90'))
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Global cache for table reference
_table = None


def get_dynamodb_table():
    """Get DynamoDB table reference (cached)"""
    global _table
    if _table is None:
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def convert_float_to_decimal(obj: Any) -> Any:
    """
    Convert float values to Decimal for DynamoDB compatibility

    DynamoDB does not support Python float type. This function recursively
    converts float values to Decimal type.

    Args:
        obj: Object to convert (can be dict, list, float, or any other type)

    Returns:
        Object with float values converted to Decimal
    """
    if isinstance(obj, float):
        # Convert float to string first to avoid precision issues
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_float_to_decimal(i) for i in obj]
    return obj


def generate_cache_key(lat: float, lon: float, date: str) -> str:
    """
    Generate SHA256 hash for cache key
    Matches the cache_manager.py implementation from Flask app

    Args:
        lat: Latitude
        lon: Longitude
        date: Observation date

    Returns:
        str: SHA256 hash as cache key
    """
    # Create hash input (matching cache_manager.py format)
    # Note: Flask version doesn't round coordinates, so we match that behavior
    key_string = f"{lat}_{lon}_{date}"

    # Generate SHA256 hash (matching cache_manager.py)
    hash_object = hashlib.sha256(key_string.encode('utf-8'))
    cache_key = hash_object.hexdigest()

    logger.debug(f"Generated cache key: {cache_key} for {key_string}")
    return cache_key


def get_cached_reasoning(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached reasoning from DynamoDB

    Args:
        cache_key: Cache key (SHA256 hash)

    Returns:
        dict: Cached item if found, None otherwise
    """
    table = get_dynamodb_table()

    try:
        response = table.get_item(Key={'cache_key': cache_key})

        if 'Item' in response:
            logger.info(f"Cache HIT for key: {cache_key}")
            return response['Item']
        else:
            logger.info(f"Cache MISS for key: {cache_key}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving from cache: {e}")
        return None


def save_to_cache(cache_key: str, reasoning: str, metadata: Dict[str, Any]) -> None:
    """
    Save reasoning to DynamoDB cache with TTL

    Args:
        cache_key: Cache key (SHA256 hash)
        reasoning: AI-generated reasoning text
        metadata: Request metadata
    """
    table = get_dynamodb_table()

    # Calculate TTL timestamp
    ttl_timestamp = int((datetime.now() + timedelta(days=CACHE_TTL_DAYS)).timestamp())

    # Convert float values to Decimal for DynamoDB compatibility
    metadata_converted = convert_float_to_decimal(metadata)

    item = {
        'cache_key': cache_key,
        'reasoning': reasoning,
        'cached_at': datetime.now().isoformat(),
        'metadata': metadata_converted,
        'ttl': ttl_timestamp
    }

    try:
        table.put_item(Item=item)
        logger.info(f"Saved to cache: {cache_key} (TTL: {CACHE_TTL_DAYS} days)")
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        # Don't raise - caching failure shouldn't break the request


def generate_reasoning_with_bedrock(
    lat: float,
    lon: float,
    co2: float,
    deviation: float,
    date: str,
    severity: str,
    zscore: float
) -> str:
    """
    Generate reasoning using AWS Bedrock Nova Pro
    Uses Japanese prompt matching the Flask implementation

    Args:
        lat: Latitude
        lon: Longitude
        co2: CO2 concentration (ppm)
        deviation: Deviation from baseline
        date: Observation date
        severity: Severity level (low, medium, high)
        zscore: Statistical Z-score

    Returns:
        str: AI-generated reasoning
    """
    # Map severity to Japanese
    severity_ja = {
        "high": "高",
        "medium": "中",
        "low": "低",
        "unknown": "不明"
    }.get(severity, severity)

    # Create prompt (matching previous implementation)
    prompt = f"""以下のCO2濃度異常データについて、専門家の視点から分析し、日本語で200-300文字程度で推論してください。

【観測データ】
- 日付: {date}
- 位置: 緯度 {lat:.2f}°, 経度 {lon:.2f}°
- CO2濃度: {co2:.2f} ppm
- 偏差: {deviation:.2f} ppm
- 異常度: {severity_ja}
- Zスコア: {zscore:.2f}

【推論内容】
この地点でのCO2濃度異常の考えられる原因、その地域の特徴、および環境への影響について、科学的根拠に基づいて分析してください。
地理的な特性や、その時期の気候的要因も考慮してください。
"""

    try:
        # Bedrock Converse API request
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 512,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        logger.debug(f"Calling Bedrock with model: {BEDROCK_MODEL_ID}")

        # Call Bedrock Converse API
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )

        # Extract response text
        if not response or 'output' not in response:
            raise Exception("Empty response received from Bedrock API")

        output = response['output']
        if 'message' not in output or 'content' not in output['message']:
            raise Exception("Invalid response structure from Bedrock API")

        content = output['message']['content']
        if not content or len(content) == 0:
            raise Exception("Empty content in Bedrock response")

        reasoning = content[0]['text'].strip()

        logger.info(f"Generated reasoning for ({lat}, {lon}): {len(reasoning)} chars")
        return reasoning
    except Exception as e:
        logger.error(f"Bedrock API error: {e}")
        raise Exception(f"Failed to generate reasoning: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for reasoning API

    Expected event structure (API Gateway):
    {
        "body": "{\"lat\": 35.6762, \"lon\": 139.6503, \"co2\": 420.5, ...}",
        "headers": {...},
        "httpMethod": "POST",
        ...
    }

    Returns:
        dict: API Gateway response format
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)

        # Validate required fields (matching Flask implementation)
        required_fields = ['lat', 'lon', 'co2', 'deviation', 'date', 'severity', 'zscore']
        missing_fields = [field for field in required_fields if field not in body]

        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                })
            }

        # Extract and validate parameters
        try:
            lat = float(body['lat'])
            lon = float(body['lon'])
            co2 = float(body['co2'])
            deviation = float(body['deviation'])
            date = str(body['date'])
            severity = str(body['severity'])
            zscore = float(body['zscore'])
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter type: {e}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'error': 'Invalid parameter type',
                    'message': str(e)
                })
            }

        # Validate severity value (accepting 'unknown' from frontend)
        # Frontend may send 'unknown' when severity is not available (sample_calendar.html:567)
        if severity not in ['high', 'medium', 'low', 'unknown']:
            logger.warning(f"Invalid severity value: {severity}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'error': 'Invalid severity value',
                    'message': 'severity must be one of: high, medium, low, unknown'
                })
            }

        logger.info(f"Processing request for location: ({lat}, {lon}), severity: {severity}")

        # Generate cache key
        cache_key = generate_cache_key(lat, lon, date)

        # Check cache
        cached_item = get_cached_reasoning(cache_key)

        if cached_item:
            # Return cached result
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
                },
                'body': json.dumps({
                    'reasoning': cached_item['reasoning'],
                    'cached': True,
                    'cache_key': cache_key,
                    'cached_at': cached_item.get('cached_at')
                })
            }

        # Cache miss - generate new reasoning
        reasoning = generate_reasoning_with_bedrock(
            lat, lon, co2, deviation, date, severity, zscore
        )

        # Save to cache
        metadata = {
            'lat': lat,
            'lon': lon,
            'co2': co2,
            'deviation': deviation,
            'date': date,
            'severity': severity,
            'zscore': zscore
        }
        save_to_cache(cache_key, reasoning, metadata)

        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            },
            'body': json.dumps({
                'reasoning': reasoning,
                'cached': False,
                'cache_key': cache_key
            })
        }

    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': f'Missing required parameter: {str(e)}'
            })
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e) if ENVIRONMENT == 'dev' else 'An error occurred'
            })
        }
