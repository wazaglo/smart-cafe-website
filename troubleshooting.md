# Troubleshooting Guide

Quick fixes for common issues when setting up or running Smart Cafe.

---

## Order form shows "NetworkError" or "Failed to place order"

**Check:** Is the `API_URL` correct in `frontend/*.html`?
```javascript
const API_URL = '__API_URL__';
```

The `__API_URL__` placeholder is replaced at build time by Amplify using the `API_URL` environment variable.

**Check:** If using CloudFront, is the distribution deployed and enabled?
- Go to CloudFront Console → distributions → check status is "Deployed"

**Check:** Did you deploy the API Gateway after making changes?
- Actions → Deploy API → prod

---

## Orders not saving to DynamoDB

**Check Lambda logs** (CloudWatch) for errors like:
- `"Float types are not supported"` — Convert floats to `Decimal(str(value))`
- `"NoneType has no attribute strip"` — Handle `null` fields with `(val or '').strip()`
- `"Task timed out"` — Increase Lambda timeout to 30 seconds in Configuration

---

## Emails not being sent

**Most common cause:** Gmail App Password is missing or wrong.

**Fix:**
1. Enable 2-Step Verification in your Google Account
2. Go to Security → App passwords → Generate a 16-char password
3. Set it as `GMAIL_APP_PASSWORD` in Lambda environment variables

---

## Admin dashboard shows no orders

**Check:** Does your API Gateway have `GET /` connected to the `get-orders` Lambda?

**Check:** Did you enable CORS? (Resources → Actions → Enable CORS → Deploy)

---

## WAF blocking legitimate traffic

WAF rules are configured to block common web threats. If the WAF is blocking valid requests:
1. Go to WAF & Shield Console → Web ACLs → `CreatedByCloudFront-*`
2. Check the **Sampled requests** tab to see what was blocked
3. Create an **allowlist rule** (higher priority) for the specific IP or pattern

---

## Everything deployed but site is blank

**If using Amplify:** Make sure `amplify.yml` in the repo root has:
```yaml
artifacts:
  baseDirectory: frontend
```

---

## Quick Commands

```bash
# Test the API
curl -X POST https://your-cloudfront-domain.cloudfront.net/prod \
  -H "Content-Type: application/json" \
  -d '{"customerName":"Test","customerEmail":"t@t.com","items":[{"name":"Latte","quantity":1,"price":4.5}]}'

# Check Lambda logs
aws logs tail /aws/lambda/cafe-order-processor --region us-east-1 --follow

# Check database
aws dynamodb scan --table-name CafeOrders --region us-east-1

# Check WAF blocked requests
aws wafv2 get-web-acl --name CreatedByCloudFront-f5e1fb9b --scope CLOUDFRONT --id $(aws wafv2 list-web-acls --scope CLOUDFRONT --query 'WebACLs[0].Id' --output text) --region us-east-1
```
