"""
AI Smart Health Navigator - Flask Backend
==========================================
Guest-mode platform: No login required.
Uses SQLite for hospitals/schemes data.
AI powered by Anthropic Claude API.
"""

import os, json, sqlite3, random, string, time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, session
from werkzeug.security import generate_password_hash, check_password_hash

# ── App Setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
# secret key used for session management (login)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_please_change')
app.config['DATABASE'] = os.path.join(app.instance_path, 'health.db')
os.makedirs(app.instance_path, exist_ok=True)

SUPPORTED_CITIES = ["Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Delhi"]

# ── DB Helpers ─────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # ── TABLES ──────────────────────────────────────────────────────────────
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        rating REAL DEFAULT 4.0,
        specialization TEXT,
        icon TEXT DEFAULT '🏥',
        beds INTEGER DEFAULT 100,
        emergency INTEGER DEFAULT 0,
        aarogyasri INTEGER DEFAULT 0,
        ayushman INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS specialists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id INTEGER,
        name TEXT,
        department TEXT,
        qualification TEXT,
        availability TEXT,
        fee INTEGER DEFAULT 500,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
    );

    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id INTEGER,
        name TEXT,
        icon TEXT,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
    );

    CREATE TABLE IF NOT EXISTS schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id INTEGER,
        scheme_name TEXT,
        category TEXT DEFAULT 'all',
        is_available INTEGER DEFAULT 1,
        benefit TEXT,
        eligibility TEXT,
        steps TEXT,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
    );

    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_number TEXT UNIQUE,
        hospital_id INTEGER,
        hospital_name TEXT,
        session_id TEXT,
        status TEXT DEFAULT 'waiting',
        people_ahead INTEGER DEFAULT 5,
        estimated_wait INTEGER DEFAULT 10,
        booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
    );

    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        query TEXT,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Backward-compatible auth migration (existing DBs may only have email/password fields)
    user_cols = [r[1] for r in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if 'mobile' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN mobile TEXT")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile)")

    # ── SEED DATA ────────────────────────────────────────────────────────────
    hospitals_count = cursor.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    if hospitals_count == 0:
        hospitals = [
            (1,"NIMS Hospital","Hyderabad","Punjagutta, Hyderabad","040-23489000",4.7,"Neurology","🧠",800,1,1,1),
            (2,"Apollo Hospitals","Hyderabad","Jubilee Hills, Hyderabad","040-23607777",4.8,"Cardiology","❤️",700,1,1,1),
            (3,"Yashoda Hospital","Hyderabad","Somajiguda, Hyderabad","040-45678900",4.6,"Oncology","🧬",500,1,0,1),
            (4,"KIMS Hospital","Hyderabad","Minister Road, Secunderabad","040-44885000",4.5,"Multi-speciality","🏥",600,1,1,1),
            (5,"Vijaya Hospital","Vijayawada","Eluru Road, Vijayawada","0866-2434455",4.4,"Orthopedic","🦴",300,0,1,1),
            (6,"Ramdev Rao Hospital","Vijayawada","Governorpet, Vijayawada","0866-2571000",4.2,"General Medicine","🩺",150,0,1,0),
            (7,"KGH Hospital","Visakhapatnam","CBD, Visakhapatnam","0891-2564891",4.1,"Multi-speciality","👑",1000,1,1,1),
            (8,"Visakha Hospital","Visakhapatnam","MVP Colony, Visakhapatnam","0891-2711000",4.3,"Multi-speciality","🏛️",400,1,1,1),
            (9,"Medanta Hospital","Bengaluru","Whitefield, Bengaluru","080-67999999",4.9,"Cardiology","💙",800,1,0,1),
            (10,"MGM Cancer Hospital","Chennai","Perambur, Chennai","044-26611686",4.5,"Oncology","🎗️",400,1,0,1),
            (11,"TTD Hospital","Tirupati","Tirupati, Andhra Pradesh","0877-2254000",4.3,"Multi-speciality","🕌",300,0,1,1),
            (12,"Care Hospitals","Hyderabad","Banjara Hills, Hyderabad","040-30419000",4.6,"Cardiology","💊",500,1,1,1),
        ]
        cursor.executemany(
            "INSERT INTO hospitals (id,name,city,address,phone,rating,specialization,icon,beds,emergency,aarogyasri,ayushman) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            hospitals
        )

        specialists = [
            (1,1,"Dr. Ramesh Kumar","Neurology","MD, DM Neurology","Mon-Sat 9AM-1PM",800),
            (2,1,"Dr. Priya Singh","Neurosurgery","MS, MCh Neurosurgery","Mon-Fri 2PM-5PM",1000),
            (3,2,"Dr. Sudhir Sharma","Interventional Cardiology","DM Cardiology, FACC","Mon-Fri 8AM-12PM",1200),
            (4,2,"Dr. Kavitha Rao","Oncology","MD, DM Oncology","Mon-Sat 9AM-1PM",900),
            (5,3,"Dr. Rajiv Menon","Medical Oncology","DM Oncology","Mon-Fri 9AM-12PM",1000),
            (6,4,"Dr. Deepak Rao","Cardiology","DM Cardiology","Mon-Sat 8AM-12PM",900),
            (7,4,"Dr. Anita Sharma","Gynecology","MS Gynec, DNB","Mon-Fri 9AM-1PM",700),
            (8,5,"Dr. Prasad Naidu","Orthopedics","MS Ortho, FRCS","Mon-Sat 9AM-2PM",800),
            (9,7,"Dr. Krishna Murthy","Orthopedics","MS Ortho","Mon-Sat 8AM-1PM",600),
            (10,9,"Dr. Suresh Krishnan","Cardiology","DM Cardiology, PhD","Mon-Fri 9AM-12PM",1500),
            (11,12,"Dr. Meena Iyer","Neurology","DM Neurology","Mon-Sat 10AM-1PM",900),
        ]
        cursor.executemany(
            "INSERT INTO specialists (id,hospital_id,name,department,qualification,availability,fee) VALUES (?,?,?,?,?,?,?)",
            specialists
        )

        departments = [
            (1,1,"Neurology","🧠"),(2,1,"Cardiology","❤️"),(3,1,"Emergency","🚨"),
            (4,2,"Cardiology","❤️"),(5,2,"Oncology","🧬"),(6,2,"Orthopedics","🦴"),(7,2,"Pediatrics","🧒"),(8,2,"Gynecology","👩‍⚕️"),
            (9,3,"Oncology","🧬"),(10,3,"Radiation","☢️"),(11,3,"Pathology","🔬"),
            (12,4,"Cardiology","❤️"),(13,4,"Gynecology","👩‍⚕️"),(14,4,"Pediatrics","🧒"),(15,4,"Emergency","🚨"),
            (16,5,"Orthopedics","🦴"),(17,5,"General Medicine","🩺"),
            (18,7,"Orthopedics","🦴"),(19,7,"Obstetrics","🤱"),(20,7,"Pediatrics","🧒"),(21,7,"Emergency","🚨"),
            (22,9,"Cardiology","❤️"),(23,9,"Neurology","🧠"),(24,9,"ICU","🏥"),
            (25,12,"Cardiology","❤️"),(26,12,"Neurology","🧠"),(27,12,"Emergency","🚨"),
        ]
        cursor.executemany(
            "INSERT INTO departments (id,hospital_id,name,icon) VALUES (?,?,?,?)",
            departments
        )

        schemes = [
            # hospital_id, name, category, available, benefit, eligibility, steps_json
            (1,"Aarogyasri","all",1,"Free treatment up to ₹5 lakh for 2000+ procedures","BPL families with White Ration Card in AP/Telangana",'["Carry Ration Card + Aadhaar","Visit Aarogyasri desk","Get pre-authorisation","Treatment starts free"]'),
            (1,"Ayushman Bharat","all",1,"₹5 lakh health cover per family per year","SECC identified families",'["Check eligibility at mera.pmjay.gov.in","Carry Aadhaar/Voter ID","Visit empanelment desk","Cashless treatment"]'),
            (2,"Aarogyasri","all",1,"Free cardiac surgeries, bypass, stents covered","BPL White Ration Card holders",'["Carry Ration Card","Visit Aarogyasri Help Desk","TMS card generated","Surgery done free"]'),
            (2,"Ayushman Bharat","all",1,"₹5 lakh cashless cover, 1500+ procedures","SECC families",'["Verify eligibility online","Visit empanelment desk","Cashless admission","Discharge free"]'),
            (2,"PM Matru Vandana","pregnant",1,"₹5000 maternity benefit in 3 instalments for first child","Women ≥19 yrs, first pregnancy",'["Register at AWC","Submit bank details","Provide MCP card","Receive in 3 instalments"]'),
            (2,"Balasevika Child Care","child",1,"Free healthcare and nutrition for children up to 6 years","Children below 6 years from low-income families",'["Visit Anganwadi Centre","Enroll child","Regular checkups","Free nutrition supplements"]'),
            (3,"Ayushman Bharat","all",1,"Cancer treatment up to ₹5 lakh covered","SECC families",'["Verify at help desk","Cashless treatment","Submit documents","Discharge free"]'),
            (3,"Aarogyasri","all",0,"Not available at this centre","N/A",'["Not available. Please visit NIMS or Apollo."]'),
            (4,"Aarogyasri","all",1,"Covers cardiac, neuro, ortho procedures","BPL White Ration Card holders",'["Carry Ration Card","Aadhaar mandatory","Visit Help Desk","Pre-auth initiated"]'),
            (4,"PM Matru Vandana","pregnant",1,"₹5000 maternity benefit","First pregnancy, registered mother",'["Register at AWC","Submit documents","Bank account needed","Receive instalments"]'),
            (5,"Aarogyasri","all",1,"Covers joint replacement, fracture management","BPL card holders in AP",'["Carry White Ration Card","Visit Aarogyasri counter","Pre-auth for procedure","Free surgery"]'),
            (7,"Aarogyasri","all",1,"Full BPL health coverage, 2000+ procedures","White Ration Card holders",'["Carry Ration Card","Aadhaar","Help desk","Free treatment authorized"]'),
            (7,"Women Welfare Scheme","women",1,"Free OPD, cancer screening for women","All women above 18 years",'["Visit women OPD","Register","Checkup done free","Reports provided"]'),
            (7,"PM Matru Vandana","pregnant",1,"₹5000 cash for first pregnancy","Registered mothers ≥19 yrs",'["AWC registration","Documents","3 instalments"]'),
            (7,"Balasevika","child",1,"Child nutrition and healthcare monthly monitoring","Children 0-6 years",'["Visit Anganwadi","Registration","Monthly checkup","Free nutrition"]'),
            (7,"Arogyam Men","men",1,"Free preventive health checkup for men","Men above 30 years",'["Visit Arogyam OPD","Carry Aadhaar","Free tests","Report same day"]'),
            (9,"Ayushman Bharat","all",1,"₹5 lakh coverage, cardiac surgeries covered","SECC families",'["Check eligibility","Help desk","Cashless treatment","Free discharge"]'),
            (12,"Aarogyasri","all",1,"Covers cardiac, neurological procedures","BPL White Ration Card",'["Carry Ration Card","Visit desk","Pre-auth","Free treatment"]'),
            (12,"Ayushman Bharat","all",1,"₹5 lakh cashless healthcare cover","SECC families",'["Eligibility check","Visit desk","Cashless IPD","No cost discharge"]'),
        ]
        for s in schemes:
            cursor.execute(
                "INSERT INTO schemes (hospital_id,scheme_name,category,is_available,benefit,eligibility,steps) VALUES (?,?,?,?,?,?,?)",
                s
            )

    # Ensure at least 7 hospitals exist for each supported city.
    curated_hospitals = [
        ("Apollo Jubilee", "Hyderabad", "Jubilee Hills, Hyderabad", "040-30001001", 4.8, "Cardiology", "H", 720, 1, 1, 1),
        ("AIG Gachibowli", "Hyderabad", "Gachibowli, Hyderabad", "040-30001002", 4.7, "Gastroenterology", "H", 650, 1, 1, 1),
        ("Yashoda Somajiguda", "Hyderabad", "Somajiguda, Hyderabad", "040-30001003", 4.6, "Oncology", "H", 500, 1, 1, 1),
        ("KIMS Secunderabad", "Hyderabad", "Minister Road, Secunderabad", "040-30001004", 4.5, "Multi-speciality", "H", 620, 1, 1, 1),
        ("Care Banjara", "Hyderabad", "Banjara Hills, Hyderabad", "040-30001005", 4.5, "Neurology", "H", 480, 1, 1, 1),
        ("Rainbow Childrens", "Hyderabad", "Banjara Hills, Hyderabad", "040-30001006", 4.4, "Pediatrics", "H", 280, 1, 1, 1),
        ("Sunshine Medcity", "Hyderabad", "Gachibowli, Hyderabad", "040-30001007", 4.3, "Orthopedic", "H", 260, 1, 1, 1),

        ("Manipal Whitefield", "Bengaluru", "Whitefield, Bengaluru", "080-30002001", 4.8, "Cardiology", "H", 700, 1, 1, 1),
        ("Fortis Bannerghatta", "Bengaluru", "Bannerghatta Road, Bengaluru", "080-30002002", 4.7, "Oncology", "H", 640, 1, 1, 1),
        ("Narayana Health City", "Bengaluru", "Bommasandra, Bengaluru", "080-30002003", 4.7, "Cardiology", "H", 900, 1, 1, 1),
        ("Aster CMI", "Bengaluru", "Hebbal, Bengaluru", "080-30002004", 4.6, "Neurology", "H", 520, 1, 1, 1),
        ("Sakra World", "Bengaluru", "Marathahalli, Bengaluru", "080-30002005", 4.5, "Orthopedic", "H", 360, 1, 1, 1),
        ("Ramaiah Memorial", "Bengaluru", "New BEL Road, Bengaluru", "080-30002006", 4.4, "Multi-speciality", "H", 420, 1, 1, 1),
        ("Columbia Asia Yeshwanthpur", "Bengaluru", "Yeshwanthpur, Bengaluru", "080-30002007", 4.3, "General Medicine", "H", 240, 1, 1, 1),

        ("Apollo Greams", "Chennai", "Greams Road, Chennai", "044-30003001", 4.8, "Cardiology", "H", 720, 1, 1, 1),
        ("MIOT International", "Chennai", "Manapakkam, Chennai", "044-30003002", 4.7, "Orthopedic", "H", 600, 1, 1, 1),
        ("SRM Global", "Chennai", "Kattankulathur, Chennai", "044-30003003", 4.5, "Multi-speciality", "H", 450, 1, 1, 1),
        ("MGM Cancer Institute", "Chennai", "Aminjikarai, Chennai", "044-30003004", 4.6, "Oncology", "H", 380, 1, 1, 1),
        ("SIMS Vadapalani", "Chennai", "Vadapalani, Chennai", "044-30003005", 4.4, "Neurology", "H", 320, 1, 1, 1),
        ("Kauvery Alwarpet", "Chennai", "Alwarpet, Chennai", "044-30003006", 4.4, "Cardiology", "H", 310, 1, 1, 1),
        ("Gleneagles Perumbakkam", "Chennai", "Perumbakkam, Chennai", "044-30003007", 4.3, "Multi-speciality", "H", 350, 1, 1, 1),

        ("Lilavati Bandra", "Mumbai", "Bandra West, Mumbai", "022-30004001", 4.8, "Cardiology", "H", 620, 1, 1, 1),
        ("Kokilaben Andheri", "Mumbai", "Andheri West, Mumbai", "022-30004002", 4.8, "Oncology", "H", 700, 1, 1, 1),
        ("Nanavati Vile Parle", "Mumbai", "Vile Parle West, Mumbai", "022-30004003", 4.7, "Neurology", "H", 540, 1, 1, 1),
        ("HN Reliance Girgaon", "Mumbai", "Girgaon, Mumbai", "022-30004004", 4.6, "Multi-speciality", "H", 420, 1, 1, 1),
        ("Fortis Mulund", "Mumbai", "Mulund West, Mumbai", "022-30004005", 4.5, "Cardiology", "H", 360, 1, 1, 1),
        ("Jaslok Peddar Road", "Mumbai", "Peddar Road, Mumbai", "022-30004006", 4.4, "Nephrology", "H", 330, 1, 1, 1),
        ("Global Sion", "Mumbai", "Sion, Mumbai", "022-30004007", 4.3, "Orthopedic", "H", 280, 1, 1, 1),

        ("AIIMS Delhi", "Delhi", "Ansari Nagar, New Delhi", "011-30005001", 4.8, "Multi-speciality", "H", 1100, 1, 1, 1),
        ("Max Saket", "Delhi", "Saket, New Delhi", "011-30005002", 4.7, "Cardiology", "H", 700, 1, 1, 1),
        ("Fortis Shalimar Bagh", "Delhi", "Shalimar Bagh, Delhi", "011-30005003", 4.6, "Oncology", "H", 500, 1, 1, 1),
        ("Apollo Indraprastha", "Delhi", "Sarita Vihar, Delhi", "011-30005004", 4.7, "Neurology", "H", 720, 1, 1, 1),
        ("BLK Max", "Delhi", "Rajendra Place, Delhi", "011-30005005", 4.6, "Oncology", "H", 650, 1, 1, 1),
        ("Sir Ganga Ram", "Delhi", "Old Rajinder Nagar, Delhi", "011-30005006", 4.5, "Cardiology", "H", 550, 1, 1, 1),
        ("Moolchand Lajpat Nagar", "Delhi", "Lajpat Nagar, Delhi", "011-30005007", 4.3, "General Medicine", "H", 320, 1, 1, 1),
    ]
    for hospital in curated_hospitals:
        name, city = hospital[0], hospital[1]
        exists = cursor.execute(
            "SELECT id FROM hospitals WHERE name=? AND city=?",
            [name, city]
        ).fetchone()
        if not exists:
            cursor.execute(
                "INSERT INTO hospitals (name,city,address,phone,rating,specialization,icon,beds,emergency,aarogyasri,ayushman) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                hospital
            )

    db.commit()
    db.close()

# ── AUTH HELPERS ─────────────────────────────────────────────────────────────────

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    user = db.execute("SELECT id,name,mobile FROM users WHERE id=?", [user_id]).fetchone()
    return dict(user) if user else None
# ── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the main SPA"""
    return render_template('index.html')

# authentication endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    mobile = ''.join(ch for ch in data.get('mobile', '') if ch.isdigit())
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    if not name or not mobile or not password or not confirm_password:
        return jsonify({'error': 'Name, mobile, password and confirm password are required'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Password and confirm password must match'}), 400
    if len(mobile) < 10:
        return jsonify({'error': 'Please enter a valid mobile number'}), 400
    db = get_db()
    try:
        exists = db.execute("SELECT id FROM users WHERE mobile=?", [mobile]).fetchone()
        if exists:
            return jsonify({'error': 'Mobile number already registered'}), 409
        pwd_hash = generate_password_hash(password)
        synthetic_email = f"{mobile}@mobile.local"
        db.execute("INSERT INTO users (name,email,password_hash,mobile) VALUES (?,?,?,?)",
                   [name, synthetic_email, pwd_hash, mobile])
        db.commit()
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        session['user_id'] = user_id
        return jsonify({'success': True, 'user': {'id': user_id, 'name': name, 'mobile': mobile}})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Unable to register with this mobile number'}), 409

@app.route('/api/login/request-otp', methods=['POST'])
def request_login_otp():
    data = request.get_json() or {}
    mobile = ''.join(ch for ch in data.get('mobile', '') if ch.isdigit())
    if len(mobile) < 10:
        return jsonify({'error': 'Valid mobile number is required'}), 400

    db = get_db()
    row = db.execute("SELECT id,name,mobile FROM users WHERE mobile=?", [mobile]).fetchone()
    if not row:
        return jsonify({'error': 'Account not found for this mobile number'}), 404

    otp = f"{random.randint(0, 999999):06d}"
    session['otp_mobile'] = mobile
    session['otp_code'] = otp
    session['otp_expiry'] = int(time.time()) + 300  # 5 mins

    # Demo mode: return OTP in response (replace with SMS provider in production)
    return jsonify({'success': True, 'message': 'OTP sent successfully', 'otp': otp})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    mobile = ''.join(ch for ch in data.get('mobile', '') if ch.isdigit())
    password = data.get('password', '')
    otp = str(data.get('otp', '')).strip()
    mode = (data.get('mode') or 'password').strip().lower()

    if not mobile:
        return jsonify({'error': 'Mobile number is required'}), 400

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE mobile=?", [mobile]).fetchone()
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401

    if mode == 'otp':
        if not otp:
            return jsonify({'error': 'OTP is required'}), 400
        stored_mobile = session.get('otp_mobile')
        stored_otp = session.get('otp_code')
        expiry = int(session.get('otp_expiry') or 0)
        if stored_mobile != mobile or not stored_otp:
            return jsonify({'error': 'Please request OTP first'}), 400
        if int(time.time()) > expiry:
            return jsonify({'error': 'OTP expired. Please request a new OTP'}), 400
        if otp != stored_otp:
            return jsonify({'error': 'Invalid OTP'}), 401
        session.pop('otp_mobile', None)
        session.pop('otp_code', None)
        session.pop('otp_expiry', None)
    else:
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        if not check_password_hash(row['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = row['id']
    return jsonify({'success': True, 'user': {'id': row['id'], 'name': row['name'], 'mobile': row['mobile']}})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/user', methods=['GET'])
def current_user():
    user = get_current_user()
    return jsonify({'user': user})


@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Get filtered hospital list"""
    db = get_db()
    city = request.args.get('city', '')
    search = request.args.get('search', '')
    spec = request.args.get('spec', '')
    aarogyasri = request.args.get('aarogyasri', '')

    query = "SELECT * FROM hospitals WHERE 1=1"
    params = []
    if city:
        query += " AND city = ?"
        params.append(city)
    if search:
        query += " AND (name LIKE ? OR city LIKE ? OR specialization LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if spec and spec != 'all':
        if spec == 'aarogyasri':
            query += " AND aarogyasri = 1"
        else:
            query += " AND specialization LIKE ?"
            params.append(f'%{spec}%')
    if aarogyasri == '1':
        query += " AND aarogyasri = 1"

    query += " ORDER BY rating DESC"
    if city and city in SUPPORTED_CITIES:
        query += " LIMIT 7"
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/hospitals/<int:hospital_id>', methods=['GET'])
def get_hospital_detail(hospital_id):
    """Full hospital details with specialists, departments, schemes"""
    db = get_db()
    hospital = db.execute("SELECT * FROM hospitals WHERE id=?", [hospital_id]).fetchone()
    if not hospital:
        return jsonify({'error': 'Not found'}), 404

    specialists = db.execute("SELECT * FROM specialists WHERE hospital_id=?", [hospital_id]).fetchall()
    departments = db.execute("SELECT * FROM departments WHERE hospital_id=?", [hospital_id]).fetchall()
    schemes = db.execute("SELECT * FROM schemes WHERE hospital_id=?", [hospital_id]).fetchall()

    result = dict(hospital)
    result['specialists'] = [dict(s) for s in specialists]
    result['departments'] = [dict(d) for d in departments]

    # Parse schemes steps JSON
    schemes_list = []
    for s in schemes:
        sd = dict(s)
        try:
            sd['steps'] = json.loads(sd['steps'])
        except:
            sd['steps'] = [sd['steps']]
        schemes_list.append(sd)
    result['schemes'] = schemes_list
    return jsonify(result)


@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get distinct cities"""
    db = get_db()
    rows = db.execute("SELECT DISTINCT city FROM hospitals").fetchall()
    available = {r[0] for r in rows}
    curated = [city for city in SUPPORTED_CITIES if city in available]
    return jsonify(curated if curated else sorted(available))


@app.route('/api/ai/disease', methods=['POST'])
def ai_disease():
    """AI-powered disease information endpoint"""
    data = request.get_json()
    query = data.get('query', '').lower().strip()
    # if user is logged in, we could track him/her using session
    user = get_current_user()
    if user:
        data['user_id'] = user['id']
    if not query:
        return jsonify({'error': 'Query required'}), 400

    # Try Claude API if key available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"""You are a helpful medical information assistant. A user asked about: "{query}"

Provide a structured response in the following EXACT JSON format:
{{
  "title": "Disease/Condition Name",
  "description": "Simple explanation in 2-3 sentences for a common person",
  "dos": ["do1", "do2", "do3", "do4", "do5"],
  "donts": ["dont1", "dont2", "dont3", "dont4", "dont5"],
  "food": [
    {{"icon": "emoji", "text": "food recommendation"}},
    {{"icon": "emoji", "text": "food recommendation"}},
    {{"icon": "emoji", "text": "food recommendation"}}
  ],
  "prevention": [
    {{"icon": "emoji", "text": "prevention tip"}},
    {{"icon": "emoji", "text": "prevention tip"}},
    {{"icon": "emoji", "text": "prevention tip"}}
  ],
  "specialist": "type of doctor to see",
  "emergency": false
}}

Keep language simple and clear for general public. If it sounds like a medical emergency, set emergency to true."""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            text = message.content[0].text
            # Extract JSON from response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1:
                result = json.loads(text[start:end])
                return jsonify({'source': 'ai', 'data': result})
        except Exception as e:
            pass  # Fall through to mock data

    # Mock AI responses database
    DISEASE_DB = {
        "diabetes": {
            "title": "Diabetes Mellitus",
            "description": "Diabetes is a chronic condition where your body cannot properly process sugar (glucose) from food, causing high blood sugar levels. It requires ongoing management through diet, exercise, and often medication.",
            "dos": ["Monitor blood sugar daily", "Take medicines on time", "Eat small meals every 3-4 hours", "Walk 30 minutes daily", "Drink plenty of water", "Wear comfortable footwear"],
            "donts": ["Avoid sugary drinks & sweets", "Don't skip meals", "Avoid smoking & alcohol", "Don't ignore wound healing", "Don't skip follow-up visits"],
            "food": [{"icon": "🥗", "text": "Eat green leafy vegetables like spinach and fenugreek"}, {"icon": "🫘", "text": "Include lentils, beans, and whole grains in diet"}, {"icon": "🍎", "text": "Fruits like guava, papaya, and berries (in moderation)"}, {"icon": "🚫", "text": "Avoid white rice, white bread, and sugary foods"}],
            "prevention": [{"icon": "🏃", "text": "30 min physical activity daily reduces insulin resistance"}, {"icon": "⚖️", "text": "Maintain healthy body weight (BMI 18.5-24.9)"}, {"icon": "🧘", "text": "Manage stress with yoga and meditation"}, {"icon": "🩺", "text": "Regular HbA1c and eye checkup every 3 months"}],
            "specialist": "Endocrinologist / Diabetologist",
            "emergency": False
        },
        "fever": {
            "title": "Fever (Pyrexia)",
            "description": "Fever is when body temperature rises above 38°C (100.4°F). It is usually a sign that your body is fighting an infection. Most fevers resolve in 3-5 days with proper care and rest.",
            "dos": ["Rest adequately", "Drink plenty of fluids", "Take paracetamol as per dosage", "Apply cool wet cloth on forehead", "Monitor temperature every 4 hours"],
            "donts": ["Don't self-medicate with antibiotics", "Avoid heavy blankets", "Don't delay if fever > 103°F", "Avoid cold baths when feverish"],
            "food": [{"icon": "🥣", "text": "Light foods like khichdi, idli, rice porridge"}, {"icon": "🍋", "text": "Vitamin C rich fruits like lemon and orange"}, {"icon": "💧", "text": "ORS, coconut water, soups every hour"}],
            "prevention": [{"icon": "🧼", "text": "Wash hands regularly with soap for 20 seconds"}, {"icon": "😷", "text": "Wear mask in crowded places during outbreak season"}, {"icon": "💉", "text": "Keep vaccinations up to date"}],
            "specialist": "General Physician",
            "emergency": False
        },
        "hypertension": {
            "title": "Hypertension (High Blood Pressure)",
            "description": "Hypertension means your blood pressure is consistently too high (≥140/90 mmHg). Called the 'silent killer' because it often has no symptoms but can lead to heart attack, stroke, or kidney damage.",
            "dos": ["Take BP medicine daily as prescribed", "Eat low-salt diet", "Exercise regularly", "Monitor BP at home", "Sleep 7-8 hours"],
            "donts": ["Don't eat excess salt or pickles", "Don't smoke", "Don't drink alcohol", "Don't stop medicines without doctor advice", "Avoid stress and overexertion"],
            "food": [{"icon": "🍌", "text": "Bananas - potassium helps lower BP"}, {"icon": "🥦", "text": "Broccoli, spinach, and beets are excellent"}, {"icon": "🐟", "text": "Fatty fish like salmon (omega-3 reduces BP)"}, {"icon": "🧂", "text": "Limit sodium to less than 2300mg/day"}],
            "prevention": [{"icon": "🏃", "text": "Aerobic exercise 150 min/week"}, {"icon": "⚖️", "text": "Lose even 5 kg if overweight to significantly reduce BP"}, {"icon": "🚬", "text": "Quit smoking immediately"}, {"icon": "🧘", "text": "Practice deep breathing and relaxation techniques"}],
            "specialist": "Cardiologist",
            "emergency": False
        },
        "heart": {
            "title": "Coronary Heart Disease",
            "description": "Heart disease refers to conditions affecting the heart's structure and function, most commonly when arteries get blocked with plaque, potentially causing chest pain, heart attacks, or heart failure.",
            "dos": ["Take medicines as prescribed", "Eat heart-healthy diet", "Exercise regularly (with doctor approval)", "Monitor cholesterol and BP", "Attend cardiac follow-ups"],
            "donts": ["Don't ignore chest pain or breathlessness - call 108 immediately", "Avoid fatty and fried foods", "Don't smoke", "Don't consume alcohol", "Avoid stress"],
            "food": [{"icon": "🥑", "text": "Avocado and olive oil (healthy fats)"}, {"icon": "🫐", "text": "Berries and dark fruits (antioxidants)"}, {"icon": "🐟", "text": "Salmon, sardines (omega-3 fatty acids)"}],
            "prevention": [{"icon": "🚬", "text": "Quitting smoking reduces heart risk by 50% in 1 year"}, {"icon": "⚖️", "text": "Maintain healthy weight"}, {"icon": "🏃", "text": "150 minutes of moderate exercise per week"}, {"icon": "🩺", "text": "Annual cholesterol and BP screening after age 40"}],
            "specialist": "Cardiologist",
            "emergency": True
        },
        "cancer": {
            "title": "Cancer (General Overview)",
            "description": "Cancer occurs when cells in the body grow uncontrollably. There are 100+ types of cancer. Early detection is key to successful treatment. Many cancers are treatable when caught early.",
            "dos": ["Follow oncologist's treatment plan", "Maintain proper nutrition", "Stay hydrated", "Join cancer support groups", "Report new symptoms immediately"],
            "donts": ["Don't self-medicate", "Avoid smoking and tobacco", "Don't consume alcohol", "Don't delay treatment", "Avoid excessive sun exposure"],
            "food": [{"icon": "🥦", "text": "Cruciferous vegetables have anti-cancer properties"}, {"icon": "🫐", "text": "Berries and grapes rich in antioxidants"}, {"icon": "🌰", "text": "Turmeric and ginger have anti-inflammatory effects"}],
            "prevention": [{"icon": "🚬", "text": "Tobacco cessation is the single most important prevention step"}, {"icon": "🩺", "text": "Regular cancer screenings as per age"}, {"icon": "💉", "text": "HPV and Hepatitis B vaccines reduce cancer risk"}],
            "specialist": "Oncologist",
            "emergency": False
        },
        "cough": {
            "title": "Cough & Cold",
            "description": "Cough is a reflex action to clear the airway. Acute cough (< 3 weeks) is usually viral. Chronic cough (> 8 weeks) may indicate asthma, allergies, or other conditions needing evaluation.",
            "dos": ["Stay hydrated with warm water", "Inhale steam with eucalyptus", "Rest your voice", "Keep head elevated while sleeping", "Take honey in warm water"],
            "donts": ["Don't smoke or be near smokers", "Avoid cold drinks", "Don't use antibiotics without prescription", "Avoid talking loudly when throat is sore"],
            "food": [{"icon": "🍯", "text": "Honey with warm water or tea soothes throat"}, {"icon": "🫚", "text": "Ginger tea with tulsi leaves"}, {"icon": "🥛", "text": "Warm turmeric milk (haldi doodh)"}],
            "prevention": [{"icon": "😷", "text": "Wear N95 mask in dusty or polluted environments"}, {"icon": "🧼", "text": "Frequent handwashing prevents viral spread"}, {"icon": "💉", "text": "Annual flu vaccine reduces respiratory infection risk"}],
            "specialist": "General Physician / Pulmonologist",
            "emergency": False
        }
    }

    # Fuzzy match
    result = None
    for key, val in DISEASE_DB.items():
        if key in query or query in key or any(w in query for w in key.split()):
            result = val
            break

    if not result:
        # Generic response
        result = {
            "title": query.title(),
            "description": f"'{query}' is a medical condition that requires proper diagnosis by a qualified healthcare professional. Symptoms and severity vary. Early consultation leads to better outcomes.",
            "dos": ["Consult a doctor immediately", "Follow prescribed treatment", "Rest adequately", "Stay hydrated", "Monitor your symptoms"],
            "donts": ["Don't self-medicate", "Don't ignore worsening symptoms", "Avoid stress", "Don't miss follow-up visits"],
            "food": [{"icon": "🥗", "text": "Eat balanced diet with fruits and vegetables"}, {"icon": "💧", "text": "Drink 8+ glasses of water daily"}],
            "prevention": [{"icon": "🏃", "text": "Regular exercise improves immunity"}, {"icon": "🩺", "text": "Annual health checkups catch problems early"}],
            "specialist": "General Physician",
            "emergency": False
        }

    # Save to search history if session_id provided
    session_id = data.get('session_id', '')
    if session_id and query:
        try:
            db = get_db()
            db.execute("INSERT INTO search_history (session_id, query) VALUES (?,?)", [session_id, query])
            # additionally if user logged in, store user_id separately
            if user:
                db.execute("UPDATE search_history SET session_id=? WHERE rowid = last_insert_rowid()",[f"user_{user['id']}"])
            db.commit()
        except:
            pass

    return jsonify({'source': 'mock', 'data': result})


@app.route('/api/ai/advice', methods=['POST'])
def ai_health_advice():
    """AI-style personalized health advice endpoint"""
    data = request.get_json() or {}
    query = (data.get('query') or '').strip().lower()
    if not query:
        return jsonify({'error': 'Query required'}), 400

    advice_db = {
        'stress': {
            'title': 'Stress Management Advice',
            'summary': 'Long-term stress can affect sleep, blood pressure, digestion, and mood. Small daily habits can reduce stress and improve focus.',
            'recommended': [
                'Do 10 minutes of breathing exercises twice daily',
                'Take short movement breaks every 60 minutes',
                'Maintain a fixed sleep and wake-up time',
                'Reduce caffeine intake after 4 PM',
                'Talk to a trusted person if stress feels overwhelming'
            ],
            'avoid': [
                'Skipping meals during busy days',
                'Using alcohol or smoking to cope',
                'Excessive late-night screen time',
                'Ignoring persistent anxiety symptoms'
            ],
            'when_to_consult': 'Consult a doctor/mental health professional if stress affects work, sleep, appetite, or relationships for more than 2 weeks.'
        },
        'sleep': {
            'title': 'Better Sleep Guidance',
            'summary': 'Sleep quality improves when your body has a consistent schedule and low stimulation before bedtime.',
            'recommended': [
                'Keep a fixed sleep routine every day',
                'Stop mobile/laptop use 45 minutes before sleep',
                'Keep your room cool, dark, and quiet',
                'Eat dinner at least 2 hours before bedtime',
                'Practice relaxation or light stretching before bed'
            ],
            'avoid': [
                'Heavy meals close to bedtime',
                'Late coffee/tea and energy drinks',
                'Long daytime naps',
                'Using bed for work activities'
            ],
            'when_to_consult': 'Consult a doctor if insomnia continues beyond 3 weeks, or if there is snoring with daytime fatigue.'
        },
        'weight': {
            'title': 'Healthy Weight Advice',
            'summary': 'Safe weight loss is gradual and sustainable. Focus on balanced eating, daily activity, and regular tracking.',
            'recommended': [
                'Aim for 30-45 minutes of activity on most days',
                'Use a plate method: half vegetables, quarter protein, quarter grains',
                'Drink water before meals and avoid sugary drinks',
                'Track weight once weekly at the same time',
                'Set realistic goals (0.5-1 kg per week)'
            ],
            'avoid': [
                'Crash diets and meal skipping',
                'Very low-calorie plans without supervision',
                'Frequent fried and ultra-processed foods',
                'Comparing progress daily'
            ],
            'when_to_consult': 'Consult a doctor/dietitian if you have diabetes, thyroid problems, or sudden unexplained weight changes.'
        },
        'bp': {
            'title': 'Blood Pressure Care',
            'summary': 'Managing blood pressure daily helps prevent heart, kidney, and brain complications.',
            'recommended': [
                'Reduce salt in cooking and packaged foods',
                'Walk at least 30 minutes daily',
                'Monitor blood pressure at home regularly',
                'Take medicines exactly as prescribed',
                'Practice stress reduction techniques'
            ],
            'avoid': [
                'Stopping BP medicine without advice',
                'Smoking and excess alcohol',
                'High-salt snacks and pickles frequently',
                'Ignoring headaches, dizziness, or chest discomfort'
            ],
            'when_to_consult': 'Seek urgent care for severe headache, chest pain, breathlessness, or very high BP readings.'
        }
    }

    match_key = None
    for key in advice_db.keys():
        if key in query:
            match_key = key
            break

    result = advice_db.get(match_key, {
        'title': f'Health Advice for {query.title()}',
        'summary': 'A personalized routine with healthy diet, hydration, sleep, exercise, and stress control is helpful for most health goals.',
        'recommended': [
            'Follow regular meal timings and hydration',
            'Do at least 30 minutes of physical activity daily',
            'Sleep 7-8 hours with a fixed schedule',
            'Track symptoms and improvements weekly',
            'Consult a qualified doctor for diagnosis-specific guidance'
        ],
        'avoid': [
            'Self-medicating without medical advice',
            'Ignoring persistent or worsening symptoms',
            'Unverified internet remedies',
            'Skipping follow-up visits'
        ],
        'when_to_consult': 'Consult a doctor if symptoms persist, worsen, or interfere with your daily routine.'
    })

    return jsonify({'source': 'mock', 'data': result})


@app.route('/api/ai/chat', methods=['POST'])
def ai_health_chat():
    """Free-form health chatbot endpoint"""
    data = request.get_json() or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'Query required'}), 400

    q = query.lower()

    follow_up_prompts = [
        "If you want, tell me your age and how long this has been happening.",
        "Share if symptoms are getting better or worse through the day.",
        "If there are other symptoms, mention them and I can refine guidance.",
        "Tell me if you have BP/diabetes/asthma so advice can be safer.",
    ]
    random.shuffle(follow_up_prompts)
    follow_up = follow_up_prompts[0]

    emergency_replies = [
        "This may be an emergency. Call 108 now or go to the nearest emergency hospital immediately.",
        "These signs can be serious. Please seek urgent care now and do not delay online consultation.",
        "Please treat this as urgent: call 108 or visit emergency services right away.",
    ]
    fever_replies = [
        "For mild fever/cold: hydrate well, rest, and monitor temperature every 6-8 hours.",
        "Start with rest, warm fluids, and symptom tracking. Seek care if fever continues beyond 2-3 days.",
        "You can try supportive care first: light food, fluids, and adequate sleep. Watch for worsening symptoms.",
    ]
    bp_replies = [
        "For BP care: reduce salt, continue prescribed medicines, and check BP regularly at home.",
        "Keep BP controlled with low-salt diet, daily walking, and medicine adherence.",
        "Track BP readings morning/evening, avoid excess salt, and do not skip BP tablets.",
    ]
    diabetes_replies = [
        "For diabetes: fixed meal timings, fewer sugary drinks, daily activity, and regular glucose checks help.",
        "Keep sugars stable with portion control, exercise, hydration, and medicine compliance.",
        "Prioritize low-glycemic meals, walking, and glucose monitoring; avoid abrupt medicine changes.",
    ]
    sleep_replies = [
        "To improve sleep: fixed bedtime, no screens 45 minutes before sleep, and reduced late caffeine.",
        "Try a strict sleep routine, a dark quiet room, and avoid heavy meals near bedtime.",
        "Better sleep usually comes from routine timing, low evening stimulation, and stress reduction.",
    ]
    diet_replies = [
        "Use plate method: half vegetables, quarter protein, quarter whole grains.",
        "Prefer home-cooked food, reduce fried/processed items, and maintain hydration.",
        "For healthy nutrition: increase fiber/protein, reduce sugar and refined snacks.",
    ]
    hospital_replies = [
        "Use 'Find Hospitals' in this app and choose location for nearby options.",
        "Open the Hospitals tab, set your city, and search by symptom or speciality.",
        "You can pick location first and then search hospital/speciality for faster results.",
    ]
    stomach_replies = [
        "Stomach pain can happen due to acidity, indigestion, gas, infection, or food intolerance.",
        "Common reasons include gastritis, gas, constipation, infection, or sometimes urinary causes.",
        "Possible causes are acidity, gas, food infection, ulcer irritation, or bowel issues.",
    ]

    def varied(base_options, caution):
        chosen = random.choice(base_options)
        return f"{chosen} {caution} {follow_up}"

    if any(term in q for term in ['chest pain', 'not breathing', 'severe bleeding', 'stroke', 'fainted', 'unconscious']):
        reply = f"{random.choice(emergency_replies)} {follow_up}"
    elif any(term in q for term in ['stomach pain', 'stomach ache', 'abdominal pain', 'gastric', 'acidity']):
        caution = "Seek urgent medical care if pain is severe, with vomiting, blood in stool, fever, or pain >24-48 hours."
        reply = varied(stomach_replies, caution)
    elif any(term in q for term in ['fever', 'cold', 'cough', 'headache']):
        caution = "See a doctor quickly for breathing trouble, persistent high fever, severe weakness, or confusion."
        reply = varied(fever_replies, caution)
    elif any(term in q for term in ['bp', 'blood pressure', 'hypertension']):
        caution = "Get urgent care for chest pain, severe headache, sudden breathlessness, or very high BP readings."
        reply = varied(bp_replies, caution)
    elif any(term in q for term in ['sugar', 'diabetes', 'glucose']):
        caution = "Consult your doctor before any medication change or fasting plan."
        reply = varied(diabetes_replies, caution)
    elif any(term in q for term in ['sleep', 'insomnia']):
        caution = "If poor sleep continues for 2-3 weeks, consult a doctor."
        reply = varied(sleep_replies, caution)
    elif any(term in q for term in ['diet', 'food', 'weight']):
        caution = "Sustainable progress is better than crash dieting."
        reply = varied(diet_replies, caution)
    elif any(term in q for term in ['hospital', 'doctor', 'specialist']):
        caution = "If you share symptoms, I can suggest the right specialist."
        reply = varied(hospital_replies, caution)
    else:
        generic_openers = [
            "I can help with symptoms, diet, sleep, BP, diabetes, and specialist guidance.",
            "I can guide you step-by-step for common health doubts and when to seek care.",
            "I can provide practical health guidance and warning signs to watch for.",
        ]
        reply = f"{random.choice(generic_openers)} {follow_up}"

    return jsonify({'source': 'mock', 'reply': reply})


@app.route('/api/tokens', methods=['POST'])
def book_token():
    """Book a queue token"""
    data = request.get_json()
    hospital_id = data.get('hospital_id')
    session_id = data.get('session_id', 'guest')

    db = get_db()
    hospital = db.execute("SELECT * FROM hospitals WHERE id=?", [hospital_id]).fetchone()
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404

    # Generate token number
    letter = random.choice('ABCDE')
    number = random.randint(30, 60)
    token_number = f"{letter}{number}"
    ahead = random.randint(3, 15)
    wait = ahead * 2

    db.execute(
        "INSERT OR REPLACE INTO tokens (token_number, hospital_id, hospital_name, session_id, people_ahead, estimated_wait) VALUES (?,?,?,?,?,?)",
        [token_number, hospital_id, hospital['name'], session_id, ahead, wait]
    )
    db.commit()

    return jsonify({
        'token': token_number,
        'hospital_id': hospital_id,
        'hospital_name': hospital['name'],
        'people_ahead': ahead,
        'estimated_wait': wait,
        'current_token': f"{letter}{number - ahead - 1}"
    })


@app.route('/api/tokens/<token_number>/status', methods=['GET'])
def token_status(token_number):
    """Get live queue status (simulated)"""
    db = get_db()
    token = db.execute("SELECT * FROM tokens WHERE token_number=?", [token_number]).fetchone()
    if not token:
        return jsonify({'error': 'Token not found'}), 404

    # Simulate queue movement
    td = dict(token)
    booked_at = td.get('booked_at', '')
    try:
        from datetime import datetime, timezone
        bt = datetime.fromisoformat(str(booked_at).replace('Z',''))
        elapsed = (datetime.now() - bt).seconds
        reduction = elapsed // 30  # reduce 1 person every 30 seconds
        ahead = max(0, td['people_ahead'] - reduction)
    except:
        ahead = td['people_ahead']

    wait = ahead * 2
    return jsonify({
        'token': token_number,
        'people_ahead': ahead,
        'estimated_wait': wait,
        'status': 'your_turn' if ahead == 0 else ('near' if ahead <= 3 else 'waiting')
    })


@app.route('/api/ai/recommend-hospitals', methods=['POST'])
def recommend_hospitals():
    """AI hospital recommendation based on disease"""
    data = request.get_json()
    disease = data.get('disease', '').lower()
    city = data.get('city', '')

    db = get_db()
    # Map disease to specialization
    spec_map = {
        'heart': 'Cardiology', 'cardiac': 'Cardiology', 'cardio': 'Cardiology',
        'cancer': 'Oncology', 'tumor': 'Oncology',
        'brain': 'Neurology', 'neuro': 'Neurology', 'stroke': 'Neurology',
        'bone': 'Orthopedic', 'joint': 'Orthopedic', 'fracture': 'Orthopedic',
    }

    spec = None
    for k, v in spec_map.items():
        if k in disease:
            spec = v
            break

    query = "SELECT * FROM hospitals WHERE 1=1"
    params = []
    if city:
        query += " AND city = ?"
        params.append(city)
    if spec:
        query += " AND (specialization LIKE ? OR specialization = 'Multi-speciality')"
        params.append(f'%{spec}%')
    query += " ORDER BY rating DESC LIMIT 5"

    hospitals = db.execute(query, params).fetchall()
    return jsonify([dict(h) for h in hospitals])


@app.route('/api/schemes', methods=['GET'])
def get_all_schemes():
    """Get enriched government schemes for schemes page"""
    db = get_db()
    rows = db.execute("""
        SELECT scheme_name, category, benefit, eligibility, steps
        FROM schemes
        WHERE is_available=1
        ORDER BY scheme_name
    """).fetchall()

    scheme_meta = {
        'Ayushman Bharat': {
            'income_limit': 'As per SECC eligibility (BPL/economically vulnerable families)',
            'documents_required': ['Aadhaar Card', 'Ration Card', 'Family ID / PMJAY eligibility proof'],
            'approval_time': 'Verification usually same day at empanelled desk'
        },
        'Aarogyasri': {
            'income_limit': 'Primarily for BPL families with valid white ration card',
            'documents_required': ['Aadhaar Card', 'White Ration Card', 'Recent medical reports'],
            'approval_time': 'Pre-authorization generally 1-3 days for major procedures'
        },
        'PM Matru Vandana': {
            'income_limit': 'Applicable as per PMMVY rules for eligible mothers',
            'documents_required': ['Aadhaar Card', 'MCP Card', 'Bank account details'],
            'approval_time': 'Installments credited after document verification'
        },
        'Balasevika': {
            'income_limit': 'Priority for low-income families and eligible children',
            'documents_required': ['Child birth certificate (if available)', 'Parent Aadhaar', 'Local ID records'],
            'approval_time': 'Enrollment typically immediate at local center'
        },
        'Balasevika Child Care': {
            'income_limit': 'Priority for low-income families and eligible children',
            'documents_required': ['Child birth certificate (if available)', 'Parent Aadhaar', 'Local ID records'],
            'approval_time': 'Enrollment typically immediate at local center'
        },
        'Women Welfare Scheme': {
            'income_limit': 'As per state welfare eligibility norms',
            'documents_required': ['Aadhaar Card', 'Address proof', 'Any required medical records'],
            'approval_time': 'Screening and OPD benefits available after registration'
        },
        'Arogyam Men': {
            'income_limit': 'As per hospital/state program criteria',
            'documents_required': ['Aadhaar Card', 'Age proof'],
            'approval_time': 'Usually same day for routine preventive checkups'
        }
    }

    grouped = {}
    for r in rows:
        name = r['scheme_name']
        if name in grouped:
            continue

        steps_val = r['steps'] or '[]'
        try:
            parsed_steps = json.loads(steps_val) if isinstance(steps_val, str) else steps_val
            if not isinstance(parsed_steps, list):
                parsed_steps = [str(parsed_steps)]
        except Exception:
            parsed_steps = [str(steps_val)]

        meta = scheme_meta.get(name, {})
        grouped[name] = {
            'scheme_name': name,
            'category': r['category'] or 'all',
            'benefit': r['benefit'] or 'Benefit details available at scheme desk.',
            'eligibility': r['eligibility'] or 'As per scheme guidelines.',
            'income_limit': meta.get('income_limit', 'As per government scheme rules.'),
            'documents_required': meta.get('documents_required', ['Aadhaar Card', 'Address proof', 'Relevant medical reports']),
            'how_to_apply': parsed_steps,
            'approval_time': meta.get('approval_time', 'Subject to document verification and hospital process.')
        }

    return jsonify(list(grouped.values()))


# ── INIT & RUN ──────────────────────────────────────────────────────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n✅ AI Smart Health Navigator is starting...")
    print("   Open http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)
