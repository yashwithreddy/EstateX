# EstateX — Fractional Real Estate Investment Platform

Production-grade full-stack platform enabling fractional ownership of verified Indian real estate.  
Built with **FastAPI + SQLite/PostgreSQL**, **React 18 + Tailwind CSS**, **SHAP ML explainability**, and an **Ethereum smart contract** (mock mode by default).

---

## Quick Start (Local Dev)

### 1. Backend

```bash
cd backend

# Create virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialise database schema
python scripts/init_db.py

# Seed 22 Indian properties + 3 demo users
python scripts/seed_data.py

# Start API server
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
```

Opens at **https://localhost:5173** — on first load Chrome will show a certificate warning. Click **Advanced → Proceed to localhost** (once only).

---

## Demo Credentials

| Role           | Email               | Password     |
| -------------- | ------------------- | ------------ |
| Admin          | admin@estatex.in    | Admin@123    |
| Property Owner | owner@estatex.in    | Owner@123    |
| Investor       | investor@estatex.in | Investor@123 |

All three credential sets are also shown as one-click buttons on the login page.

---

## Key Features

| Feature                   | Details                                                                  |
| ------------------------- | ------------------------------------------------------------------------ |
| **Role-based auth**       | Investor / Property Owner / Admin with JWT, bcrypt                       |
| **20+ Indian Properties** | Hyderabad, Mumbai, Bangalore, Pune, Chennai, Delhi and 16 more           |
| **Explainable AI**        | ROI + Risk predictions with SHAP feature importance bars                 |
| **Exit Simulation**       | Partial exit calculator with Indian LTCG tax (20%) breakdown             |
| **Admin Panel**           | Approve listings, verify documents, manage users                         |
| **Owner Dashboard**       | Upload property + 4 documents, track listing status                      |
| **Blockchain Tracking**   | Ethereum mock (set `BLOCKCHAIN_ENABLED=true` + deploy contract for live) |
| **INR Currency**          | All values formatted in Indian Rupees (₹) with locale formatting         |

---

## Environment Variables (`backend/.env`)

```
DATABASE_URL=sqlite:///./estatex.db
JWT_SECRET_KEY=supersecretkeyForSampleRun123
JWT_EXPIRE_MINUTES=60
BLOCKCHAIN_ENABLED=false
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For PostgreSQL replace `DATABASE_URL` with:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/estatex
```

---

## Architecture Overview

## Monorepo Structure

```
realestate/
├── backend/
│   ├── app/
│   │   ├── blockchain/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── ml/
│   │   ├── artifacts/
│   │   └── train_models.py
│   ├── scripts/
│   │   ├── init_db.py
│   │   └── seed_data.py
│   ├── .env.example
│   └── requirements.txt
├── blockchain/
│   ├── contracts/EstateXFractional.sol
│   ├── scripts/deploy.js
│   ├── scripts/estatexClient.js
│   ├── hardhat.config.js
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── context/
    │   ├── layouts/
    │   ├── pages/
    │   ├── routes/
    │   └── utils/
    ├── .env.example
    └── package.json
```

## Core Features Implemented

- JWT auth with roles (`investor`, `owner`, `admin`) and protected routes.
- Property listing workflow requires title + ownership PDFs.
- SHA-256 document hash generation and storage.
- Admin document verification and listing approval gates.
- No listing investment before verification.
- Primary fractional share buying with oversell protection.
- Partial exit/liquidity via share listings and peer buy.
- On-chain fractional ownership events + share tracking.
- ROI regression model + confidence interval.
- Risk classification model with probability.
- SHAP explainability endpoint + frontend visualization.
- Investor dashboard and admin dashboard.

## Backend Setup (FastAPI + PostgreSQL)

1. Create DB and env:

```bash
createdb estatex
cd backend
cp .env.example .env
```

2. Install dependencies and run model training:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ml/train_models.py
```

3. Initialize DB + seed data:

```bash
python -m scripts.init_db
python -m scripts.seed_data
```

4. Run API:

```bash
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup (React + Tailwind + Chart.js + Axios + Ethers)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Blockchain Setup (Hardhat + Solidity + Ethers)

```bash
cd blockchain
cp .env.example .env
npm install
npm run compile
npm run node
```

In another terminal:

```bash
cd blockchain
npm run deploy:local
```

Copy deployed contract address to:

- `frontend/.env` -> `VITE_CONTRACT_ADDRESS`
- `backend/.env` -> `CHAIN_CONTRACT_ADDRESS`

Set `BLOCKCHAIN_ENABLED=true` in backend to enable server-side chain calls.

## API Endpoints

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

### Properties

- `GET /api/v1/properties`
- `GET /api/v1/properties/{id}`
- `POST /api/v1/properties` (owner only, multipart + two PDFs)

### Investments / Liquidity

- `POST /api/v1/investments/buy`
- `POST /api/v1/investments/list`
- `GET /api/v1/investments/listings`
- `POST /api/v1/investments/trade`

### Admin

- `GET /api/v1/admin/documents/pending`
- `PATCH /api/v1/admin/documents/{document_id}/verify`
- `PATCH /api/v1/admin/properties/{property_id}/approve`

### AI/ML

- `POST /api/v1/ai/roi`
- `POST /api/v1/ai/risk`
- `POST /api/v1/ai/explain`

### Dashboard

- `GET /api/v1/dashboard/investor`
- `GET /api/v1/dashboard/admin`

## Seed Accounts

- Admin: `admin@estatex.com` / `Admin@123`
- Owner: `owner@estatex.com` / `Owner@123`
- Investor: `investor@estatex.com` / `Investor@123`

## Business Rule Enforcement

- Property cannot go live without verified title + ownership documents.
- API blocks investment for non-approved/non-verified listings.
- API blocks buying more shares than available.
- Liquidity listing blocked if seller has insufficient shares.
- Role-based route/API access is enforced server-side and client-side.
