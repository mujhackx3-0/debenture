# Fast API Guide - Esoteric Loan Sales Assistant

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
# REQUIRED: GROQ_API_KEY=your_actual_key_here
```

### 2. Run Locally (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn app.main:app --reload --port 8000

# Or use the main.py directly
python app/main.py
```

### 3. Run with Docker (Production)

```bash
# Build and run
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f esoteric-backend

# Stop
docker-compose down
```

---

## 📡 API Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **Docker**: `http://localhost:8000`

### Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔌 API Endpoints Reference

### Health & Monitoring

#### GET /health
Health check endpoint.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "timestamp": "2025-10-30T10:00:00"
}
```

#### GET /ready
Readiness check (verifies all services initialized).

```bash
curl http://localhost:8000/ready
```

#### GET /metrics
Application metrics.

```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "total_sessions": 10,
  "active_sessions": 3,
  "total_messages": 45,
  "avg_response_time_ms": 1250.5,
  "uptime_seconds": 3600.0
}
```

---

### Session Management

#### POST /api/v1/sessions
Create a new chat session.

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-30T10:00:00",
  "greeting_message": "Hello! I'm your AI Loan Sales Assistant from NBFC..."
}
```

#### GET /api/v1/sessions/{session_id}
Get session details.

```bash
curl http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "loan_application": {
    "applicant_name": "John Doe",
    "desired_amount": 300000,
    "loan_term_months": 24,
    "purpose": "Home renovation",
    "kyc_verified": true,
    "credit_score": 720,
    "credit_eligibility": "eligible",
    "offered_amount": 300000,
    "offered_interest_rate": 10.5,
    "sanction_letter_generated": false,
    "sanction_letter_url": null,
    "status": "offer_made"
  },
  "message_count": 8
}
```

#### DELETE /api/v1/sessions/{session_id}
Delete a session.

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000
```

---

### Chat (REST API)

#### POST /api/v1/chat
Send a message and get synchronous response.

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a loan of 3 lakh rupees",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Request Body:**
```json
{
  "message": "I need a loan of 3 lakh rupees",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Great! I can help you with a ₹3,00,000 loan. May I know your name?",
  "loan_application": {
    "applicant_name": null,
    "desired_amount": 300000,
    "loan_term_months": null,
    "purpose": null,
    "kyc_verified": false,
    "credit_score": null,
    "credit_eligibility": "pending",
    "offered_amount": null,
    "offered_interest_rate": null,
    "sanction_letter_generated": false,
    "sanction_letter_url": null,
    "status": "initiated"
  },
  "timestamp": "2025-10-30T10:00:00"
}
```

---

### WebSocket (Streaming Chat)

#### WS /api/v1/ws/{session_id}
Real-time streaming chat endpoint.

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/550e8400-e29b-41d4-a716-446655440000');

ws.onopen = () => {
  console.log('Connected');
  
  // Send message
  ws.send(JSON.stringify({
    message: "I need a loan of 3 lakh rupees"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  if (data.type === 'message') {
    console.log('Chunk:', data.content);
  } else if (data.type === 'end') {
    console.log('Final loan state:', data.loan_application);
  } else if (data.type === 'error') {
    console.error('Error:', data.content);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Python Example:**
```python
import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:8000/api/v1/ws/550e8400-e29b-41d4-a716-446655440000"
    
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "message": "I need a loan of 3 lakh rupees"
        }))
        
        # Receive responses
        async for message in websocket:
            data = json.loads(message)
            print(f"Type: {data['type']}, Content: {data['content']}")
            
            if data['type'] == 'end':
                print(f"Loan Application: {data['loan_application']}")
                break

asyncio.run(chat())
```

---

### RAG Knowledge Base

#### POST /api/v1/rag/query
Query the loan products knowledge base.

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the eligibility criteria for personal loans?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "query": "What are the eligibility criteria for personal loans?",
  "results": [
    "Eligibility Criteria: All applicants must be 21-60 years old, Indian citizens, with a minimum monthly income of ₹25,000 for personal loans.",
    "Personal Loan: Max ₹5,00,000, Interest Rate: 10-15%, Term: 12-60 months, Eligibility: Salaried employees, good credit score (650+).",
    "Credit Score Impact: A higher credit score (700+) usually results in better interest rates. Scores below 600 might lead to rejection."
  ],
  "sources": [
    "Internal Knowledge Base - Document 1",
    "Internal Knowledge Base - Document 2",
    "Internal Knowledge Base - Document 3"
  ]
}
```

---

## 💻 Frontend Integration Examples

### React Example

```typescript
// services/loanApi.ts
const API_BASE_URL = 'http://localhost:8000';

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  loan_application: LoanApplication;
  timestamp: string;
}

export const loanAPI = {
  // Create session
  async createSession(): Promise<{ session_id: string; greeting_message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return response.json();
  },

  // Send message
  async sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    return response.json();
  },

  // WebSocket connection
  connectWebSocket(sessionId: string, onMessage: (data: any) => void) {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${sessionId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    return ws;
  }
};
```

```tsx
// components/LoanChat.tsx
import { useState, useEffect } from 'react';
import { loanAPI } from './services/loanApi';

export function LoanChat() {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize session
    loanAPI.createSession().then(({ session_id, greeting_message }) => {
      setSessionId(session_id);
      setMessages([greeting_message]);
    });
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;
    
    setLoading(true);
    setMessages(prev => [...prev, `You: ${input}`]);
    
    try {
      const response = await loanAPI.sendMessage(input, sessionId);
      setMessages(prev => [...prev, `AI: ${response.message}`]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  return (
    <div className="loan-chat">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i}>{msg}</div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        placeholder="Type your message..."
        disabled={loading}
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
}
```

---

## 🧪 Testing

### Manual Testing with cURL

```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# 2. Send first message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I need a loan of 3 lakh rupees\", \"session_id\": \"$SESSION_ID\"}"

# 3. Send name
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"My name is John Doe\", \"session_id\": \"$SESSION_ID\"}"

# 4. Check session
curl http://localhost:8000/api/v1/sessions/$SESSION_ID
```

### Testing with Postman

1. Import the OpenAPI spec from `http://localhost:8000/openapi.json`
2. Create environment variables:
   - `base_url`: `http://localhost:8000`
   - `session_id`: (will be set dynamically)
3. Create test collection following the cURL examples above

---

## 🚀 Deployment

### Docker Production Deployment

```bash
# Build production image
docker-compose -f docker-compose.yml build

# Run in production mode
docker-compose up -d

# Scale workers
docker-compose up -d --scale esoteric-backend=3

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables for Production

```bash
# .env file for production
ENVIRONMENT=production
DEBUG=false
GROQ_API_KEY=your_production_key
SECRET_KEY=generate_strong_random_key_here
ALLOWED_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=WARNING
```

---

## 📊 Performance Optimization

### Current Optimizations

1. **Async Operations**: All I/O operations use asyncio
2. **Connection Pooling**: Sentence transformer model loaded once
3. **Message History Truncation**: Limited to 50 messages per session
4. **Timeout Handling**: 30s timeout on LLM calls
5. **Multi-stage Docker Build**: Reduced image size
6. **Health Checks**: Automatic container restart on failure

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test chat endpoint (requires token)
ab -n 100 -c 5 -p message.json -T application/json \
  http://localhost:8000/api/v1/chat
```

---

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **GROQ_API_KEY not set**
   ```bash
   # Verify environment variable
   echo $GROQ_API_KEY
   # Set it
   export GROQ_API_KEY=your_key_here
   ```

3. **Docker build fails**
   ```bash
   # Clear Docker cache
   docker system prune -a
   # Rebuild
   docker-compose build --no-cache
   ```

4. **ChromaDB persistence issues**
   ```bash
   # Delete and recreate
   rm -rf loan_sales_rag.db/
   # Restart application
   ```

---

## 📈 Monitoring

### Application Logs

```bash
# View logs
docker-compose logs -f esoteric-backend

# Filter errors
docker-compose logs esoteric-backend | grep ERROR
```

### Metrics Endpoint

Monitor via `/metrics` endpoint for:
- Total sessions created
- Active sessions
- Total messages processed
- Average response time
- Uptime

---

## 🔐 Security Best Practices

1. ✅ API key via environment variables
2. ✅ Input validation with Pydantic
3. ✅ CORS configuration
4. ✅ Error message sanitization
5. ✅ Non-root Docker user
6. ⚠️ TODO: Rate limiting (add SlowAPI)
7. ⚠️ TODO: JWT authentication
8. ⚠️ TODO: HTTPS/TLS in production

---

## 📝 API Rate Limits

Currently no rate limiting is enforced. For production, recommended limits:

- `/api/v1/chat`: 60 requests/minute per session
- `/api/v1/sessions`: 10 requests/minute per IP
- WebSocket: 100 messages/minute per session

---

**Production Ready Checklist:**

- [x] Environment variables for secrets
- [x] Async/await for I/O
- [x] Proper error handling
- [x] Health checks
- [x] Metrics endpoint
- [x] CORS configuration
- [x] Input validation
- [x] Logging
- [x] Docker multi-stage build
- [x] Session management
- [x] WebSocket support
- [ ] Rate limiting
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] Load testing
- [ ] CI/CD pipeline

