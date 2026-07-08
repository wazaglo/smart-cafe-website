# Smart Cafe - Serverless Cloud Ordering System

A production-ready, serverless cafe ordering system built on AWS. Customers can browse the menu, place orders with optional table reservations, and receive email confirmations. Cafe owners can manage orders through an admin dashboard with real-time status updates.

> **🔒 Security:** All sensitive credentials have been removed from this repo. See [SECURITY.md](SECURITY.md) for what was sanitized and how to configure your own credentials.
>
> **📖 Backend Setup:** See [backend/README.md](backend/README.md) for step-by-step API Gateway and Lambda setup guide.

## Architecture

```
Users ──> AWS Amplify ──> frontend/ ──> API Gateway ──> Lambda ──> DynamoDB
  (HTML/CSS/JS)                                 └──> Gmail SMTP (Email)
```

### AWS Resources

| Service | Name | Purpose |
|---------|------|---------|
| Amplify | `smart-cafe-website` | Frontend hosting with CI/CD |
| API Gateway | `CafeOrderAPI` | REST API (POST, GET, PUT, OPTIONS) |
| Lambda | `cafe-order-processor` | Process orders, send emails |
| Lambda | `get-orders` | Retrieve all orders / single order by ID |
| Lambda | `update-order-status` | Update order status + email when ready |
| Lambda | `get-analytics` | Revenue stats and popular items |
| Lambda | `get-order-status` | Dedicated single-order lookup (optional) |
| DynamoDB | `CafeOrders` | Order storage |
| IAM Role | `cafe-order-processor-role` | Lambda permissions |

### Live URL

**Frontend:** https://dsss7mj4domm4.amplifyapp.com  
**API Endpoint:** https://your-api-id.execute-api.us-east-1.amazonaws.com/prod

## Project Structure

```
smart-cafe-website/
  frontend/                         # Static website files
    index.html                      Home page
    about.html                      About page
    menu.html                       Menu page
    order.html                      Order form page
    status.html                     Order tracking page
    contact.html                    Contact page
    admin.html                      Admin dashboard + analytics
    styles.css                      Global styles
    app.js                          Shared JavaScript
  backend/                          # Serverless backend
    lambda/
      cafe-order-processor/         POST / — place order + email
      get-orders/                   GET / — list/search orders
      update-order-status/          PUT / — update status + ready notification
      get-analytics/                GET /analytics — revenue + popularity
      get-order-status/             GET /order — single order lookup (optional)
    README.md                       API Gateway setup guide
  README.md                         This file
  SECURITY.md                       Sanitization & credentials guide
  troubleshooting.md                Common issues debugged
```

## Features

- **Order Online** — Select items, customize quantities, optional table reservation
- **Order Tracking** — Enter your Order ID to check status in real-time
- **Admin Dashboard** — View all orders, update status, see analytics
- **Email Notifications** — Confirmation to customer + alert to admin on new order
- **Ready Notification** — Customer gets email when order status is set to "ready"
- **Analytics** — Daily revenue, popular items breakdown on admin dashboard

## API Endpoints

### POST / — Place Order
```json
{ "customerName": "John Doe", "customerEmail": "john@example.com",
  "items": [{ "name": "Latte", "quantity": 2, "price": 4.50 }],
  "tableReservation": "Table 3", "specialInstructions": "Extra foam" }
```
**Response:** `{ "orderId": "ORD-...", "totalAmount": 9.00 }`

### GET / — Get Orders
- `GET /` — List all orders (newest first)
- `GET /?orderId=ORD-...` — Look up single order
- `GET /?status=pending` — Filter by status

### PUT / — Update Status
```json
{ "orderId": "ORD-...", "orderStatus": "ready" }
```
Triggers "ready for pickup" email to customer.

### GET /analytics — Stats
Returns total revenue, today's revenue, top 5 popular items, status breakdown.

## DynamoDB Schema

**Table:** `CafeOrders` | **Partition Key:** `orderId` | **Sort Key:** `customerEmail`

```json
{
  "orderId": "ORD-1783514182230-72DE4EE5",
  "customerEmail": "test@example.com",
  "customerName": "Test User",
  "items": [{ "name": "Latte", "quantity": 1, "price": 4.50 }],
  "totalAmount": 4.50, "orderStatus": "pending",
  "tableReservation": "Table 3", "specialInstructions": "",
  "createdAt": "2026-07-08T12:36:22.230111Z",
  "updatedAt": "2026-07-08T12:42:22.230111Z"
}
```

## Getting Started

### Prerequisites
- AWS account (free tier)
- GitHub account
- Gmail account with 2-Step Verification enabled

### 1. Deploy Backend
Follow the step-by-step guide in [backend/README.md](backend/README.md):
1. Create Lambda functions with the code in `backend/lambda/`
2. Set environment variables (see [SECURITY.md](SECURITY.md))
3. Create API Gateway with POST/GET/PUT methods + `/analytics`
4. Enable CORS and deploy to `prod` stage

### 2. Deploy Frontend
```bash
git clone https://github.com/wazaglo/smart-cafe-website.git
```
Push to GitHub → Amplify auto-deploys from `frontend/` directory.

### 3. Configure Credentials
See [SECURITY.md](SECURITY.md) for Gmail App Password setup and Lambda environment variables.

## Local Development

```bash
cd frontend/
open index.html        # No build tools needed
```

## Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Hosting:** AWS Amplify (auto CI/CD from GitHub)
- **Backend:** AWS Lambda (Python 3.14)
- **API:** Amazon API Gateway (REST, regional)
- **Database:** Amazon DynamoDB (NoSQL, on-demand)
- **Email:** Gmail SMTP via smtplib
- **IAM:** DynamoDB full access + Lambda basic execution

## Cost

**$0/month** (all within AWS Free Tier):
- Amplify: 1000 build min/month
- Lambda: 1M requests/month
- API Gateway: 1M calls/month
- DynamoDB: 25GB storage
- Gmail SMTP: Free (500 recipients/day)
