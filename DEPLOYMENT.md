# Deployment Information

## Public URL
https://my-projct-production-ac3d.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://my-projct-production-ac3d.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://my-projct-production-ac3d.up.railway.app/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/railway.png)
- [Service running](screenshots/load_balancer.png)
- [Test results](screenshots/rate_test.png)
