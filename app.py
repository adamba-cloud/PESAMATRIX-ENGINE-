import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

# ================= CONFIG =================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BG = "#0b1220"
CARD = "#111a2e"
ACCENT = "#38bdf8"

CONTACTS = """
📞 <a href="tel:+254781585319" style="color:#38bdf8">+254 781 585 319</a><br>
📞 <a href="tel:+254717434943" style="color:#38bdf8">+254 717 434 943</a><br>
📧 support@pesamatrix.com<br>
🎵 TikTok: <a href="https://tiktok.com/@smartgoldsignals" style="color:#38bdf8">@smartgoldsignals</a>
"""

PAYMENTS = """
💳 Lipa Na Mpesa<br>
🏦 Paybill: <b>322372</b><br>
🔢 Account: <b>Your Unique Join Code</b>
"""

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        account_code TEXT,
        trial_end TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        status TEXT,
        created_at TEXT,
        expiry_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS access_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        expiry TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()


init_db()

# ================= HOME =================
@app.route("/")
def home():
    return render_template_string(f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <div style="display:flex;justify-content:space-between;padding:15px;background:#0f172a">
        <h2 style="color:{ACCENT}">🚀 PESAMATRIX</h2>
        <a href="/login" style="color:{ACCENT}">Admin</a>
    </div>

    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:15px">

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/videos">🎥 Free Videos</a>
        </div>

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/news">📰 Trading News</a>
        </div>

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/access">🔐 Premium Signals</a>
        </div>

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/posts">📊 Latest Posts</a>
        </div>

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/register">🟢 Join</a>
        </div>

        <div style="background:{CARD};padding:18px;border-radius:12px;text-align:center">
            <a href="/dashboard">👤 Dashboard</a>
        </div>

    </div>

    <div style="padding:15px;background:{CARD};margin:10px;border-radius:12px">
        <h3>About</h3>
        <p>We deliver high accuracy trading signals in real time.</p>
    </div>

    <div style="padding:15px;background:{CARD};margin:10px;border-radius:12px">
        <h3>Contacts</h3>
        {CONTACTS}
    </div>

    <div style="padding:15px;background:{CARD};margin:10px;border-radius:12px">
        <h3>Payments</h3>
        {PAYMENTS}
    </div>

    </body>
    """)

# ================= REGISTER (NOW WITH 4 DAY TRIAL) =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()
        trial_end = datetime.now() + timedelta(days=4)

        conn = db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO users VALUES (NULL,?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["contact"],
            code,
            trial_end.isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        return f"""
        <body style="background:{BG};color:white">
        <h2>WELCOME 🎉</h2>
        <p>Your Account Code:</p>
        <h1 style="color:{ACCENT}">{code}</h1>
        <p>🆓 Free Trial: 4 Days Active</p>
        <a href="/dashboard">Go to Dashboard</a>
        </body>
        """

    return f"""
    <body style="background:{BG};color:white">
    <form method='post'>
        <input name='name' placeholder='Name'><br><br>
        <input name='contact' placeholder='Contact'><br><br>
        <button>Join</button>
    </form>
    </body>
    """

# ================= USER DASHBOARD (NEW) =================
@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]
    now = datetime.now()

    trial_end = datetime.fromisoformat(user["trial_end"])
    active = now < trial_end

    status = "ACTIVE 🟢" if active else "EXPIRED 🔴"

    return f"""
    <body style="background:{BG};color:white;font-family:Arial">

    <h1 style="color:{ACCENT}">👤 USER DASHBOARD</h1>

    <div style="background:{CARD};padding:15px;border-radius:12px;margin:10px">
        <p><b>Name:</b> {user['name']}</p>
        <p><b>Account Code:</b> {user['account_code']}</p>
        <p><b>Trial Status:</b> {status}</p>
        <p><b>Expiry:</b> {user['trial_end']}</p>
    </div>

    <div style="background:{CARD};padding:15px;border-radius:12px;margin:10px">
        <a href="/videos">🎥 Videos</a><br>
        <a href="/news">📰 News</a><br>
        <a href="/posts">📊 Posts</a><br>
        <a href="/access">🔐 Signals</a>
    </div>

    </body>
    """

# ================= USER LOGIN (AUTO SESSION) =================
@app.route("/user_login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        code = request.form["code"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE account_code=?", (code,))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect("/dashboard")

        return "Invalid Code"

    return """
    <body style="background:#0b1220;color:white">
    <form method='post'>
        <input name='code' placeholder='Enter Account Code'>
        <button>Login</button>
    </form>
    </body>
    """

# ================= SIGNAL ACCESS CHECK (UPDATED) =================
@app.route("/access")
def access_gate():
    if not session.get("user"):
        return redirect("/user_login")

    user = session["user"]
    trial_end = datetime.fromisoformat(user["trial_end"])

    if datetime.now() > trial_end:
        return "<body style='background:#0b1220;color:white'><h2>Trial Expired ❌</h2><p>Please upgrade.</p></body>"

    session["access"] = True
    return redirect("/signals")


# ================= KEEP YOUR ORIGINAL SIGNALS =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = f"<body style='background:{BG};color:white'><h1>🔐 SIGNALS</h1>"

    for r in rows:
        out += f"""
        <div style='background:{CARD};margin:10px;padding:15px;border-radius:12px'>
            📊 {r['symbol']}<br>
            📥 Entry: {r['entry']}<br>
            🎯 TP: {r['tp']}<br>
            🛑 SL: {r['sl']}
        </div>
        """

    return out + "</body>"


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
