# Security & Setup Guide

## What You Need to Configure

All sensitive values are managed via Lambda environment variables — nothing is hardcoded in the source code.

### 1. AWS Account

Create an AWS account at [aws.amazon.com](https://aws.amazon.com). The free tier covers all services used.

### 2. Lambda Environment Variables

After deploying each Lambda function to AWS, set these environment variables in the Lambda console:

| Variable | Description | Where to Set |
|----------|-------------|-------------|
| `GMAIL_USER` | Your Gmail address (must have 2FA enabled) | `cafe-order-processor`, `update-order-status` |
| `GMAIL_APP_PASSWORD` | 16-char Gmail App Password (see below) | `cafe-order-processor`, `update-order-status` |
| `ADMIN_EMAIL` | Email to receive admin notifications | `cafe-order-processor` |
| `COMPANY_NAME` | Business name for email templates | `cafe-order-processor`, `update-order-status` |
| `API_URL` | Your API Gateway invoke URL | Amplify environment variable + `frontend/*.html` |

### 3. Gmail App Password Setup

1. Go to your Google Account → **Security** → **2-Step Verification** → Turn it **ON**
2. Go to **App passwords** (under 2-Step Verification)
3. Select app: **Mail** → device: **Other (Custom name)** → enter "Smart Cafe Lambda"
4. Copy the **16-character password** that appears
5. Set it as `GMAIL_APP_PASSWORD` in Lambda environment variables

### 4. API Gateway

Deploy your own API Gateway and update the `API_URL` constant in every `.html` file under `frontend/`:

```javascript
const API_URL = 'https://your-api-id.execute-api.your-region.amazonaws.com/prod';
```

Or use an Amplify environment variable to inject it at build time.

See `backend/README.md` for full step-by-step API Gateway setup.

### 5. DynamoDB Table

Create a table named `CafeOrders` with:
- **Partition key:** `orderId` (String)
- **Sort key:** `customerEmail` (String)
- **Capacity:** On-demand

### 6. IAM Permissions

The Lambda execution role needs these policies:
- `AmazonDynamoDBFullAccess` — read/write orders
- `AWSLambdaBasicExecutionRole` — CloudWatch logs

## Security Best Practices

- **Never hardcode credentials.** All sensitive values are read from Lambda environment variables.
- **Use Gmail App Passwords** instead of your regular Gmail password.
- **Rotate App Passwords** periodically if deploying for production.
- **IAM least privilege.** The Lambda role has more access than needed for demo purposes. For production, scope DynamoDB access to specific table and actions.

## Reporting Issues

If you find a security concern in this repo, open an issue on GitHub.
