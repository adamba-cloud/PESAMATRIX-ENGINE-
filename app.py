import os, sqlite3, hashlib, random, requests
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

DB = "app.db"

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        email TEXT,
        password TEXT,
        role TEXT,
        status TEXT,
        account_number TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY,
        phone TEXT,
        mpesa_code TEXT,
        amount TEXT,
        plan TEXT,
        status TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS signals(
        id INTEGER PRIMARY KEY,
        asset TEXT,
        entry TEXT,
        tp TEXT,
        sl TEXT,
        status TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# =========================
# TELEGRAM (OPTIONAL)
# =========================
TELEGRAM_TOKEN = ""
CHAT_ID = ""

def send_telegram(msg):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# UI STYLE
# =========================
def layout(title, content):
    return f"""
    <html>
    <body style="margin:0;background:#0b1220;color:white;font-family:Arial">

    <div style="background:#111a2e;padding:15px;text-align:center">
        <h2 style="color:#38bdf8">📊 PESAMATRIX PRO</h2>

        <a href="/" style="color:white;margin:10px">Home</a>
        <a href="/login" style="color:white;margin:10px">Login</a>
        <a href="/register" style="color:white;margin:10px">Register</a>
        <a href="/dashboard" style="color:white;margin:10px">Dashboard</a>
        <a href="/admin" style="color:#facc15;margin:10px">Admin</a>
    </div>

    <div style="padding:20px">{content}</div>

    <div style="text-align:center;padding:20px;background:#111a2e">
        📞 <a href="tel:+254781585319" style="color:#38bdf8">+254781585319</a> |
        <a href="tel:+254717434943" style="color:#38bdf8">+254717434943</a>
        <br><br>

        🎵 <a href="https://tiktok.com/@smartgoldsignals" target="_blank" style="color:#38bdf8">
        @smartgoldsignals</a>

        <br><br>
        💰 Paybill: <b>322372</b><br>
        Account: <b>Your Login Account Number</b>
    </div>

    </body>
    </html>
    """

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def db():
    return sqlite3.connect(DB)

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return layout("Home", "<h1>Welcome to PESAMATRIX PRO</h1>")

# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()

        acc = str(random.randint(100000,999999))

        cur.execute("""
        INSERT INTO users(name,phone,email,password,role,status,account_number)
        VALUES(?,?,?,?,?,?,?)
        """, (
            request.form["name"],
            request.form["phone"],
            request.form["email"],
            hash_pw(request.form["password"]),
            "user",
            "inactive",
            acc
        ))

        conn.commit()
        conn.close()

        return layout("Success",
        f"<h2>Registered!</h2><p>Account Number: <b>{acc}</b></p>")

    return layout("Register", """
    <form method="POST">
    Name:<input name="name"><br>
    Phone:<input name="phone"><br>
    Email:<input name="email"><br>
    Password:<input name="password" type="password"><br>
    <button>Register</button>
    </form>
    """)

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()

        u = cur.execute("""
        SELECT * FROM users WHERE phone=? AND password=?
        """, (request.form["phone"], hash_pw(request.form["password"]))).fetchone()

        if u:
            session["user_id"] = u[0]
            session["role"] = u[5]
            session["status"] = u[6]
            session["account"] = u[7]

            return redirect("/dashboard")

        return layout("Error","Invalid login")

    return layout("Login", """
    <form method="POST">
    Phone:<input name="phone"><br>
    Password:<input name="password" type="password"><br>
    <button>Login</button>
    </form>
    """)

# =========================
# DASHBOARD (USER)
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("status") != "active":
        return layout("Blocked","<h2>Your account is not activated yet</h2>")

    return layout("Dashboard", f"""
    <h2>Welcome</h2>
    Account: <b>{session['account']}</b><br>

    <a href="/signals" style="color:#38bdf8">Signals</a><br>
    <a href="/payments" style="color:#38bdf8">Payments</a><br>
    <a href="/logout" style="color:red">Logout</a>
    """)

# =========================
# SIGNALS (USER VIEW)
# =========================
@app.route("/signals")
def signals():
    conn = db()
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM signals").fetchall()

    out = "<h2>📊 SIGNALS</h2>"

    for r in rows:
        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px">
        {r[1]} | Entry {r[2]} | TP {r[3]} | SL {r[4]}
        </div>
        """

    return layout("Signals", out)

# =========================
# PAYMENTS (USER VIEW)
# =========================
@app.route("/payments")
def payments():
    conn = db()
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM payments").fetchall()

    out = "<h2>💳 PAYMENTS</h2>"

    for r in rows:
        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px">
        {r[1]} | {r[3]} | {r[4]} | {r[5]}
        </div>
        """

    return layout("Payments", out)

# =========================
# ADMIN LOGIN
# =========================
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["user"] == ADMIN_USER and request.form["pass"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin/dashboard")

    return """
    <h2>Admin Login</h2>
    <form method="POST">
    User:<input name="user"><br>
    Pass:<input name="pass" type="password"><br>
    <button>Login</button>
    </form>
    """

# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard")
def admin_dash():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    payments = cur.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    signals = cur.execute("SELECT COUNT(*) FROM signals").fetchone()[0]

    return f"""
    <h1>ADMIN DASHBOARD</h1>

    Users: {users}<br>
    Payments: {payments}<br>
    Signals: {signals}<br>

    <a href="/admin/payments">Payments</a><br>
    <a href="/admin/signals">Signals</a><br>
    """

# =========================
# APPROVE PAYMENT
# =========================
@app.route("/admin/approve", methods=["POST"])
def approve():
    if not session.get("admin"):
        return redirect("/admin")

    pid = request.form["id"]

    conn = db()
    cur = conn.cursor()

    phone = cur.execute("SELECT phone FROM payments WHERE id=?", (pid,)).fetchone()[0]

    cur.execute("UPDATE payments SET status='APPROVED' WHERE id=?", (pid,))
    cur.execute("UPDATE users SET status='active' WHERE phone=?", (phone,))

    conn.commit()
    conn.close()

    return redirect("/admin/payments")

# =========================
# ADMIN PAYMENTS
# =========================
@app.route("/admin/payments")
def admin_payments():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM payments").fetchall()

    out = "<h2>PAYMENTS</h2>"

    for r in rows:
        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px">
        {r[1]} | {r[3]} | {r[4]} | {r[5]}

        <form method="POST" action="/admin/approve">
        <input type="hidden" name="id" value="{r[0]}">
        <button>Approve</button>
        </form>

        </div>
        """

    return layout("Payments", out)

# =========================
# ADMIN SIGNALS
# =========================
@app.route("/admin/signals", methods=["GET","POST"])
def admin_signals():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    if request.method == "POST":
        asset = request.form["asset"]
        entry = request.form["entry"]
        tp = request.form["tp"]
        sl = request.form["sl"]

        cur.execute("""
        INSERT INTO signals(asset,entry,tp,sl,status)
        VALUES(?,?,?,?,?)
        """, (asset,entry,tp,sl,"LIVE"))

        conn.commit()

        send_telegram(f"NEW SIGNAL: {asset} {entry} {tp} {sl}")

    rows = cur.execute("SELECT * FROM signals").fetchall()

    out = """
    <h2>ADD SIGNAL</h2>
    <form method="POST">
    Asset:<input name="asset"><br>
    Entry:<input name="entry"><br>
    TP:<input name="tp"><br>
    SL:<input name="sl"><br>
    <button>Create</button>
    </form>
    <hr>
    """

    for r in rows:
        out += f"<div style='background:#111a2e;padding:10px'>{r[1]} {r[2]}</div>"

    return layout("Signals", out)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
