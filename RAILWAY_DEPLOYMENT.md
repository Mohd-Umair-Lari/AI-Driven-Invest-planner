# Railway Deployment Guide for FinPass AI

## 🚀 Overview

This guide explains how to deploy the FinPass AI backend to **Railway** with proper environment variable management.

---

## 📌 Key Concepts

### Local Development (`backend/.env`)
- File you create locally on your machine
- Contains real credentials for development
- **NEVER committed to git** (it's in .gitignore)
- Python-dotenv automatically loads it when Flask starts

### Railway Dashboard (Production)
- Web platform for setting environment variables
- All variables are encrypted and secure
- No .env file needed on Railway
- Railway injects variables at runtime into the container
- Can view/edit anytime in Railway dashboard

---

## 🔒 Environment Variable Strategy

```
YOUR MACHINE (Local):
  backend/.env (created by you)
    ↓ (never uploaded)
  Flask app reads via os.getenv()

RAILWAY (Production):
  Railway Dashboard Variables
    ↓ (injected at runtime)
  Flask app reads via os.getenv()

CODE (Same in both):
  MONGO_URI = os.getenv("MONGO_URI")
  GROQ_API_KEY = os.getenv("GROQ_API_KEY")
```

**The code is identical!** Only the source of environment variables differs.

---

## 📋 Step-by-Step Deployment

### Step 1: Prepare Local Environment

Create `backend/.env` file locally:

```bash
cd backend
cp .env.example .env
# Edit .env with your real credentials:
# MONGO_URI=mongodb+srv://YOUR_USER:YOUR_PASS@...
# GROQ_API_KEY=gsk_your_actual_key...
```

**Verify it works locally:**
```bash
python main.py
# Should start Flask server without "MONGO_URI environment variable is not set" error
```

### Step 2: Create Railway Project

1. Go to https://railway.app/
2. Sign up / Log in
3. Click **"New Project"**
4. Select **"GitHub"** (if you haven't connected, authorize it)
5. Select your **AI-Financial Advisor** repository
6. Railway will auto-detect `Procfile` or `main.py`

### Step 3: Add Environment Variables to Railway

1. In Railway Dashboard, go to your project
2. Click on the **backend** service
3. Go to **Variables** tab
4. Click **"New Variable"** and add:

| Key | Value | Example |
|-----|-------|---------|
| MONGO_URI | Your MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0` |
| GROQ_API_KEY | Your Groq API key | `gsk_xxxxxxxxxxxxxxxxxxxx` |
| DB_NAME | Database name | `mockDB` |
| COLLECTION_NAME | Collection name | `userGoals` |
| FLASK_ENV | Environment type | `production` |
| PORT | Server port | `8000` |

**Leave PORT empty** - Railway auto-assigns it!

### Step 4: Add Start Command

Railway needs to know how to start your app:

1. In Railway Dashboard, go to **Variables**
2. Scroll down to **"Domains"** section
3. Under **"Start Command"**, set:
```
gunicorn main:app --bind 0.0.0.0:$PORT --workers 2
```

Or create `Procfile` in root directory:
```
web: cd backend && gunicorn main:app --bind 0.0.0.0:$PORT --workers 2
```

### Step 5: Verify requirements.txt

Make sure `backend/requirements.txt` includes:
```
Flask==3.0.3
gunicorn==21.2.0
flask-cors==4.0.1
pymongo==4.6.3
certifi==2024.7.4
python-dotenv==1.0.1
werkzeug==3.0.0
groq
```

✅ **numpy should be removed** (not used)

### Step 6: Deploy

1. Push your code to main branch:
```bash
git add -A
git commit -m "Prepare for Railway deployment"
git push origin main
```

2. Railway automatically detects the push and starts deployment
3. Watch the **Deployment** tab for build progress
4. Once green ✅, your backend is live!

---

## 🌐 Frontend CORS Configuration

Frontend (Vercel) needs to know your Railway backend URL:

In `frontend/js/api.js`:
```javascript
const API_BASE = 'https://your-railway-project.railway.app';
// Railway gives you this URL in the Domains section
```

---

## 🧪 Testing Deployment

### Test Endpoint
```bash
curl https://your-railway-project.railway.app/api/test-connection
```

Should return:
```json
{"status": "ok", "message": "Backend is running"}
```

### Test Login
```bash
curl -X POST https://your-railway-project.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"lol@example.com","password":"12345678"}'
```

---

## 🔐 Security Best Practices

### ✅ CORRECT:
- ✅ Create `.env` locally with real credentials
- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Store credentials in Railway Dashboard
- ✅ Use `python-dotenv` to load `.env` locally
- ✅ Code uses `os.getenv()` for all environment variables

### ❌ WRONG:
- ❌ Commit `.env` file to git
- ❌ Hardcode credentials in code
- ❌ Share API keys in messages/chat
- ❌ Use plain HTTP (always use HTTPS)
- ❌ Store credentials in comments

---

## 📊 Comparison: Local vs Railway

| Aspect | Local Development | Railway Production |
|--------|------------------|-------------------|
| `.env` file? | ✅ Yes (in .gitignore) | ❌ No (use Dashboard) |
| Git tracking | ❌ Never committed | - |
| Credentials visible? | 👤 Only on your machine | 🔒 Encrypted on Railway |
| Update credentials? | Edit local .env + restart | Change in Dashboard |
| Python-dotenv? | ✅ Required | ✅ Works with os.getenv() |
| How code reads vars | `os.getenv("KEY")` | `os.getenv("KEY")` |
| Flask startup | Reads from `.env` file | Reads from environment |

---

## 🛠️ Troubleshooting

### Problem: "MONGO_URI environment variable is not set"
**Solution:** Add `MONGO_URI` in Railway Dashboard Variables

### Problem: Backend works locally but not on Railway
**Possible causes:**
1. Missing environment variables (check Railway Dashboard)
2. Network/IP whitelist on MongoDB (add Railway IP to MongoDB Atlas)
3. Wrong start command (should use gunicorn)

### Problem: Logs show environment error
**Solution:**
1. Go to Railway Dashboard
2. Click your service
3. Look at **Logs** tab for detailed error messages
4. Check **Variables** tab to ensure all are set

### Problem: Can't connect to MongoDB from Railway
**Solution:** In MongoDB Atlas:
1. Go to **Network Access**
2. Add `0.0.0.0/0` (allow all IPs) - ⚠️ For testing only
3. Or better: Whitelist Railway's IP range (check Railway docs)

---

## 📝 File Checklist Before Deployment

- ✅ `backend/.env.example` - Template created
- ✅ `backend/.gitignore` - Excludes `.env`
- ✅ `backend/main.py` - Loads `.env` correctly
- ✅ `backend/requirements.txt` - All dependencies listed
- ✅ `Procfile` (or Railway config) - Start command specified
- ✅ Frontend `api.js` - Backend URL updated
- ✅ MongoDB Atlas - TLS enabled, IP whitelisted
- ✅ Groq API key - Valid and not expired

---

## 🎯 Next Steps

1. **Local testing:** Create `.env` and verify Flask starts
2. **Push to git:** `git push origin main`
3. **Create Railway project:** Connect GitHub repo
4. **Set variables:** Add all in Railway Dashboard
5. **Deploy:** Railway auto-deploys on push
6. **Test:** Call `/api/test-connection` endpoint
7. **Update frontend:** Set correct Railway backend URL

---

## 📚 Useful Links

- [Railway Docs](https://docs.railway.app/)
- [Python Deployment on Railway](https://docs.railway.app/deploy/python)
- [Environment Variables Guide](https://docs.railway.app/deploy/environment-variables)
- [MongoDB TLS Connection](https://docs.mongodb.com/manual/reference/connection-string/#tls-tlsinsecure)
