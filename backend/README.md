# Backend: AWS Setup Guide

This directory contains the Lambda functions for the Smart Cafe backend. Each subdirectory is a separate Lambda function.

## Lambda Functions

| Function | File | Trigger | Purpose |
|----------|------|---------|---------|
| `cafe-order-processor` | `lambda/cafe-order-processor/lambda_function.py` | POST / | Place new order, send email notifications |
| `get-orders` | `lambda/get-orders/lambda_function.py` | GET / | List all orders or look up by `?orderId=` |
| `update-order-status` | `lambda/update-order-status/lambda_function.py` | PUT / | Update order status, notify when ready |
| `get-analytics` | `lambda/get-analytics/lambda_function.py` | GET /analytics | Revenue stats and popular items |
| `get-order-status` | `lambda/get-order-status/lambda_function.py` | (Optional) GET /order | Dedicated single-order lookup |

---

## Step-by-Step: API Gateway Setup (AWS Console)

### 1. Create the REST API

1. Go to **API Gateway** → **Create API**
2. Select **REST API (not HTTP API)** → **Build**
3. **API name:** `CafeOrderAPI`
4. **Endpoint type:** Regional
5. Click **Create API**

### 2. Set Up the Root Resource Methods

Your API already has a root path `/`. You need to attach these methods:

#### POST / — Place Order
1. Select `/` resource → **Actions** → **Create Method**
2. Method: **POST** → checkmark
3. Integration type: **Lambda Function**
4. **Use Lambda Proxy integration:** ✅ checked
5. **Lambda Region:** `us-east-1`
6. **Lambda Function:** `cafe-order-processor`
7. Click **Save** → **OK** (to add Lambda permission)

#### GET / — Get Orders
1. Select `/` resource → **Actions** → **Create Method**
2. Method: **GET** → checkmark
3. Integration type: **Lambda Function**
4. **Use Lambda Proxy integration:** ✅ checked
5. **Lambda Function:** `get-orders`
6. Click **Save** → **OK**

#### PUT / — Update Order Status
1. Select `/` resource → **Actions** → **Create Method**
2. Method: **PUT** → checkmark
3. Integration type: **Lambda Function**
4. **Use Lambda Proxy integration:** ✅ checked
5. **Lambda Function:** `update-order-status`
6. Click **Save** → **OK**

### 3. Add the /analytics Resource (for Analytics)

1. Select `/` resource → **Actions** → **Create Resource**
2. **Resource Path:** `/analytics`
3. **Resource Name:** `analytics`
4. Click **Create Resource**
5. Select `/analytics` → **Actions** → **Create Method**
6. Method: **GET** → checkmark
7. Integration type: **Lambda Function**, proxy checked
8. **Lambda Function:** `get-analytics`
9. Click **Save** → **OK**

### 4. Enable CORS on All Methods

1. Select `/` resource → **Actions** → **Enable CORS**
2. Check: **GET**, **POST**, **PUT**, **OPTIONS**
3. Click **Enable CORS and replace existing CORS headers**
4. Click **Yes, replace existing values**
5. Repeat for `/analytics` resource (check GET, OPTIONS)

### 5. Deploy the API

1. Select **Actions** → **Deploy API**
2. **Deployment stage:** [New Stage]
3. **Stage name:** `prod`
4. Click **Deploy**
5. Copy the **Invoke URL** (looks like `https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod`)

### 6. Update Frontend

Replace the `API_URL` value in all `frontend/*.html` files with your Invoke URL:

```javascript
const API_URL = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
```

---

## Step 7 (Optional): CloudFront + WAF (Recommended)

Put CloudFront in front of your API Gateway for CDN caching and edge security via AWS WAF — all included in the CloudFront Free plan ($0/month).

### Create CloudFront Distribution

1. Go to **CloudFront** → **Create Distribution**
2. **Origin domain:** Select your API Gateway (`CafeOrderAPI`)
3. **Protocol:** HTTPS only
4. **Cache policy:** `CachingDisabled`
5. **Origin request policy:** `AllViewerExceptHostHeader`
6. **Allowed methods:** GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
7. Click **Create Distribution**

### Subscribe to Free Plan

1. While viewing your distribution, click the **Pricing Plan** tab
2. Select **Free** ($0/month — includes WAF, DDoS protection, and Route 53 DNS)
3. Confirm

### Create and Attach WAF Web ACL

1. Go to **WAF & Shield** → **Web ACLs** → **Create web ACL**
2. **Scope:** CloudFront (global)
3. Add managed rule groups:
   - `AWSManagedRulesCommonRuleSet` — set key rules to **Block** (SQLi, XSS, LFI, RFI)
   - `AWSManagedRulesAmazonIpReputationList` — block DDoS source IPs
   - `AWSManagedRulesKnownBadInputsRuleSet` — block path traversal, Log4j
4. Associate the web ACL with your CloudFront distribution

### Update Frontend

Replace `API_URL` in all `frontend/*.html` files with your CloudFront domain:

```javascript
const API_URL = 'https://your-cloudfront-domain.cloudfront.net/prod';
```

---

## Deploying Lambda Code

After making changes to any Lambda function, deploy it:

```bash
# Using AWS CLI
cd backend/lambda/<function-name>
zip -r function.zip lambda_function.py
aws lambda update-function-code \
  --function-name <function-name> \
  --zip-file fileb://function.zip \
  --region us-east-1 \
  --publish
```

Or upload `lambda_function.py` directly in the Lambda console (Code → Upload from → .zip file).

---

## Lambda Environment Variables

Set these in Lambda console (Configuration → Environment variables):

| Lambda | Variables |
|--------|-----------|
| `cafe-order-processor` | `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ADMIN_EMAIL`, `COMPANY_NAME` |
| `update-order-status` | `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `COMPANY_NAME` |
| `get-orders` | *(none needed)* |
| `get-analytics` | *(none needed)* |
| `get-order-status` | *(none needed)* |

See `SECURITY.md` for how to get a Gmail App Password.

---

## Lambda Configuration

Set these in Lambda console (Configuration → General configuration):

| Setting | Value |
|---------|-------|
| Timeout | **30 seconds** |
| Memory | **128 MB** (default is fine) |
| IAM Role | Must have `AmazonDynamoDBFullAccess` + `AWSLambdaBasicExecutionRole` |

---

## Testing

```bash
# Place an order (via CloudFront)
curl -X POST https://your-cloudfront-domain.cloudfront.net/prod \
  -H "Content-Type: application/json" \
  -d '{"customerName":"Test","customerEmail":"test@example.com","items":[{"name":"Latte","quantity":1,"price":4.50}]}'

# Place an order (direct to API Gateway)
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod \
  -H "Content-Type: application/json" \
  -d '{"customerName":"Test","customerEmail":"test@example.com","items":[{"name":"Latte","quantity":1,"price":4.50}]}'

# Get all orders
curl https://your-cloudfront-domain.cloudfront.net/prod

# Get single order
curl "https://your-cloudfront-domain.cloudfront.net/prod?orderId=ORD-XXXXXXXX-XXXX"

# Update status
curl -X PUT https://your-cloudfront-domain.cloudfront.net/prod \
  -H "Content-Type: application/json" \
  -d '{"orderId":"ORD-XXXXXXXX-XXXX","orderStatus":"ready"}'

# Analytics
curl https://your-cloudfront-domain.cloudfront.net/prod/analytics
```
