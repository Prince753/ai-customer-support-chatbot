# 🚀 Vercel Deployment Guide

Deploy the AI Customer Support Chatbot to Vercel for a production-ready, globally distributed application.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture on Vercel](#architecture-on-vercel)
4. [Step 1: Set Up Supabase](#step-1-set-up-supabase)
5. [Step 2: Prepare the Project](#step-2-prepare-the-project)
6. [Step 3: Deploy Backend (Serverless)](#step-3-deploy-backend-serverless)
7. [Step 4: Deploy Frontend](#step-4-deploy-frontend)
8. [Step 5: Configure Environment Variables](#step-5-configure-environment-variables)
9. [Step 6: Set Up Custom Domain](#step-6-set-up-custom-domain)
10. [Step 7: Configure WhatsApp Webhook](#step-7-configure-whatsapp-webhook)
11. [Troubleshooting](#troubleshooting)
12. [Cost Estimation](#cost-estimation)

---

## Overview

This guide covers deploying:
- **Backend API** → Vercel Serverless Functions (Python)
- **Demo Store** → Vercel Static Hosting
- **Admin Dashboard** → Vercel Static Hosting
- **Database** → Supabase (PostgreSQL)
- **Chat Widget** → CDN via Vercel

### Final URLs
After deployment, you'll have:
- `https://your-app.vercel.app` - Demo Store
- `https://your-app.vercel.app/admin` - Admin Dashboard
- `https://your-app.vercel.app/api` - Backend API
- `https://your-app.vercel.app/widget` - Embeddable Chat Widget

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Vercel Account** - [Sign up free](https://vercel.com/signup)
- [ ] **GitHub Account** - For repository hosting
- [ ] **Supabase Account** - [Sign up free](https://supabase.com)
- [ ] **OpenAI API Key** - [Get API key](https://platform.openai.com/api-keys)
- [ ] **Node.js 18+** - For Vercel CLI
- [ ] **Git** - For version control

### Optional (for WhatsApp):
- [ ] **Meta Developer Account** - For WhatsApp Business API
- [ ] **WhatsApp Business Account** - Verified business

---

## Architecture on Vercel

```
┌─────────────────────────────────────────────────────────────┐
│                         Vercel                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │  Demo Store  │  │    Admin     │  │ Chat Widget  │     │
│   │   (Static)   │  │  Dashboard   │  │   (Static)   │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                 │                 │              │
│          └─────────────────┼─────────────────┘              │
│                            ▼                                 │
│   ┌─────────────────────────────────────────────────────┐  │
│   │           Serverless Functions (Python)              │  │
│   │   /api/chat  /api/orders  /api/faqs  /api/admin     │  │
│   └─────────────────────────────────────────────────────┘  │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │        Supabase          │
              │   (PostgreSQL + Vector)  │
              └──────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │       OpenAI API         │
              └──────────────────────────┘
```

---

## Step 1: Set Up Supabase

### 1.1 Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in:
   - **Name**: `ai-chatbot-prod`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
4. Click **"Create new project"**
5. Wait ~2 minutes for provisioning

### 1.2 Run Database Schema

1. In Supabase, go to **SQL Editor**
2. Click **"New Query"**
3. Copy the contents of `database/schema.sql`
4. Click **"Run"**
5. Verify tables were created in **Table Editor**

### 1.3 Enable Vector Extension

If not already enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.4 Get Connection Details

From **Project Settings → API**:
- **Project URL**: `https://xxxxx.supabase.co`
- **anon public key**: `eyJhbGciOiJIUzI1NiIs...`
- **service_role key**: `eyJhbGciOiJIUzI1NiIs...` (keep secret!)

Save these for Step 5.

---

## Step 2: Prepare the Project

### 2.1 Restructure for Vercel

Create the following structure for Vercel deployment:

```
ai-customer-support-chatbot/
├── api/                    # Serverless functions
│   ├── index.py           # Main API router
│   └── requirements.txt   # Python dependencies
├── public/                 # Static files
│   ├── index.html         # Demo store
│   ├── admin/             # Admin dashboard
│   └── widget/            # Chat widget
├── vercel.json            # Vercel configuration
└── package.json           # Node.js config (optional)
```

### 2.2 Create Vercel Configuration

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/admin(.*)",
      "dest": "/public/admin/index.html"
    },
    {
      "src": "/widget/(.*)",
      "dest": "/public/widget/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/public/$1"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.11"
  }
}
```

### 2.3 Create API Entry Point

Create `api/index.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Import your existing app components
import sys
sys.path.insert(0, './backend')

from backend.app.main import app

# Wrap FastAPI with Mangum for serverless
handler = Mangum(app, lifespan="off")
```

### 2.4 Update Requirements

Create `api/requirements.txt`:

```
fastapi==0.104.1
mangum==0.17.0
pydantic==2.5.2
pydantic-settings==2.1.0
openai==1.6.1
supabase==2.3.0
httpx==0.25.2
python-dotenv==1.0.0
python-multipart==0.0.6
```

---

## Step 3: Deploy Backend (Serverless)

### 3.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 3.2 Login to Vercel

```bash
vercel login
```

### 3.3 Initialize Project

```bash
cd ai-customer-support-chatbot
vercel
```

Follow the prompts:
- **Set up and deploy?** → Yes
- **Which scope?** → Select your account
- **Link to existing project?** → No
- **Project name?** → `ai-chatbot` (or your choice)
- **Directory with code?** → `./`
- **Override settings?** → No

### 3.4 Deploy to Production

```bash
vercel --prod
```

Note the deployment URL (e.g., `https://ai-chatbot-xxx.vercel.app`)

---

## Step 4: Deploy Frontend

### 4.1 Prepare Static Files

Copy frontend files to `public/` directory:

```bash
# Create public directory structure
mkdir -p public/admin public/widget

# Copy demo store
cp frontend/demo-store/index.html public/index.html

# Copy admin dashboard
cp frontend/admin-dashboard/* public/admin/

# Copy chat widget
cp frontend/chat-widget/* public/widget/
```

### 4.2 Update API URLs

In `public/widget/widget.js`, update the API URL:

```javascript
const CONFIG = {
    apiUrl: '/api/v1',  // Relative URL for same-domain
    // apiUrl: 'https://your-app.vercel.app/api/v1', // Or full URL
    sessionKey: 'ai_chat_session_id',
    maxMessageLength: 1000,
    typingDelay: 1500
};
```

In `public/admin/dashboard.js`:

```javascript
const CONFIG = {
    apiUrl: '/api/v1',
    refreshInterval: 30000
};
```

### 4.3 Redeploy

```bash
vercel --prod
```

---

## Step 5: Configure Environment Variables

### 5.1 Via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings → Environment Variables**
4. Add the following variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-...` | Production, Preview |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Production, Preview |
| `SUPABASE_KEY` | `eyJ...` (anon key) | Production, Preview |
| `SUPABASE_SERVICE_KEY` | `eyJ...` (service key) | Production |
| `WHATSAPP_TOKEN` | Your token | Production |
| `WHATSAPP_PHONE_ID` | Your phone ID | Production |
| `WHATSAPP_VERIFY_TOKEN` | Custom string | Production |
| `ENVIRONMENT` | `production` | Production |
| `DEBUG` | `false` | Production |

### 5.2 Via CLI

```bash
vercel env add OPENAI_API_KEY
# Enter value when prompted

vercel env add SUPABASE_URL
# Repeat for all variables
```

### 5.3 Redeploy with Environment Variables

```bash
vercel --prod
```

---

## Step 6: Set Up Custom Domain

### 6.1 Add Domain in Vercel

1. Go to **Project Settings → Domains**
2. Click **"Add"**
3. Enter your domain (e.g., `support.yourstore.com`)
4. Follow DNS configuration instructions

### 6.2 Configure DNS

Add these records at your DNS provider:

**For apex domain (yourstore.com):**
```
Type: A
Name: @
Value: 76.76.19.19
```

**For subdomain (support.yourstore.com):**
```
Type: CNAME
Name: support
Value: cname.vercel-dns.com
```

### 6.3 Enable HTTPS

Vercel automatically provisions SSL certificates. Wait a few minutes after DNS propagation.

---

## Step 7: Configure WhatsApp Webhook

### 7.1 Set Up Webhook URL

Your webhook URL will be:
```
https://your-domain.vercel.app/api/v1/whatsapp/webhook
```

### 7.2 Configure in Meta Developer Console

1. Go to [Meta Developer Console](https://developers.facebook.com)
2. Select your app
3. Go to **WhatsApp → Configuration**
4. Under **Webhook**:
   - **Callback URL**: `https://your-domain.vercel.app/api/v1/whatsapp/webhook`
   - **Verify Token**: Same as `WHATSAPP_VERIFY_TOKEN` env variable
5. Click **"Verify and Save"**
6. Subscribe to: `messages`, `message_status`

### 7.3 Test Webhook

Send a test message to your WhatsApp number and check Vercel logs:

```bash
vercel logs --follow
```

---

## Troubleshooting

### Common Issues

#### 1. Function Timeout
**Error**: `FUNCTION_INVOCATION_TIMEOUT`

**Solution**: Vercel Hobby plan has 10s timeout. Upgrade to Pro for 60s, or optimize:
```json
// vercel.json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  }
}
```

#### 2. Module Not Found
**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**: Check `api/requirements.txt` includes all dependencies.

#### 3. Cold Start Latency
**Issue**: First request takes 5-10 seconds

**Solution**: 
- Keep functions warm with cron pings
- Use Vercel Pro for faster cold starts
- Optimize imports

#### 4. CORS Errors
**Error**: `Access-Control-Allow-Origin` issues

**Solution**: Ensure CORS middleware is configured:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific domains
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5. Environment Variables Not Loading
**Solution**: 
- Redeploy after adding env vars
- Check variable names match exactly
- Verify correct environment (Production/Preview)

### Viewing Logs

```bash
# Real-time logs
vercel logs --follow

# Function-specific logs
vercel logs api/index.py
```

### Local Testing with Vercel

```bash
# Run locally with Vercel environment
vercel dev
```

---

## Cost Estimation

### Vercel Pricing

| Plan | Cost | Serverless Execution | Bandwidth |
|------|------|---------------------|-----------|
| Hobby | Free | 100 GB-hours/month | 100 GB |
| Pro | $20/month | 1000 GB-hours/month | 1 TB |
| Enterprise | Custom | Unlimited | Unlimited |

### Supabase Pricing

| Plan | Cost | Database | Storage |
|------|------|----------|---------|
| Free | $0 | 500 MB | 1 GB |
| Pro | $25/month | 8 GB | 100 GB |
| Team | $599/month | Unlimited | Unlimited |

### OpenAI Costs (Estimated)

| Usage | GPT-4 Turbo Cost |
|-------|------------------|
| 1000 chats/month | ~$5-15 |
| 10,000 chats/month | ~$50-150 |
| 100,000 chats/month | ~$500-1500 |

### Total Estimated Monthly Cost

| Scale | Vercel | Supabase | OpenAI | Total |
|-------|--------|----------|--------|-------|
| Hobby (1K chats) | $0 | $0 | $10 | ~$10 |
| Small (10K chats) | $20 | $25 | $100 | ~$145 |
| Medium (50K chats) | $20 | $25 | $500 | ~$545 |

---

## Production Checklist

Before going live, ensure:

- [ ] All environment variables are set
- [ ] Database schema is deployed
- [ ] CORS is configured correctly
- [ ] Rate limiting is enabled
- [ ] Error tracking (Sentry) is set up
- [ ] Custom domain is configured
- [ ] SSL certificate is active
- [ ] WhatsApp webhook is verified
- [ ] Bot responses tested thoroughly
- [ ] Admin dashboard accessible
- [ ] Backup strategy in place

---

## Next Steps

1. **Monitor Performance**: Use Vercel Analytics
2. **Set Up Alerts**: Configure Vercel notifications
3. **Add Error Tracking**: Integrate Sentry
4. **Scale as Needed**: Upgrade plans based on usage
5. **Iterate**: Improve bot responses based on chat logs

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **OpenAI Docs**: https://platform.openai.com/docs

---

*Last updated: December 2024*
