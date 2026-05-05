import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, make_response

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= UI =================
BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"

STYLE = f"margin:0;font-family:Arial;background:{BG};color:white"

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        code TEXT UNIQUE,
        role TEXT,
        trial_end TEXT,
        created_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        entry TEXT,
        sl TEXT,
        tp TEXT,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS media(
        id INTEGER PRIMARY KEY,
        filename TEXT,
        type TEXT
    )""")

    conn.commit()
    conn.close()

init()

# ================= AUTH =================
def get_user():
    code = session.get("code") or request.cookies.get("code")
    if not code:
        return None

    conn = db()
    cur = conn.cursor()
    user = cur.execute("SELECT * FROM users WHERE code=?", (code,)).fetchone()
    conn.close()

    if user:
        session["code"] = code
        return dict(user)

    return None

def is_admin():
    return session.get("admin") == True

# ================= UI HELPERS =================
def header(title):
    return f"""
    <div style="background:{CARD};padding:20px;text-align:center">
        <h1 style="color:{BLUE}">PESAMATRIX</h1>
        <h2>{title}</h2>
    </div>
    """

def card(content):
    return f"<div style='background:{CARD};padding:15px;margin:10px;border-radius:12px'>{content}</div>"

def button(txt, link):
    return f"<a href='{link}' style='background:{BLUE};padding:10px;color:black;border-radius:8px;text-decoration:none'>{txt}</a>"

# =====================================================
# 🟦 LANDING PAGE (BUSY SAAS)
# =====================================================
@app.route("/")
def home():
    return f"""
    <body style="{STYLE}">

    <div style="padding:60px;text-align:center">
        <h1 style="color:{BLUE};font-size:50px">PESAMATRIX AI</h1>
        <p>Forex Signals • AI Trading • Automation • Analytics</p>

        <br>
        {button("Get Started","/register")}
        {button("Login","/login")}
        <a href="/admin" style="color:{BLUE};margin-left:10px">Admin</a>
    </div>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:20px">
        {card("📊 Live Signals")}
        {card("📡 AI Market Analysis")}
        {card("💰 High Accuracy Trades")}
        {card("🎥 Trading Videos")}
        {card("📰 Market News")}
        {card("🔐 Premium Signals")}
    </div>

    {card("<h3 style='color:#38bdf8'>ABOUT US</h3>We provide professional trading signals and automation tools.")}

    {card("""
    <h3 style='color:#38bdf8'>CONTACT</h3>
    <a href='tel:+254781585319' style='color:#38bdf8'>Call</a><br>
    <a href='https://tiktok.com/@smartgoldsignals' style='color:#38bdf8'>TikTok</a>
    """)}

    {card("""
    <h3 style='color:#38bdf8'>PAYMENTS</h3>
    Mpesa Paybill: <b>322372</b><br>
    Account: Your Code
    """)}

    </body>
    """

# =====================================================
# 🟩 REGISTER
# =====================================================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        code = str(uuid.uuid4())[:8].upper()

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?,?)",
        (request.form["name"],
         request.form["phone"],
         code,
         "user",
         (datetime.now()+timedelta(days=3)).isoformat(),
         datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return f"<body style='{STYLE}'>{header('ACCOUNT CREATED')}<h1>{code}</h1><a href='/login'>Login</a></body>"

    return f"""
    <body style="{STYLE}">
    {header("REGISTER")}
    <form method="POST">
    Name:<input name="name"><br>
    Phone:<input name="phone"><br>
    <button>Create</button>
    </form>
    </body>
    """

# =====================================================
# 🟩 LOGIN (PERSISTENT)
# =====================================================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        user = cur.execute("SELECT * FROM users WHERE code=?",(request.form["code"],)).fetchone()
        conn.close()

        if user:
            session["code"] = user["code"]
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie("code", user["code"], max_age=60*60*24*30)
            return resp

    return f"<body style='{STYLE}'>{header('LOGIN')}<form method='POST'>Code:<input name='code'><button>Login</button></form></body>"

# =====================================================
# 🟩 DASHBOARD
# =====================================================
@app.route("/dashboard")
def dashboard():
    u = get_user()
    if not u:
        return redirect("/login")

    status = "ACTIVE" if datetime.now() < datetime.fromisoformat(u["trial_end"]) else "EXPIRED"

    return f"""
    <body style="{STYLE}">
    {header("USER DASHBOARD")}
    {card(f"Name:{u['name']}<br>Code:{u['code']}<br>Status:{status}")}

    {card(button("View Signals","/signals"))}
    {card(button("Media","/media"))}

    </body>
    """

# =====================================================
# 🔐 SIGNAL LOCK
# =====================================================
@app.route("/signals")
def signals():
    u = get_user()
    if not u:
        return redirect("/login")

    if datetime.now() > datetime.fromisoformat(u["trial_end"]):
        return f"<body style='{STYLE}'>{header('🔒 LOCKED')}Please Pay via Mpesa</body>"

    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out = f"<body style='{STYLE}'>{header('SIGNALS')}"
    for r in rows:
        out += card(f"{r['symbol']} | {r['entry']} | {r['tp']} | {r['sl']} | {r['status']}")
    return out+"</body>"

# =====================================================
# 🟥 ADMIN
# =====================================================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")

    if not is_admin():
        return f"<body style='{STYLE}'>{header('ADMIN LOGIN')}<form method='POST'><input name='password'><button>Login</button></form></body>"

    conn = db()
    cur = conn.cursor()
    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trades = cur.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    media = cur.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    conn.close()

    return f"""
    <body style="{STYLE}">
    {header("ADMIN DASHBOARD")}

    {card(f"Users:{users} | Trades:{trades} | Media:{media}")}

    <a href="/admin/trade">Create Trade</a><br>
    <a href="/admin/upload">Upload Media</a>

    </body>
    """

# =====================================================
# TRADE CREATE
# =====================================================
@app.route("/admin/trade", methods=["GET","POST"])
def trade():
    if not is_admin():
        return redirect("/admin")

    if request.method=="POST":
        conn=db();cur=conn.cursor()
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
        (request.form["symbol"],request.form["entry"],request.form["sl"],request.form["tp"],request.form["status"]))
        conn.commit();conn.close()
        return redirect("/admin")

    return "<form method='POST'>Symbol<input name='symbol'><br>Entry<input name='entry'><br>SL<input name='sl'><br>TP<input name='tp'><br>Status<input name='status'><button>Create</button></form>"

# =====================================================
# MEDIA UPLOAD (FIXED)
# =====================================================
@app.route("/admin/upload", methods=["GET","POST"])
def upload():
    if not is_admin():
        return redirect("/admin")

    if request.method=="POST":
        f=request.files["file"]
        path=os.path.join(UPLOAD_FOLDER,f.filename)
        f.save(path)

        conn=db();cur=conn.cursor()
        cur.execute("INSERT INTO media VALUES(NULL,?,?)",(f.filename,"image"))
        conn.commit();conn.close()

    return "<form method='POST' enctype='multipart/form-data'><input type='file' name='file'><button>Upload</button></form>"

@app.route("/media")
def media():
    conn=db();cur=conn.cursor()
    rows=cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out=f"<body style='{STYLE}'>{header('MEDIA')}"
    for m in rows:
        out+=f"<img src='/static/uploads/{m['filename']}' width='300'><br>"
    return out

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
