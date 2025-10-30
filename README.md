# Esoteric - AI Loan Sales Assistant

> **Conversational Loan Sales Assistant** - An intelligent digital chatbot for NBFC personal loan conversions

## 📋 Overview

Esoteric is an AI-powered conversational assistant designed to revolutionize personal loan sales for Non-Banking Financial Companies (NBFCs). Built with LangChain, LangGraph, and Groq LLM, it provides an intelligent, personalized approach to loan applications, replacing impersonal lead generation with engaging customer interactions.

### Key Features

- 🤖 **Intelligent Conversation Flow** - Natural dialogue for loan application gathering
- 🔐 **KYC Verification** - Simulated Know Your Customer verification process
- 💳 **Credit Assessment** - Automated creditworthiness evaluation
- 📄 **Sanction Letter Generation** - Digital loan approval document creation
- 📚 **RAG-based Knowledge Base** - ChromaDB-powered loan product information retrieval
- 💬 **Persistent Chat Memory** - SQLite-based conversation history
- 🎯 **Agentic Workflow** - LangGraph state machine for complex loan processes

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup)
- Groq API Key ([Get one here](https://console.groq.com/))

---

## 📦 Installation Methods

### Option 1: Docker (Recommended)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/mujhackx3-0/Esoteric.git
cd Esoteric
```

#### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# Windows (PowerShell)
notepad .env

# Linux/Mac
nano .env
```

**Required configuration in `.env`:**
```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL_NAME=mixtral-8x7b-32768
```

#### Step 3: Build and Run with Docker Compose
```bash
# Build the Docker image
docker-compose build

# Run the container
docker-compose up

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

#### Step 4: Interact with the Chatbot
```bash
# Attach to the running container for interactive session
docker attach esoteric-app
```

---

### Option 2: Local Python Setup

#### Step 1: Clone the Repository
```bash
git clone https://github.com/mujhackx3-0/Esoteric.git
cd Esoteric
```

#### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment

**Option A: Using .env file**
```bash
cp .env.example .env
# Edit .env with your Groq API key
```

**Option B: Export environment variable**

*Windows (PowerShell):*
```powershell
$env:GROQ_API_KEY="your_actual_groq_api_key_here"
```

*Linux/Mac:*
```bash
export GROQ_API_KEY="your_actual_groq_api_key_here"
```

#### Step 5: Run the Application
```bash
python "ai_studio_code (1).py"
```

---

## 🐳 Docker Commands Reference

### Building
```bash
# Build the image
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build using Dockerfile directly
docker build -t esoteric-app .
```

### Running
```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# Run specific service
docker-compose up esoteric-loan-assistant

# Run with Docker directly
docker run -it --env-file .env esoteric-app
```

### Managing
```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove with volumes
docker-compose down -v

# View logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Debugging
```bash
# Access running container shell
docker exec -it esoteric-app /bin/bash

# Inspect container
docker inspect esoteric-app

# View resource usage
docker stats esoteric-app
```

---

## 📚 Project Structure

```
Esoteric/
├── ai_studio_code (1).py    # Main application file
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose configuration
├── .dockerignore           # Docker build exclusions
├── .env.example            # Environment template
├── .env                    # Your environment config (create this)
├── README.md              # This file
├── chat_memory_loan_sales.db  # SQLite chat history (auto-generated)
└── loan_sales_rag.db/         # ChromaDB vector store (auto-generated)
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Your Groq API authentication key | - | ✅ Yes |
| `GROQ_MODEL_NAME` | Groq LLM model to use | `mixtral-8x7b-32768` | ❌ No |
| `SQLITE_DB_PATH` | Path to SQLite chat history database | `chat_memory_loan_sales.db` | ❌ No |
| `CHROMA_DB_PERSIST_DIR` | ChromaDB persistence directory | `loan_sales_rag.db` | ❌ No |

### Supported Groq Models

- `mixtral-8x7b-32768` (Default, Recommended)
- `llama3-70b-8192`
- `llama3-8b-8192`
- `gemma-7b-it`

Check [Groq Console](https://console.groq.com/docs/models) for the latest available models.

---

## 💡 Usage

### Starting a Conversation

Once the application is running, you'll see:

```
=== NBFC AI Loan Sales Assistant ===
I'm here to help you with your personal loan application.

Hello! I'm your AI Loan Sales Assistant from NBFC. I can help you find 
the right personal loan. What kind of loan are you interested in, or 
how much do you need?

Customer: 
```

### Example Conversation Flow

```
Customer: I need a personal loan of 3 lakh rupees
AI: Great! I can help you with that. May I have your name please?

Customer: My name is Rahul Kumar
AI: Thank you, Rahul. What is the purpose of this loan?

Customer: Home renovation
AI: Understood. How many months would you like to repay this loan?

Customer: 24 months
AI: Perfect! Let me verify your KYC details and check your eligibility...
[Process continues with credit check, offer, and sanction letter]
```

### Available Commands

- Type your message to interact with the assistant
- Type `quit`, `exit`, `bye`, or `end` to exit the conversation

---

## 🏗️ Architecture

### Tech Stack

- **LLM Provider**: Groq (Mixtral-8x7b)
- **Framework**: LangChain + LangGraph
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Chat Memory**: SQLite
- **Orchestration**: LangGraph StateGraph

### Workflow States

1. **Initiated** → Initial information gathering
2. **KYC Pending** → Customer verification
3. **Credit Check Pending** → Creditworthiness evaluation
4. **Offer Made** → Loan offer presentation
5. **Sanctioned** → Approval and letter generation
6. **Rejected** → Application declined

### Tools & Capabilities

- `update_loan_application_details` - Capture loan information
- `retrieve_context` - RAG-based knowledge retrieval
- `verify_kyc` - KYC verification simulation
- `evaluate_creditworthiness` - Credit assessment
- `generate_loan_sanction_letter` - Digital approval letter

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Build Fails
```bash
# Clear Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

#### 2. API Key Error
```
Error: Invalid API key
```
**Solution**: Verify your `.env` file has the correct `GROQ_API_KEY`

#### 3. Permission Issues (Linux/Mac)
```bash
# Fix database file permissions
chmod 666 chat_memory_loan_sales.db
chmod -R 777 loan_sales_rag.db/
```

#### 4. Port Already in Use
```bash
# Find and stop conflicting containers
docker ps
docker stop <container_id>
```

#### 5. Module Import Errors
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

---

## 🧪 Development

### Running Tests
```bash
# Add test framework (pytest recommended)
pip install pytest
pytest tests/
```

### Code Formatting
```bash
# Install formatting tools
pip install black ruff

# Format code
black .

# Lint code
ruff check .
```

### Modifying the Application

1. Edit `ai_studio_code (1).py`
2. Update dependencies in `requirements.txt` if needed
3. Rebuild Docker image: `docker-compose build`
4. Restart: `docker-compose up`

---

## 📊 Data Persistence

### Chat History
- **File**: `chat_memory_loan_sales.db`
- **Type**: SQLite database
- **Purpose**: Stores conversation history per session

### RAG Knowledge Base
- **Directory**: `loan_sales_rag.db/`
- **Type**: ChromaDB vector store
- **Purpose**: Loan product information and eligibility criteria

### Volume Mapping (Docker)
```yaml
volumes:
  - ./data:/app/data
  - ./chat_memory_loan_sales.db:/app/chat_memory_loan_sales.db
  - ./loan_sales_rag.db:/app/loan_sales_rag.db
```

---

## 🔒 Security Considerations

### Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use environment variables** - Don't hardcode API keys
3. **Rotate API keys regularly** - Update in Groq console
4. **Secure database files** - Restrict file permissions
5. **Use HTTPS in production** - Encrypt data in transit

### Production Deployment

For production use:
- Set up proper authentication
- Implement rate limiting
- Use managed database services
- Enable logging and monitoring
- Configure secrets management (AWS Secrets Manager, Azure Key Vault)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is part of an EY Problem Statement #5 for NBFC loan conversion optimization.

---

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [mujhackx3-0](https://github.com/mujhackx3-0)

---

## 🎯 Roadmap

- [ ] Add real KYC integration
- [ ] Implement actual credit bureau APIs
- [ ] Multi-language support
- [ ] Web UI interface
- [ ] Analytics dashboard
- [ ] Webhook integrations for CRM systems

---

**Built with ❤️ using LangChain & Groq**
