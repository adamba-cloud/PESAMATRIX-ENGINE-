import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
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
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
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

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contact TEXT,
    created_at TEXT
)
""")

conn.commit()

# ---------------- TRADE LOGIC ----------------
def execute_trade(symbol, side, entry, sl, tp):
    return {
        "symbol": symbol,
        "side": side,
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "status": "ACTIVE"
    }

# ---------------- CLASSIFY STATUS ----------------
def trade_status(expiry):
    if not expiry:
        return "UNKNOWN"
    if datetime.now() > datetime.fromisoformat(expiry):
        return "EXPIRED"
    return "ACTIVE"


# =====================================================
# 🌍 PUBLIC LANDING PAGE
# =====================================================
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
        <p>We provide real-time forex & crypto trading signals.</p>
    </div>

    <div class="section">
        <h2>Contacts</h2>
        <p>📞 +254 700 000 000</p>
        <p>📧 support@pesamatrix.com</p>
        <p>🌐 Instagram | Telegram | Twitter</p>
    </div>

    <div class="section">
        <h2>Services</h2>
        <p>🎥 Free Trading Videos</p>
        <p>📰 Trading News (Open)</p>
        <p>🔐 Premium Signals (Locked)</p>
        <a href="/access">Unlock Premium</a>
    </div>

    <div class="section">
        <h2>Sign In</h2>
        <form action="/register" method="post">
            <input name="name" placeholder="Name"><br><br>
            <input name="contact" placeholder="Phone or Email"><br><br>
            <button>Join</button>
        </form>
    </div>

    </body>
    </html>
    """)

# =====================================================
# 👤 USER REGISTRATION
# =====================================================
@app.route("/register", methods=["POST"])
def register():
    cur.execute("INSERT INTO users (name, contact, created_at) VALUES (?, ?, ?)",
                (request.form["name"], request.form["contact"], datetime.now().isoformat()))
    conn.commit()
    return redirect("/public")

# =====================================================
# 🔐 ACCESS PAGE (LOCKED SIGNALS)
# =====================================================
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
    <h2>🔐 Premium Access</h2>
    <form method='post'>
        <input name='code' placeholder='Enter code'>
        <button>Unlock</button>
    </form>
    """

# =====================================================
# 📊 SIGNALS (LOCKED)
# =====================================================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()

    html = "<h1>📊 PREMIUM SIGNALS</h1>"

    for r in rows:
        status = trade_status(r[7])
        html += f"""
        <div style='background:#1e293b;color:white;margin:10px;padding:10px'>
            <b>{r[1]}</b> {r[2]}<br>
            Entry: {r[3]} | SL: {r[4]} | TP: {r[5]}<br>
            Status: {status}
        </div>
        """

    return html

# =====================================================
# 📢 ADMIN DASHBOARD
# =====================================================
@app.route("/admin")
def admin():
    return render_template_string("""
    <h1>ADMIN DASHBOARD</h1>

    <form action="/trade" method="post">
        <input name="symbol" placeholder="Symbol"><br>
        <input name="side"><br>
        <input name="entry"><br>
        <input name="sl"><br>
        <input name="tp"><br>
        <button>Send Signal</button>
    </form>

    <a href="/generate">Generate Code</a>
    """)

# =====================================================
# 📡 TRADE POST
# =====================================================
@app.route("/trade", methods=["POST"])
def trade():
    data = request.form
    now = datetime.now()
    expiry = now + timedelta(hours=4)

    result = execute_trade(
        data["symbol"], data["side"], data["entry"], data["sl"], data["tp"]
    )

    cur.execute("""
        INSERT INTO trades
        (symbol, side, entry, sl, tp, status, created_at, expiry_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["symbol"], result["side"], result["entry"],
        result["sl"], result["tp"], "ACTIVE",
        now.isoformat(), expiry.isoformat()
    ))

    conn.commit()
    return redirect("/admin")

# =====================================================
# 🧾 GENERATE ACCESS CODE
# =====================================================
@app.route("/generate")
def generate():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute("INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
                (code, expiry.isoformat()))
    conn.commit()

    return f"CODE: {code}"

# =====================================================
# 🔥 LIVE API
# =====================================================
@app.route("/api/live")
def api():
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 10")
    trades = cur.fetchall()

    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 10")
    posts = cur.fetchall()

    return jsonify({"trades": trades, "posts": posts})

# =====================================================
# START
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
