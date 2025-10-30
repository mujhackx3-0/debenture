# Esoteric FastAPI Backend - Quick Start Script
# For Windows PowerShell

Write-Host "🚀 Esoteric Loan Sales Assistant - FastAPI Backend" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔑 IMPORTANT: Edit .env and add your GROQ_API_KEY!" -ForegroundColor Red
    Write-Host "   Press any key to open .env in notepad..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    notepad .env
    Write-Host ""
}

# Ask user for run mode
Write-Host "Select run mode:" -ForegroundColor Cyan
Write-Host "1. Docker (Recommended for production)" -ForegroundColor White
Write-Host "2. Local Python (For development)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "1") {
    # Docker mode
    Write-Host ""
    Write-Host "🐳 Starting with Docker..." -ForegroundColor Cyan
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-Host "✅ Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "Building and starting containers..." -ForegroundColor Cyan
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Backend is starting up!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📡 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "🏥 Health Check:     http://localhost:8000/health" -ForegroundColor Cyan
        Write-Host "📊 Metrics:          http://localhost:8000/metrics" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "View logs with: docker-compose logs -f esoteric-backend" -ForegroundColor Yellow
        Write-Host "Stop with:      docker-compose down" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "❌ Failed to start Docker containers" -ForegroundColor Red
        Write-Host "   Check docker-compose logs for details" -ForegroundColor Yellow
    }
    
} elseif ($choice -eq "2") {
    # Local Python mode
    Write-Host ""
    Write-Host "🐍 Starting with local Python..." -ForegroundColor Cyan
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
        Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    # Check if virtual environment exists
    if (!(Test-Path "venv")) {
        Write-Host ""
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        python -m venv venv
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate virtual environment
    Write-Host ""
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    
    # Start server
    Write-Host ""
    Write-Host "🚀 Starting FastAPI server..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📡 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🏥 Health Check:     http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host "📊 Metrics:          http://localhost:8000/metrics" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    python -m uvicorn app.main:app --reload --port 8000
    
} else {
    Write-Host ""
    Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
    exit 1
}

