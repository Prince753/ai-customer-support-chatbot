# Vercel Deployment Preparation Script for Windows
# Run this before deploying to Vercel

Write-Host "🚀 Preparing project for Vercel deployment..." -ForegroundColor Cyan

# Create public directory structure
Write-Host "📁 Creating public directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "public/admin" | Out-Null
New-Item -ItemType Directory -Force -Path "public/widget" | Out-Null

# Copy demo store
Write-Host "📄 Copying demo store..." -ForegroundColor Yellow
Copy-Item "frontend/demo-store/index.html" -Destination "public/index.html" -Force

# Copy admin dashboard
Write-Host "📄 Copying admin dashboard..." -ForegroundColor Yellow
Copy-Item "frontend/admin-dashboard/index.html" -Destination "public/admin/index.html" -Force
Copy-Item "frontend/admin-dashboard/dashboard.css" -Destination "public/admin/dashboard.css" -Force
Copy-Item "frontend/admin-dashboard/dashboard.js" -Destination "public/admin/dashboard.js" -Force

# Copy chat widget
Write-Host "📄 Copying chat widget..." -ForegroundColor Yellow
Copy-Item "frontend/chat-widget/index.html" -Destination "public/widget/index.html" -Force
Copy-Item "frontend/chat-widget/widget.css" -Destination "public/widget/widget.css" -Force
Copy-Item "frontend/chat-widget/widget.js" -Destination "public/widget/widget.js" -Force

# Update API URLs in widget.js for production
Write-Host "🔧 Updating API URLs for production..." -ForegroundColor Yellow
$widgetJs = Get-Content "public/widget/widget.js" -Raw
$widgetJs = $widgetJs -replace "http://localhost:8000/api/v1", "/api/v1"
Set-Content "public/widget/widget.js" -Value $widgetJs

$dashboardJs = Get-Content "public/admin/dashboard.js" -Raw
$dashboardJs = $dashboardJs -replace "http://localhost:8000/api/v1", "/api/v1"
Set-Content "public/admin/dashboard.js" -Value $dashboardJs

Write-Host ""
Write-Host "✅ Preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run 'vercel login' if not already logged in"
Write-Host "2. Run 'vercel' to deploy to preview"
Write-Host "3. Run 'vercel --prod' to deploy to production"
Write-Host ""
Write-Host "Don't forget to set environment variables in Vercel dashboard!" -ForegroundColor Yellow
