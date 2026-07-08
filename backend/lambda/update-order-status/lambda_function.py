import json
import boto3
import logging
import os
import smtplib
import ssl
from decimal import Decimal
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CafeOrders')

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Smart Café')


def lambda_handler(event, context):
    logger.info(f"FULL EVENT: {json.dumps(event)}")

    try:
        body = parse_request_body(event)
        logger.info(f"Parsed body: {json.dumps(body)}")

        if 'orderId' not in body:
            logger.error("Missing orderId in request")
            return create_response(400, {'error': 'Missing orderId'})

        if 'orderStatus' not in body:
            logger.error("Missing orderStatus in request")
            return create_response(400, {'error': 'Missing orderStatus'})

        order_id = body['orderId']
        new_status = body['orderStatus']

        logger.info(f"Updating order {order_id} to status: {new_status}")

        valid_statuses = ['pending', 'preparing', 'ready', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            logger.error(f"Invalid status: {new_status}")
            return create_response(400, {
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            })

        query_response = table.query(
            KeyConditionExpression='orderId = :orderId',
            ExpressionAttributeValues={
                ':orderId': order_id
            }
        )

        items = query_response.get('Items', [])

        if not items:
            logger.error(f"Order not found: {order_id}")
            return create_response(404, {'error': f'Order {order_id} not found'})

        existing_order = items[0]
        customer_email = existing_order.get('customerEmail')

        if not customer_email:
            logger.error(f"Order {order_id} has no customerEmail")
            return create_response(500, {'error': 'Order data is corrupted'})

        logger.info(f"Found customer email: {customer_email}")

        response = table.update_item(
            Key={
                'orderId': order_id,
                'customerEmail': customer_email
            },
            UpdateExpression='SET orderStatus = :status, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':status': new_status,
                ':updatedAt': datetime.utcnow().isoformat() + 'Z'
            },
            ReturnValues='ALL_NEW'
        )

        updated_order = response.get('Attributes', {})
        logger.info(f"Order {order_id} updated successfully")

        if new_status == 'ready':
            try:
                send_ready_notification(existing_order)
                logger.info(f"Ready notification sent to {customer_email}")
            except Exception as e:
                logger.error(f"Ready notification failed: {str(e)}")

        updated_order_serializable = convert_decimal_to_float(updated_order)

        return create_response(200, {
            'success': True,
            'message': f'Order {order_id} updated to {new_status}',
            'order': updated_order_serializable
        })

    except Exception as e:
        logger.error(f"Error updating order: {str(e)}")
        logger.exception("Full traceback:")

        return create_response(500, {
            'error': 'Failed to update order',
            'details': str(e)
        })


def send_ready_notification(order):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set, skipping notification")
        return

    subject = f'{COMPANY_NAME} - Order Ready for Pickup'

    items_text = ', '.join([
        f"{item['name']} x{item['quantity']}"
        for item in order.get('items', [])
    ])

    body = f"""
Order Ready for Pickup

Order ID: {order['orderId']}
Items: {items_text}
Total: ${float(order['totalAmount']):.2f}

Please come to the café to collect your order.

Thank you for choosing {COMPANY_NAME}.
    """

    msg = MIMEText(body.strip())
    msg['Subject'] = subject
    msg['From'] = formataddr((COMPANY_NAME, GMAIL_USER))
    msg['To'] = order['customerEmail']

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, order['customerEmail'], msg.as_string())

    logger.info(f"Ready notification sent to {order['customerEmail']}")


def parse_request_body(event):
    if 'body' not in event:
        raise ValueError('Missing request body')

    body = event['body']

    if isinstance(body, str):
        body = json.loads(body)

    return body


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
