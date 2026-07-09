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

### 3. Gmail App Password Setup

1. Go to your Google Account → **Security** → **2-Step Verification** → Turn it **ON**
2. Go to **App passwords** (under 2-Step Verification)
3. Select app: **Mail** → device: **Other (Custom name)** → enter "Smart Cafe Lambda"
4. Copy the **16-character password** that appears
5. Set it as `GMAIL_APP_PASSWORD` in Lambda environment variables

### 4. API Gateway & CloudFront

This project uses **CloudFront** as a CDN and security edge in front of API Gateway:

```
Frontend → CloudFront → WAF (SQLi, XSS, DDoS protection) → API Gateway → Lambda → DynamoDB
```

Update the `API_URL` constant in every `.html` file under `frontend/` to your CloudFront URL:

```javascript
const API_URL = 'https://your-cloudfront-domain.cloudfront.net/prod';
```

If you forked this project, replace it with your own CloudFront domain. The API Gateway can also be called directly at:
```
https://your-api-id.execute-api.your-region.amazonaws.com/prod
```

See `backend/README.md` for full step-by-step API Gateway setup.

### 5. CloudFront + WAF Setup

1. Create a CloudFront distribution with API Gateway as origin
2. Use cache policy: `CachingDisabled`
3. Use origin request policy: `AllViewerExceptHostHeader`
4. Subscribe to the **Free flat-rate pricing plan** ($0/month — includes WAF at no extra cost)
5. Attach a WAF web ACL with these managed rule groups set to `Block`:
   - `AWSManagedRulesCommonRuleSet` (SQLi, XSS, LFI, RFI)
   - `AWSManagedRulesAmazonIpReputationList` (DDoS IPs)
   - `AWSManagedRulesKnownBadInputsRuleSet` (path traversal, Log4j)

### 6. DynamoDB Table

Create a table named `CafeOrders` with:
- **Partition key:** `orderId` (String)
- **Sort key:** `customerEmail` (String)
- **Capacity:** On-demand

### 7. IAM Permissions

The Lambda execution role needs these policies:
- `AmazonDynamoDBFullAccess` — read/write orders
- `AWSLambdaBasicExecutionRole` — CloudWatch logs

## Security Best Practices

- **Never hardcode credentials.** All sensitive values are read from Lambda environment variables.
- **Use Gmail App Passwords** instead of your regular Gmail password.
- **Rotate App Passwords** periodically if deploying for production.
- **WAF protects at the edge.** The CloudFront distribution sits in front of API Gateway with WAF rules blocking common web exploits before they reach your backend.
- **IAM least privilege.** The Lambda role has more access than needed for demo purposes. For production, scope DynamoDB access to specific table and actions.

## Reporting Issues

If you find a security concern in this repo, open an issue on GitHub.
