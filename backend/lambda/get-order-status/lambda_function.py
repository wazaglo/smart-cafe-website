import json
import boto3
import logging
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CafeOrders')


def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")

    try:
        params = event.get('queryStringParameters', {}) or {}
        order_id = params.get('orderId')

        if not order_id:
            return create_response(400, {'error': 'Missing orderId parameter'})

        response = table.query(
            KeyConditionExpression='orderId = :orderId',
            ExpressionAttributeValues={':orderId': order_id}
        )

        items = response.get('Items', [])

        if not items:
            return create_response(404, {'error': 'Order not found'})

        order = items[0]
        serialized = convert_decimal_to_float(order)

        return create_response(200, {
            'success': True,
            'orderId': serialized['orderId'],
            'customerName': serialized['customerName'],
            'orderStatus': serialized['orderStatus'],
            'items': serialized['items'],
            'totalAmount': serialized['totalAmount'],
            'tableReservation': serialized.get('tableReservation'),
            'specialInstructions': serialized.get('specialInstructions', ''),
            'createdAt': serialized['createdAt'],
            'updatedAt': serialized.get('updatedAt')
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve order', 'details': str(e)})


def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj


def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, default=str)
    }
