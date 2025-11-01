"""
Lambda Handler for CO2 Anomaly Reasoning API

This Lambda function handles API requests to generate AI reasoning for CO2 anomalies
using Google Gemini API with DynamoDB caching.

Environment Variables:
    DYNAMODB_TABLE_NAME: Name of DynamoDB cache table
    GEMINI_API_KEY_SECRET_NAME: Name of Secrets Manager secret for Gemini API key
    CACHE_TTL_DAYS: Cache TTL in days (default: 90)
    GEMINI_MODEL: Gemini model version (default: gemini-2.0-flash-exp)
    ENVIRONMENT: Deployment environment (dev, staging, prod)
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""

import json
import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import boto3
import google.generativeai as genai

# Configure logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL))

# AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
SECRET_NAME = os.environ['GEMINI_API_KEY_SECRET_NAME']
CACHE_TTL_DAYS = int(os.environ.get('CACHE_TTL_DAYS', '90'))
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Global cache for API key and table reference
_api_key_cache: Optional[str] = None
_table = None


def get_dynamodb_table():
    """Get DynamoDB table reference (cached)"""
    global _table
    if _table is None:
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def get_gemini_api_key() -> str:
    """
    Retrieve Gemini API key from AWS Secrets Manager (cached)

    Returns:
        str: Gemini API key
    """
    global _api_key_cache

    if _api_key_cache is not None:
        return _api_key_cache

    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret_string = response['SecretString']

        # Secret can be plain string or JSON
        try:
            secret_dict = json.loads(secret_string)
            _api_key_cache = secret_dict.get('apiKey') or secret_dict.get('GEMINI_API_KEY')
        except json.JSONDecodeError:
            _api_key_cache = secret_string

        return _api_key_cache
    except Exception as e:
        logger.error(f"Failed to retrieve API key from Secrets Manager: {e}")
        raise


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

    item = {
        'cache_key': cache_key,
        'reasoning': reasoning,
        'cached_at': datetime.now().isoformat(),
        'metadata': metadata,
        'ttl': ttl_timestamp
    }

    try:
        table.put_item(Item=item)
        logger.info(f"Saved to cache: {cache_key} (TTL: {CACHE_TTL_DAYS} days)")
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        # Don't raise - caching failure shouldn't break the request


def generate_reasoning_with_gemini(
    lat: float,
    lon: float,
    co2: float,
    deviation: float,
    date: str,
    severity: str,
    zscore: float
) -> str:
    """
    Generate reasoning using Google Gemini API
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
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    # Map severity to Japanese (matching gemini_client.py logic)
    severity_ja = {
        "high": "高",
        "medium": "中",
        "low": "低"
    }.get(severity, severity)

    # Create prompt (matching gemini_client.py generate_prompt function)
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
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        # Check for empty response (matching gemini_client.py validation)
        if not response or not response.text:
            raise Exception("Empty response received from Gemini API")

        reasoning = response.text.strip()

        logger.info(f"Generated reasoning for ({lat}, {lon}): {len(reasoning)} chars")
        return reasoning
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
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

        # Validate severity value (matching Flask implementation)
        if severity not in ['high', 'medium', 'low']:
            logger.warning(f"Invalid severity value: {severity}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'error': 'Invalid severity value',
                    'message': 'severity must be one of: high, medium, low'
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
        reasoning = generate_reasoning_with_gemini(
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
