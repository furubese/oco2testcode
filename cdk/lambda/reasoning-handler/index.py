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

    Args:
        lat: Latitude
        lon: Longitude
        date: Observation date

    Returns:
        str: SHA256 hash as cache key
    """
    # Round coordinates to 4 decimal places for cache consistency
    lat_rounded = round(lat, 4)
    lon_rounded = round(lon, 4)

    # Create hash input
    hash_input = f"{lat_rounded}_{lon_rounded}_{date}"

    # Generate SHA256 hash
    hash_object = hashlib.sha256(hash_input.encode())
    cache_key = hash_object.hexdigest()

    logger.debug(f"Generated cache key: {cache_key} for {hash_input}")
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

    # Create prompt
    prompt = f"""You are an environmental data analyst. Analyze this CO₂ concentration anomaly:

Location: {lat}°N, {lon}°E
CO₂ Concentration: {co2} ppm
Deviation from baseline: {deviation} ppm
Severity: {severity}
Z-Score: {zscore}
Observation Date: {date}

Provide a concise analysis (2-3 sentences) explaining possible causes of this CO₂ anomaly. Consider:
- Nearby industrial activities
- Urban density and traffic patterns
- Seasonal factors
- Geographic features
- Weather patterns

Focus on the most likely causes based on the location and severity."""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
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

        # Extract parameters
        lat = float(body['lat'])
        lon = float(body['lon'])
        co2 = float(body['co2'])
        deviation = float(body.get('deviation', 0))
        date = body.get('date', '')
        severity = body.get('severity', 'unknown')
        zscore = float(body.get('zscore', 0))

        logger.info(f"Processing request for location: ({lat}, {lon})")

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
