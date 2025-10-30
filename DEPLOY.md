# 🚀 DEPLOYMENT GUIDE - Esoteric FastAPI Backend

## ✅ PRE-CONFIGURED & READY TO DEPLOY

All configuration is **DONE**. Groq API key is embedded. Just run the deployment command!

---

## 🎯 ONE-COMMAND DEPLOYMENT

### Windows PowerShell:
```powershell
.\deploy.ps1
```

### Alternative (Docker Compose):
```bash
docker-compose up --build -d
```

That's it! The backend will be running at **http://localhost:8000**

---

## 📡 ACCESS YOUR API

Once deployed, access these endpoints:

| Endpoint | URL | Description |
|----------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| **Alternative Docs** | http://localhost:8000/redoc | ReDoc documentation |
| **Health Check** | http://localhost:8000/health | Service health status |
| **Metrics** | http://localhost:8000/metrics | Performance metrics |
| **Root** | http://localhost:8000 | API information |

---

## 🧪 QUICK TEST

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "timestamp": "2025-10-30T10:54:33"
}
```

### 2. Create Chat Session
```bash
curl -X POST http://localhost:8000/api/v1/sessions
```

**Expected Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-30T10:54:33",
  "greeting_message": "Hello! I'm your AI Loan Sales Assistant from NBFC..."
}
```

### 3. Send Message
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I need a loan of 3 lakh rupees\", \"session_id\": \"YOUR_SESSION_ID\"}"
```

---

## 📋 DOCKER COMMANDS

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f esoteric-backend

# View last 100 lines
docker-compose logs --tail=100 esoteric-backend
```

### Stop Backend
```bash
docker-compose down
```

### Restart Backend
```bash
docker-compose restart
```

### Rebuild & Restart
```bash
docker-compose up --build -d
```

### Check Status
```bash
docker-compose ps
```

---

## 🔧 CONFIGURATION

### Environment Variables (Already Set in .env)

| Variable | Value | Description |
|----------|-------|-------------|
| `GROQ_API_KEY` | `gsk_oYSr...` | ✅ Pre-configured |
| `GROQ_MODEL_NAME` | `mixtral-8x7b-32768` | LLM model |
| `PORT` | `8000` | API port |
| `ENVIRONMENT` | `production` | Deployment env |
| `LOG_LEVEL` | `INFO` | Logging level |

**All environment variables are pre-configured in `.env` file.**

---

## 🌐 CONNECT FRONTEND

### JavaScript/React Example:

```javascript
// Create session
const response = await fetch('http://localhost:8000/api/v1/sessions', {
  method: 'POST'
});
const { session_id, greeting_message } = await response.json();

// Send message
const chatResponse = await fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'I need a loan of 3 lakh rupees',
    session_id: session_id
  })
});
const result = await chatResponse.json();
console.log(result.message);
```

### WebSocket Example:

```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${session_id}`);

ws.onopen = () => {
  ws.send(JSON.stringify({ message: 'I need a loan' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

---

## 🐛 TROUBLESHOOTING

### Backend Not Starting

1. **Check Docker is running:**
   ```bash
   docker info
   ```

2. **View logs for errors:**
   ```bash
   docker-compose logs esoteric-backend
   ```

3. **Rebuild from scratch:**
   ```bash
   docker-compose down
   docker system prune -a  # Clean everything
   docker-compose up --build
   ```

### Port 8000 Already in Use

```bash
# Windows - Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in .env file
PORT=8001
```

### API Key Issues

The API key is **hardcoded** in both `.env` and `docker-compose.yml`. If you need to change it:

1. Edit `.env`:
   ```bash
   GROQ_API_KEY=your_new_key_here
   ```

2. Restart:
   ```bash
   docker-compose restart
   ```

### Slow First Response

First response may be slow (10-30 seconds) due to:
- Model initialization
- Embedding model loading
- ChromaDB indexing

Subsequent responses will be much faster (1-3 seconds).

---

## 📊 PERFORMANCE

### Expected Performance:
- **Startup Time**: 30-60 seconds
- **First Request**: 10-30 seconds (initialization)
- **Subsequent Requests**: 1-3 seconds
- **Concurrent Users**: 50-100 users
- **Memory Usage**: 500MB-1GB

### Monitor Performance:
```bash
# View metrics
curl http://localhost:8000/metrics

# Docker stats
docker stats esoteric-backend
```

---

## 🔒 SECURITY NOTES

### For Production Deployment:

1. **Change SECRET_KEY** in `.env`:
   ```bash
   SECRET_KEY=generate-a-strong-random-key-here
   ```

2. **Configure CORS** for your frontend domain:
   ```bash
   ALLOWED_ORIGINS=["https://yourdomain.com"]
   ```

3. **Use HTTPS** - Deploy behind reverse proxy (Nginx/Traefik)

4. **Add Rate Limiting** - See API_GUIDE.md for details

5. **Setup Monitoring** - Use Prometheus + Grafana

---

## 📦 DEPLOYMENT CHECKLIST

- [x] Groq API key configured
- [x] Docker Compose file ready
- [x] Environment variables set
- [x] Health checks enabled
- [x] CORS configured (allow all for dev)
- [x] Logging enabled
- [x] Metrics endpoint available
- [ ] Change SECRET_KEY for production
- [ ] Configure CORS for your domain
- [ ] Setup HTTPS/TLS
- [ ] Add rate limiting
- [ ] Setup monitoring

---

## 🆘 SUPPORT

### Common Issues:

**Q: Backend returns 500 errors**  
A: Check logs with `docker-compose logs esoteric-backend`

**Q: Groq API errors**  
A: Verify API key is valid and has credits

**Q: ChromaDB errors**  
A: Delete volume: `docker volume rm esoteric_loan_sales_rag_data`

**Q: Memory issues**  
A: Increase Docker memory limit in Docker Desktop settings

---

## 🎉 SUCCESS!

If you see this response from `/health`:
```json
{"status": "healthy", "version": "2.0.0"}
```

**Your backend is LIVE and ready for frontend integration!** 🚀

---

## 📚 NEXT STEPS

1. ✅ Open http://localhost:8000/docs to explore API
2. ✅ Test endpoints with Postman or cURL
3. ✅ Connect your frontend using examples above
4. ✅ Monitor logs: `docker-compose logs -f`
5. ✅ Check metrics: http://localhost:8000/metrics

---

**The backend is 100% configured and ready. Just run `.\deploy.ps1` or `docker-compose up`!**

