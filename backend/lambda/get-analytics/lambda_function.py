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
    logger.info(f"Event: {json.dumps(event)}")

    try:
        response = table.scan()
        orders = response.get('Items', [])

        total_orders = len(orders)
        total_revenue = sum(float(o.get('totalAmount', 0)) for o in orders)

        today = datetime.utcnow().date().isoformat()
        today_orders = [o for o in orders if o.get('createdAt', '').startswith(today)]
        today_revenue = sum(float(o.get('totalAmount', 0)) for o in today_orders)

        item_counts = {}
        for order in orders:
            for item in order.get('items', []):
                name = item.get('name', 'Unknown')
                qty = int(item.get('quantity', 1))
                item_counts[name] = item_counts.get(name, 0) + qty

        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        popular_items = [{'name': name, 'count': count} for name, count in top_items]

        status_counts = {}
        for order in orders:
            status = order.get('orderStatus', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        return create_response(200, {
            'success': True,
            'totalOrders': total_orders,
            'totalRevenue': round(total_revenue, 2),
            'todayOrders': len(today_orders),
            'todayRevenue': round(today_revenue, 2),
            'popularItems': popular_items,
            'statusBreakdown': status_counts
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return create_response(500, {'error': 'Failed to get analytics', 'details': str(e)})


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
