#!/bin/bash
# Vercel Deployment Preparation Script
# Run this before deploying to Vercel

echo "🚀 Preparing project for Vercel deployment..."

# Create public directory structure
echo "📁 Creating public directory structure..."
mkdir -p public/admin
mkdir -p public/widget

# Copy demo store
echo "📄 Copying demo store..."
cp frontend/demo-store/index.html public/index.html

# Copy admin dashboard
echo "📄 Copying admin dashboard..."
cp frontend/admin-dashboard/index.html public/admin/index.html
cp frontend/admin-dashboard/dashboard.css public/admin/dashboard.css
cp frontend/admin-dashboard/dashboard.js public/admin/dashboard.js

# Copy chat widget
echo "📄 Copying chat widget..."
cp frontend/chat-widget/index.html public/widget/index.html
cp frontend/chat-widget/widget.css public/widget/widget.css
cp frontend/chat-widget/widget.js public/widget/widget.js

# Update API URLs in widget.js for production
echo "🔧 Updating API URLs for production..."
sed -i "s|http://localhost:8000/api/v1|/api/v1|g" public/widget/widget.js
sed -i "s|http://localhost:8000/api/v1|/api/v1|g" public/admin/dashboard.js

echo "✅ Preparation complete!"
echo ""
echo "Next steps:"
echo "1. Run 'vercel login' if not already logged in"
echo "2. Run 'vercel' to deploy to preview"
echo "3. Run 'vercel --prod' to deploy to production"
echo ""
echo "Don't forget to set environment variables in Vercel dashboard!"
