import os, sqlite3, hashlib, random
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
# UI STYLE (GLOBAL THEME)
# =========================
def layout(title, content):
    return f"""
    <html>
    <head>
    <title>{title}</title>
    </head>

    <body style="margin:0;background:#0b1220;color:white;font-family:Arial">

    <div style="background:#111a2e;padding:15px;text-align:center">
        <h2 style="color:#38bdf8">📊 PESAMATRIX PRO</h2>
        <a href="/" style="color:white;margin:10px">Home</a>
        <a href="/login" style="color:white;margin:10px">Login</a>
        <a href="/register" style="color:white;margin:10px">Register</a>
        <a href="/dashboard" style="color:white;margin:10px">Dashboard</a>
    </div>

    <div style="padding:20px">
    {content}
    </div>

    <hr>

    <div style="text-align:center;padding:20px;background:#111a2e">
        📞 <a href="tel:+254781585319" style="color:#38bdf8">+254781585319</a> |
        <a href="tel:+254717434943" style="color:#38bdf8">+254717434943</a>
        <br><br>

        🎵 <a href="https://tiktok.com/@smartgoldsignals" target="_blank" style="color:#38bdf8">
        @smartgoldsignals</a>

        <br><br>
        💰 Paybill: <b>322372</b> <br>
        Account: <b>Your Login Account Number</b>
    </div>

    </body>
    </html>
    """

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return layout("Home",
    "<h1>Welcome to PESAMATRIX PRO</h1><p>Trading Signals Platform</p>")

# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect(DB)
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
        f"<h2>Registered!</h2><p>Your Account Number: <b>{acc}</b></p>")

    return layout("Register", """
    <h2>Register</h2>
    <form method="POST">
    Name:<br><input name="name"><br><br>
    Phone:<br><input name="phone"><br><br>
    Email:<br><input name="email"><br><br>
    Password:<br><input name="password" type="password"><br><br>
    <button>Register</button>
    </form>
    """)

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        u = cur.execute("""
        SELECT * FROM users WHERE phone=? AND password=?
        """, (request.form["phone"], hash_pw(request.form["password"]))).fetchone()

        if u:
            session["user_id"] = u[0]
            session["role"] = u[5]
            session["account"] = u[7]
            return redirect("/dashboard")

        return layout("Error","<h2>Invalid login</h2>")

    return layout("Login", """
    <h2>Login</h2>
    <form method="POST">
    Phone:<br><input name="phone"><br><br>
    Password:<br><input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    """)

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return layout("Dashboard",
    f"""
    <h2>Welcome User</h2>

    <div style="background:#111a2e;padding:10px">
        Account: <b>{session['account']}</b><br>
        Role: {session['role']}
    </div>

    <br>
    <a href="/signals" style="color:#38bdf8">View Signals</a><br>
    <a href="/payments" style="color:#38bdf8">Payments</a><br>
    <a href="/logout" style="color:red">Logout</a>
    """)

# =========================
# SIGNALS
# =========================
@app.route("/signals")
def signals():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM signals").fetchall()

    out = "<h2>📊 SIGNALS</h2>"

    for r in rows:
        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px">
        {r[1]} | Entry: {r[2]} | TP: {r[3]} | SL: {r[4]} | {r[5]}
        </div>
        """

    return layout("Signals", out)

# =========================
# PAYMENTS (USER VIEW)
# =========================
@app.route("/payments")
def payments():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM payments").fetchall()

    out = "<h2>💳 PAYMENTS</h2>"

    for r in rows:
        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px">
        {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}
        </div>
        """

    return layout("Payments", out)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
