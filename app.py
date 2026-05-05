import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

# ================= ADMIN SECURITY =================
ADMIN_PASSWORD = "admin123"

# ================= DATABASE =================
conn = sqlite3.connect("trades.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,
    entry REAL,
    sl REAL,
    tp REAL,
    status TEXT,
    created_at TEXT,
    expiry_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS access_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    expiry_date TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contact TEXT,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    media_url TEXT,
    created_at TEXT
)
""")

conn.commit()


# ================= TRADE LOGIC =================
def execute_trade(symbol, side, entry, sl, tp):
    return {
        "symbol": symbol,
        "side": side,
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "status": "UPCOMING"
    }


def trade_status(expiry, manual_status=None):
    if manual_status:
        return manual_status

    try:
        exp = datetime.fromisoformat(expiry)
        now = datetime.now()

        if now > exp:
            return "EXPIRED"
        elif now < exp - timedelta(hours=4):
            return "UPCOMING"
        else:
            return "ACTIVE"
    except:
        return "UNKNOWN"


# ================= ROOT =================
@app.route("/")
def root():
    return redirect("/public")


# ================= PUBLIC PAGE =================
@app.route("/public")
def public():
    return render_template_string("""
    <html>
    <head>
        <title>PESAMATRIX</title>
        <style>
            body { font-family: Arial; background:#0f172a; color:white; margin:0; }
            .section { padding:40px; border-bottom:1px solid #1e293b; }
            a { color:#38bdf8; }
        </style>
    </head>
    <body>

    <div class="section">
        <h1>🚀 PESAMATRIX</h1>
        <p>Smart Trading Signal Platform</p>
    </div>

    <div class="section">
        <h2>About</h2>
        <p>We provide forex & crypto trading signals in real time.</p>
    </div>

    <div class="section">
        <h2>Contacts</h2>
        <p>📞 +254 700 000 000</p>
        <p>📧 support@pesamatrix.com</p>
        <p>📱 Telegram | Instagram | Twitter</p>
    </div>

    <div class="section">
        <h2>Services</h2>
        <p>🎥 Videos (Open)</p>
        <p>📰 Trading News (Open)</p>
        <p>🔐 Premium Signals (Locked)</p>
        <a href="/access">Unlock Signals</a>
    </div>

    <div class="section">
        <h2>Sign In</h2>
        <form action="/register" method="post">
            <input name="name" placeholder="Name"><br><br>
            <input name="contact" placeholder="Phone or Email"><br><br>
            <button>Join</button>
        </form>
    </div>

    <div class="section">
        <a href="/login">Admin Login</a>
    </div>

    </body>
    </html>
    """)


# ================= USER REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    cur.execute(
        "INSERT INTO users (name, contact, created_at) VALUES (?, ?, ?)",
        (request.form["name"], request.form["contact"], datetime.now().isoformat())
    )
    conn.commit()
    return redirect("/public")


# ================= ADMIN LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password ❌"

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input name="password" placeholder="Password">
        <button>Login</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= BEAUTIFUL ADMIN DASHBOARD =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cur.fetchall()

    return render_template_string("""
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body { margin:0; font-family:Arial; background:#0f172a; color:white; }
            .sidebar { width:220px; height:100vh; background:#111827; position:fixed; padding:20px; }
            .sidebar a { display:block; color:#38bdf8; margin:10px 0; text-decoration:none; }
            .main { margin-left:240px; padding:20px; }
            .card { background:#1e293b; padding:15px; margin-bottom:15px; border-radius:10px; }
            input, select, button {
                width:100%; padding:10px; margin-top:5px;
                border-radius:6px; border:none;
            }
            button { background:#22c55e; color:white; }
            .trade { background:#111827; padding:10px; margin-top:10px; border-radius:8px; }
        </style>
    </head>
    <body>

    <div class="sidebar">
        <h2>ADMIN</h2>
        <a href="/admin">Dashboard</a>
        <a href="/logout">Logout</a>
        <a href="/generate">Generate Code</a>
    </div>

    <div class="main">

        <div class="card">
            <h3>Create Trade</h3>
            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol">
                <input name="side" placeholder="BUY / SELL">
                <input name="entry" placeholder="Entry">
                <input name="sl" placeholder="SL">
                <input name="tp" placeholder="TP">
                <button>Create Trade</button>
            </form>
        </div>

        <div class="card">
            <h3>Live Trades</h3>
            {% for t in trades %}
            <div class="trade">
                <b>{{t[1]}}</b> {{t[2]}}<br>
                Entry: {{t[3]}} SL: {{t[4]}} TP: {{t[5]}}<br>
                Status: {{t[6]}}
            </div>
            {% endfor %}
        </div>

    </div>

    </body>
    </html>
    """, trades=trades)


# ================= TRADE CREATE =================
@app.route("/trade", methods=["POST"])
def trade():
    data = request.form
    now = datetime.now()
    expiry = now + timedelta(hours=4)

    cur.execute("""
        INSERT INTO trades 
        (symbol, side, entry, sl, tp, status, created_at, expiry_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["symbol"],
        data["side"],
        float(data["entry"]),
        float(data["sl"]),
        float(data["tp"]),
        "ACTIVE",
        now.isoformat(),
        expiry.isoformat()
    ))

    conn.commit()
    return redirect("/admin")


# ================= ACCESS SYSTEM =================
@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        result = cur.fetchone()

        if result and datetime.now() < datetime.fromisoformat(result[2]):
            session["access"] = True
            return redirect("/signals")

        return "Invalid code ❌"

    return """
    <h2>Access Signals</h2>
    <form method="post">
        <input name="code">
        <button>Unlock</button>
    </form>
    """


# ================= SIGNALS =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()

    html = "<h1>Premium Signals</h1>"

    for r in rows:
        html += f"""
        <div style='background:#1e293b;color:white;margin:10px;padding:10px'>
            {r[1]} {r[2]}<br>
            Entry: {r[3]} SL: {r[4]} TP: {r[5]}<br>
            Status: {r[6]}
        </div>
        """

    return html


# ================= CODE GENERATOR =================
@app.route("/generate")
def generate():
    if not session.get("admin"):
        return redirect("/login")

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute("INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
                (code, expiry.isoformat()))
    conn.commit()

    return f"ACCESS CODE: {code}"


# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
