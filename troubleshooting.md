# Troubleshooting Guide

Quick fixes for common issues when setting up or running Smart Cafe.

---

## Order form shows "Failed to place order"

**Check:** Is your API Gateway URL correct in `frontend/*.html`?
```javascript
const API_URL = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
```

**Check:** Did you deploy the API after making changes? (Actions → Deploy API → prod)

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
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod \
  -H "Content-Type: application/json" \
  -d '{"customerName":"Test","customerEmail":"t@t.com","items":[{"name":"Latte","quantity":1,"price":4.5}]}'

# Check Lambda logs
aws logs tail /aws/lambda/cafe-order-processor --region us-east-1 --follow

# Check database
aws dynamodb scan --table-name CafeOrders --region us-east-1
```
