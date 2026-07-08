import json
import boto3
import logging
import re
import os
import smtplib
import ssl
from datetime import datetime
import uuid
from decimal import Decimal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CafeOrders')

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Smart Café')


def lambda_handler(event, context):
    logger.info("Lambda started!")

    try:
        body = json.loads(event.get('body', '{}'))
        logger.info(f"Order data: {json.dumps(body)}")

        order_id = generate_order_id()
        logger.info(f"Order ID: {order_id}")

        total = calculate_total(body.get('items', []))
        logger.info(f"Total: ${total}")

        customer_email = (body.get('customerEmail') or '').lower().strip()
        customer_name = (body.get('customerName') or '').strip()
        table_reservation = body.get('tableReservation')
        if table_reservation:
            table_reservation = str(table_reservation).strip()
        special_instructions = (body.get('specialInstructions') or '').strip()

        items = []
        for item in body.get('items', []):
            items.append({
                'name': item.get('name', ''),
                'quantity': int(item.get('quantity', 1)),
                'price': Decimal(str(item.get('price', 0)))
            })

        order = {
            'orderId': order_id,
            'customerEmail': customer_email,
            'customerName': customer_name,
            'items': items,
            'totalAmount': Decimal(str(total)),
            'orderStatus': 'pending',
            'tableReservation': table_reservation or None,
            'specialInstructions': special_instructions or '',
            'createdAt': datetime.utcnow().isoformat() + 'Z'
        }

        table.put_item(Item=order)
        logger.info(f"Order saved: {order_id}")

        try:
            send_customer_confirmation(order)
            logger.info(f"Customer email sent to {order['customerEmail']}")
        except Exception as e:
            logger.error(f"Customer email failed: {str(e)}")

        try:
            send_admin_notification(order)
            logger.info(f"Admin email sent to {ADMIN_EMAIL}")
        except Exception as e:
            logger.error(f"Admin email failed: {str(e)}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Order placed successfully! A confirmation email has been sent.',
                'orderId': order_id,
                'totalAmount': float(total)
            })
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.exception("Full traceback:")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Failed to place order',
                'details': str(e)
            })
        }


def send_customer_confirmation(order):
    try:
        subject = f'Order Confirmation - {order["orderId"]}'

        items_html = ''.join([
            f'<tr><td>{item["name"]}</td><td>{item["quantity"]}</td><td>${float(item["price"]):.2f}</td><td>${float(item["price"]) * item["quantity"]:.2f}</td></tr>'
            for item in order.get('items', [])
        ])

        table_reservation = order.get('tableReservation')
        reservation_text = table_reservation if table_reservation else 'Not requested'

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c1810; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f7f4; padding: 20px; }}
                .order-details {{ background: white; padding: 15px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #2c1810; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .total {{ font-size: 1.2em; font-weight: bold; text-align: right; padding: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Thank You for Your Order!</h1>
                </div>
                <div class="content">
                    <h2>Hello {order['customerName']},</h2>
                    <p>Your order has been received and is being prepared. Here's what you ordered:</p>

                    <div class="order-details">
                        <p><strong>Order ID:</strong> {order['orderId']}</p>
                        <p><strong>Order Date:</strong> {format_date(order['createdAt'])}</p>

                        <table>
                            <thead>
                                <tr>
                                    <th>Item</th>
                                    <th>Qty</th>
                                    <th>Price</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>

                        <div class="total">
                            Total: <span style="color: #2c1810;">${float(order['totalAmount']):.2f}</span>
                        </div>
                    </div>

                    <div>
                        <p><strong>Table Reservation:</strong> {reservation_text}</p>
                        <p><strong>Special Instructions:</strong> {order.get('specialInstructions', 'None')}</p>
                    </div>

                    <p>We'll notify you when your order is ready for pickup!</p>
                    <p>Best regards,<br><strong>{COMPANY_NAME} Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} {COMPANY_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email_via_gmail(
            to_email=order['customerEmail'],
            subject=subject,
            html_body=html_body,
            text_body=create_text_version(order)
        )
    except Exception as e:
        logger.error(f"Error in customer email: {str(e)}")
        raise


def send_admin_notification(order):
    try:
        subject = f'New Order Alert - {order["orderId"]}'

        items_list = ', '.join([f"{item['name']} x{item['quantity']}" for item in order.get('items', [])])
        table_reservation = order.get('tableReservation')
        reservation_text = table_reservation if table_reservation else 'Not requested'

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; }}
                .order-details {{ background: white; padding: 15px; }}
                .badge {{ background: #dc3545; color: white; padding: 5px 10px; border-radius: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Order Received!</h1>
                </div>
                <div class="content">
                    <h2>New order from {order['customerName']}</h2>

                    <div class="order-details">
                        <p><strong>Order ID:</strong> <span class="badge">{order['orderId']}</span></p>
                        <p><strong>Customer:</strong> {order['customerName']}</p>
                        <p><strong>Email:</strong> {order['customerEmail']}</p>
                        <p><strong>Items:</strong> {items_list}</p>
                        <p><strong>Total:</strong> ${float(order['totalAmount']):.2f}</p>
                        <p><strong>Table Reservation:</strong> {reservation_text}</p>
                        <p><strong>Special Instructions:</strong> {order.get('specialInstructions', 'None')}</p>
                    </div>

                    <p>Order placed at {format_date(order['createdAt'])}</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email_via_gmail(
            to_email=ADMIN_EMAIL,
            subject=subject,
            html_body=html_body,
            text_body=f"New order from {order['customerName']}\nOrder ID: {order['orderId']}\nTotal: ${float(order['totalAmount']):.2f}\nItems: {items_list}\nTable: {reservation_text}"
        )
    except Exception as e:
        logger.error(f"Error in admin email: {str(e)}")
        raise


def send_email_via_gmail(to_email, subject, html_body, text_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((COMPANY_NAME, GMAIL_USER))
        msg['To'] = to_email

        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        context = ssl.create_default_context()
        logger.info("Connecting to Gmail SMTP server...")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            logger.info("Gmail SMTP login successful")
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}")

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise


def create_text_version(order):
    items_text = '\n'.join([
        f"  - {item['name']} x{item['quantity']}: ${float(item['price']) * item['quantity']:.2f}"
        for item in order.get('items', [])
    ])

    table_reservation = order.get('tableReservation')
    reservation_text = table_reservation if table_reservation else 'Not requested'

    return f"""
Thank You for Your Order!

Order ID: {order['orderId']}
Order Date: {format_date(order['createdAt'])}
Customer: {order['customerName']}
Email: {order['customerEmail']}

Items:
{items_text}

Total: ${float(order['totalAmount']):.2f}
Table Reservation: {reservation_text}
Special Instructions: {order.get('specialInstructions', 'None')}

We'll notify you when your order is ready!
Thank you for choosing {COMPANY_NAME}!
    """


def format_date(date_string):
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_string


def parse_request_body(event):
    if 'body' not in event:
        raise ValueError('Missing request body')
    body = event['body']
    if isinstance(body, str):
        body = json.loads(body)
    return body


def validate_order(body):
    required_fields = ['customerName', 'customerEmail', 'items']
    for field in required_fields:
        if field not in body:
            return f"Missing required field: {field}"
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, body['customerEmail']):
        return "Invalid email format"
    if not isinstance(body['items'], list) or len(body['items']) == 0:
        return "Items must be a non-empty array"
    return None


def calculate_total(items):
    total = 0.0
    for item in items:
        total += int(item['quantity']) * float(item['price'])
    return total


def generate_order_id():
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"ORD-{timestamp}-{short_uuid}"


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
