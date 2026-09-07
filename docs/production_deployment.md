# MindGuard — Production Deployment & Cloud Architecture Guide

This guide details how to take **MindGuard** from local prototype to a secure, scalable, and compliant public production environment.

---

## 1. High-Level Production Architecture

```mermaid
graph TD
    Client["Victim / Officer Device<br/>(HTTPS / Browser / Mobile)"]

    subgraph CDN ["Edge & CDN Layer"]
        CF["Cloudflare / AWS CloudFront<br/>(DDoS Protection, SSL/TLS)"]
        FE_HOST["Frontend Hosting<br/>(Vercel / Cloudflare Pages / Nginx)"]
    end

    subgraph CLOUD ["Application Cloud Tier (AWS / DigitalOcean / Render)"]
        NGINX["Nginx Gateway / Load Balancer<br/>(:443 HTTPS)"]
        BE["FastAPI Core Backend (:8000)<br/>Gunicorn / Multi-worker Uvicorn"]
        ML["ML Intelligence Pipeline (:8001)<br/>PyTorch + HuggingFace + Whisper"]
    end

    subgraph DATA ["Managed Storage Tier"]
        DB[("Managed PostgreSQL 16<br/>(AWS RDS / Supabase / Neon)<br/>Daily Backups · Encrypted at Rest")]
        OBJ[("S3 / Cloud Storage<br/>(Audio recordings & Voice Check-ins)")]
    end

    subgraph TEL ["Telephony & SMS Gateway"]
        SMS["SMS Gateway (Exotel / CDAC / Twilio)<br/>Two-Way SMS Check-ins"]
        IVRS["Voice IVRS Provider (Exotel)<br/>Outbound Automated Calls"]
    end

    Client --> CF
    CF --> FE_HOST
    CF --> NGINX
    NGINX --> BE
    NGINX --> ML
    BE --> DB
    ML --> OBJ
    BE --> SMS
    BE --> IVRS
```

---

## 2. Database Migration: SQLite to Managed PostgreSQL

MindGuard uses **SQLAlchemy ORM** with `psycopg2-binary`, so zero code changes are needed in the models or queries.

### Recommended Managed Database Providers:
| Provider | Best For | Free / Starting Tier | Why Choose It |
|---|---|---|---|
| **Neon.tech** | Fast serverless PostgreSQL | Free 0.5 GB, branches | Easiest setup, auto-scaling |
| **Supabase** | Managed PostgreSQL + Auth | Free tier (500 MB) | Built-in row-level security & dashboard |
| **AWS RDS (PostgreSQL)** | Government & Enterprise | Free tier 1 yr (db.t4g.micro) | DPDP Act compliant, Multi-AZ backups |
| **DigitalOcean Managed DB** | Simple fixed-cost VPS | $15/month | Simple UI, automated daily backups |

### Setup Steps:
1. Create a PostgreSQL 16 database instance on your chosen provider.
2. Retrieve your connection string, formatted as:
   ```text
   postgresql://mindguard_admin:YourStrongPassword@db.example.neon.tech:5432/mindguard_prod?sslmode=require
   ```
3. Set this as the `DATABASE_URL` environment variable for the backend.
4. On first startup, `backend/main.py` automatically initializes all tables (`victims`, `check_ins`, `alerts`, `users`, `audit_logs`).

---

## 3. Backend & ML Pipeline Hosting Options

### Option A: 1-Click Container Deployment on a Cloud VPS (Recommended for SIH Pilot)
Deploy on an **AWS EC2 (t3.xlarge or g4dn.xlarge)**, **DigitalOcean Droplet ($24/mo)**, or **Hetzner Cloud**:

```bash
# 1. Clone the repository on your server
git clone https://github.com/your-org/mindguard.git
cd mindguard

# 2. Copy production environment variables
cp .env.production.example .env
nano .env   # Fill in your DB credentials and strong JWT secret

# 3. Launch all services with Docker Compose
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify running containers
docker compose -f docker-compose.prod.yml ps
```

### Option B: Serverless & App Platform Hosting
If you prefer not to manage Linux servers:
- **FastAPI Backend**: Deploy on **Render.com** (Web Service) or **Railway.app** connecting directly to your managed PostgreSQL.
- **ML Pipeline**: Deploy on **Modal.com**, **RunPod**, or **Render** (assign at least 2 GB RAM for sentiment/emotion models and Whisper-base).
- **Frontend**: Deploy on **Vercel** or **Cloudflare Pages** (Build command: `npm run build`, Output directory: `dist`).

---

## 4. Telephony & SMS API Integration (Indian Context)

For real-world victim check-ins in India, integrate with telecom aggregators approved for government/NGO outreach:

### Recommended Gateways:
1. **Exotel (India's leading telecom API)**:
   - Supports 2-way SMS and outbound automated IVRS calls in Indian regional languages.
   - Outbound IVRS trigger:
     ```python
     import requests

     def trigger_ivrs_checkin(victim_phone: str, case_id: str):
         requests.post(
             "https://api.exotel.com/v1/Accounts/{SID}/Calls/connect",
             auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN),
             data={
                 "From": EXOTEL_CALLER_ID,
                 "To": victim_phone,
                 "Url": f"https://api.mindguard.nic.in/telephony/ivrs-flow?case_id={case_id}",
             }
         )
     ```
2. **CDAC / National Informatics Centre (NIC) SMS Gateway**:
   - For official government deployments under Indian State/Central ministries.
3. **Twilio**:
   - Ideal for international demonstrations or global pilots.

---

## 5. Security, DPDP Act 2023 & HIPAA Compliance

When handling victim distress and atrocity case data:

1. **Digital Personal Data Protection (DPDP) Act 2023 Compliance**:
   - **Data Minimization**: Store only anonymized victim IDs (`VIC-YYYY-XXXXX`) in the primary analytics engine. Keep physical identity/names in a separate, isolated, encrypted vault.
   - **Audit Logs**: The system includes [`backend/models/audit_log.py`](file:///c:/Users/Ankit007/OneDrive/Documents/SIH%20project%201/backend/models/audit_log.py) recording every alert access, recommendation evaluation, and login attempt.
2. **Secrets & Keys**:
   - Never commit `.env` or JWT secrets to Git.
   - Generate production JWT secrets using:
     ```bash
     openssl rand -hex 32
     ```
3. **SSL/TLS Encryption**:
   - Enforce HTTPS across all endpoints using Cloudflare or Let's Encrypt Certbot:
     ```bash
     sudo apt install certbot python3-certbot-nginx
     sudo certbot --nginx -d mindguard.nic.in -d api.mindguard.nic.in
     ```
4. **Network Isolation**:
   - Keep PostgreSQL and the internal ML Pipeline on a private Docker bridge network (`backend-network`), exposing only port 443 (HTTPS) to the outside world through Nginx.
