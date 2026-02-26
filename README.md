# 🏥 AI Smart Health Navigator
### A Complete Healthcare Web Platform — Hackathon Edition

---

## 📋 PROJECT OVERVIEW

AI Smart Health Navigator is a full-stack healthcare assistance web application. It originally worked in guest mode with no login; recent updates add optional **login/signup functionality** so users can create accounts and retain preferences across devices. The system still supports guest mode using browser LocalStorage for personalized data.

---

## 🏗️ ARCHITECTURE

```
healthapp/
├── app.py                    ← Flask Backend (all routes + DB + AI)
├── requirements.txt          ← Python dependencies
├── instance/
│   └── health.db             ← SQLite database (auto-created)
├── templates/
│   └── index.html            ← Single Page Application (SPA)
└── static/
    ├── css/
    │   └── style.css         ← Complete UI styles (organic-medical theme)
    └── js/
        └── app.js            ← Frontend logic (fetch APIs, state, UI)
```

### Tech Stack
| Layer     | Technology |
|-----------|------------|
| Backend   | Python Flask 3.x |
| Database  | SQLite (via Python sqlite3) |
| AI Engine | Anthropic Claude API (with mock fallback) |
| Frontend  | Vanilla HTML + CSS + JavaScript (SPA) |
| Fonts     | Google Fonts (Outfit + DM Serif Display) |
| Icons     | Font Awesome 6 |

---

## 🚀 INSTALLATION & RUN

### Step 1 — Install Python dependencies
```bash
cd healthapp
pip install -r requirements.txt
```

### Step 2 — (Optional) Set Anthropic API Key
```bash
# macOS/Linux
export ANTHROPIC_API_KEY=your_key_here

# Windows CMD
set ANTHROPIC_API_KEY=your_key_here
```

> **Note:** If no API key is set, the app uses a comprehensive mock AI response database — fully functional for demos.

### Step 3 — Run the app
```bash
python app.py
```

### Step 4 — Open in browser
```
http://localhost:5000
```

The SQLite database is **auto-created and seeded** on first run. No setup needed!

---

## 🌟 FEATURES

### ✅ User Accounts (Login / Signup)
- Create an account with email, password and name
- Login persists session via Flask server-side session cookie
- Server tracks searches and can associate tokens with user

### ✅ Guest Mode — No Login Required
- Session ID auto-generated in browser
- Search history saved to localStorage
- Active token persists across browser refreshes

### 🔬 AI Disease Navigator
- Enter any disease name or symptom
- AI provides: explanation, do's & don'ts, diet tips, prevention
- Medical disclaimer always shown
- Connects to real Claude AI if API key provided

### 🏥 Hospital Finder
- 12 hospitals across Hyderabad, Vijayawada, Visakhapatnam, Bengaluru, Chennai, Tirupati
- Filter by city, specialization, search term
- One-click Aarogyasri filter
- Rating-sorted results

### 🏛️ Hospital Details
- Specialists with fees and availability
- Departments grid
- Government schemes with eligibility + application steps
- Filter schemes by: Women / Men / Child / Pregnant
- Direct call and token booking

### 🎫 Smart Queue Token System
- Book token from hospital list or detail page
- Real-time queue simulation (updates every 15 seconds via API)
- Visual progress bar and alert notifications
- Token persists across page refreshes
- Smart alerts: 3 ahead (warning), 0 ahead (success bell)

### 🏛️ Government Schemes
- Aarogyasri (AP/Telangana BPL scheme)
- Ayushman Bharat PM-JAY
- PM Matru Vandana (Pregnant women)
- Balasevika (Children 0-6)
- Women Welfare Scheme
- Arogyam (Men preventive health)
- Filter by beneficiary category

### 🌐 Multilingual Support
- English, Telugu (తెలుగు), Hindi (हिंदी)
- Switches UI labels dynamically

### 🚨 Emergency Panel
- Ambulance: 108
- Health Helpline: 104
- Women Safety: 181
- Child Helpline: 1098

---

## 🔌 API ENDPOINTS

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve SPA |
| GET | `/api/hospitals` | List hospitals (filters: city, search, spec, aarogyasri) |
| GET | `/api/hospitals/<id>` | Full hospital details |
| GET | `/api/cities` | List all cities |
| GET | `/api/schemes` | All distinct government schemes |
| POST | `/api/ai/disease` | AI disease information |
| POST | `/api/tokens` | Book queue token |
| GET | `/api/tokens/<num>/status` | Live queue status |
| POST | `/api/ai/recommend-hospitals` | AI hospital recommendation |

---

## 🗄️ DATABASE SCHEMA

```sql
hospitals        — id, name, city, address, phone, rating, specialization, icon, beds, emergency, aarogyasri, ayushman
specialists      — id, hospital_id, name, department, qualification, availability, fee
departments      — id, hospital_id, name, icon
schemes          — id, hospital_id, scheme_name, category, is_available, benefit, eligibility, steps
tokens           — id, token_number, hospital_id, hospital_name, session_id, status, people_ahead, estimated_wait, booked_at
search_history   — id, session_id, query, searched_at
```

---

## 🎨 DESIGN SYSTEM

| Element | Value |
|---------|-------|
| Primary | Jade Teal `#0d9488` |
| Background | Soft mist `#f4f8fa` |
| Display Font | DM Serif Display (headings) |
| Body Font | Outfit (UI text) |
| Border Radius | 16px cards, 22px panels, 28px hero |
| Motion | CSS animations, 0.25-0.35s easing |

---

## 📱 SCREENSHOTS — Page Tour

1. **Home** — Hero banner, quick action grid, health tips, emergency numbers
2. **Disease Search** — AI-powered query, do's/don'ts, diet & lifestyle
3. **Hospital List** — Filtered cards with Aarogyasri badges
4. **Hospital Detail** — 3-tab: Specialists / Departments / Schemes
5. **Smart Token** — Live queue progress, alert notifications
6. **Schemes** — Category-filtered government schemes

---

## 💡 HACKATHON HIGHLIGHTS

- ⚡ Zero-friction: opens instantly, no registration
- 🤖 Real AI integration (Claude API) with intelligent fallback
- 📱 Mobile-first, professional app feel
- 🏛️ Real government scheme data (Aarogyasri, Ayushman Bharat, etc.)
- 🔄 Simulated real-time queue (API-driven, polls every 15s)
- 🌐 3-language support (English, Telugu, Hindi)
- 🎨 Production-grade UI with custom typography and animations

---

*Built for Hackathon 2025 — AI Smart Health Navigator*
