import json
import boto3
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CafeOrders')


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        query_params = event.get('queryStringParameters', {}) or {}
        order_id = query_params.get('orderId')
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', 100))

        logger.info(f"orderId={order_id}, status={status_filter}, limit={limit}")

        # Single order lookup by orderId (partition key)
        if order_id:
            response = table.query(
                KeyConditionExpression='orderId = :orderId',
                ExpressionAttributeValues={':orderId': order_id}
            )
            items = response.get('Items', [])

            if not items:
                return create_response(404, {'error': 'Order not found'})

            return create_response(200, convert_decimal_to_float(items[0]))

        # List all orders (existing behavior)
        scan_params = {'Limit': limit}

        if status_filter:
            scan_params['FilterExpression'] = 'orderStatus = :status'
            scan_params['ExpressionAttributeValues'] = {
                ':status': status_filter
            }

        response = table.scan(**scan_params)
        orders = response.get('Items', [])

        last_evaluated_key = response.get('LastEvaluatedKey')

        orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        orders_serializable = convert_decimal_to_float(orders)

        total_orders = len(orders_serializable)
        status_counts = {}
        for order in orders_serializable:
            status = order.get('orderStatus', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        logger.info(f"Retrieved {total_orders} orders")
        logger.info(f"Status counts: {status_counts}")

        return create_response(200, {
            'success': True,
            'count': total_orders,
            'orders': orders_serializable,
            'stats': status_counts,
            'hasMore': last_evaluated_key is not None
        })

    except Exception as e:
        logger.error(f"Error retrieving orders: {str(e)}")
        logger.exception("Full traceback:")

        return create_response(500, {
            'error': 'Failed to retrieve orders',
            'details': str(e)
        })


def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
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
