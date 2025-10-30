#!/usr/bin/env pwsh
# One-command deployment script for Esoteric FastAPI Backend

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Esoteric FastAPI Backend Deployment  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Stop any existing containers
Write-Host ""
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Build and start
Write-Host ""
Write-Host "Building and starting backend..." -ForegroundColor Yellow
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for backend to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Check health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 30 -UseBasicParsing
        Write-Host "✓ Backend is healthy!" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Backend starting... (this may take a minute)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  🚀 ESOTERIC BACKEND IS RUNNING!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📡 API Documentation:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "🏥 Health Check:       http://localhost:8000/health" -ForegroundColor White
    Write-Host "📊 Metrics:            http://localhost:8000/metrics" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Quick Test:" -ForegroundColor Yellow
    Write-Host '   curl http://localhost:8000/health' -ForegroundColor Gray
    Write-Host ""
    Write-Host "📋 View Logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs -f esoteric-backend" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⏹  Stop Backend:" -ForegroundColor Yellow
    Write-Host "   docker-compose down" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "✗ Deployment failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs" -ForegroundColor Gray
    exit 1
}

