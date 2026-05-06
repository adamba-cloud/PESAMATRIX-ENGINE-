import os, sqlite3, uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# UI
BG="#0b1220"; CARD="#111a2e"; BLUE="#38bdf8"; WHITE="white"

def layout(c): return f"<body style='margin:0;background:{BG};color:{WHITE};font-family:Arial'>{c}</body>"
def header(t): return f"<div style='background:{CARD};padding:20px;text-align:center'><h1 style='color:{BLUE}'>PESAMATRIX AI</h1><h2>{t}</h2></div>"
def card(c): return f"<div style='background:{CARD};padding:15px;margin:10px;border-radius:10px'>{c}</div>"
def button(t,u): return f"<a href='{u}' style='display:block;background:{BLUE};color:black;padding:10px;margin:5px;border-radius:8px;text-align:center'>{t}</a>"

# ================= DB =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn=db(); cur=conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT, phone TEXT,
        code TEXT,
        expiry TEXT,
        plan TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY,
        symbol TEXT, entry TEXT, tp TEXT, sl TEXT, status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS media(
        id INTEGER PRIMARY KEY,
        filename TEXT, link TEXT, type TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS codes(
        id INTEGER PRIMARY KEY,
        code TEXT,
        plan TEXT,
        expiry TEXT,
        used INTEGER DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY,
        title TEXT,
        content TEXT,
        date TEXT
    )""")

    conn.commit(); conn.close()

init()

# ================= USER CHECK =================
def get_user():
    code=session.get("code")
    if not code: return None

    conn=db(); cur=conn.cursor()
    c=cur.execute("SELECT * FROM codes WHERE code=?", (code,)).fetchone()
    conn.close()

    if not c: return None
    if datetime.now() > datetime.fromisoformat(c["expiry"]): return None

    return c

# ================= HOME =================
@app.route("/")
def home():
    return layout(f"""
    <div style='text-align:center;padding:40px'>
        <h1 style='color:{BLUE};font-size:45px'>PESAMATRIX AI</h1>
        <p>Forex Signals • AI Trading</p>

        <p>📞 <a href='tel:+254781585319'>+254781585319</a> /
        <a href='tel:+254717434943'>+254717434943</a></p>

        <a href='/register'>Register</a> | <a href='/login'>Login</a> | <a href='/admin'>Admin</a>
    </div>

    {card("AI powered forex signals")}

    <div style='display:grid;grid-template-columns:1fr 1fr'>
        {card(button("📊 Signals","/signals"))}
        {card(button("📰 News","/news"))}
        {card(button("🎥 Videos","/videos"))}
        {card(button("🖼 Images","/images"))}
        {card(button("👤 Dashboard","/dashboard"))}
        {card(button("💳 Subscribe","/subscribe"))}
    </div>
    """)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    u=get_user()
    if not u: return redirect("/login")

    return layout(header("DASHBOARD")+
        card(f"""
        Plan: {u['plan']}<br>
        Expiry: {u['expiry']}
        """)
    )

# ================= SUBSCRIBE =================
@app.route("/subscribe")
def subscribe():
    return layout(header("SUBSCRIBE")+
        card("""
        PAY VIA M-PESA<br><br>
        Paybill: <b>322372</b><br>
        Account: <b>Your Phone Number</b><br><br>
        After paying, click below
        """)+
        button("I HAVE PAID - DAILY","/pay/daily")+
        button("I HAVE PAID - WEEKLY","/pay/weekly")+
        button("I HAVE PAID - MONTHLY","/pay/monthly")
    )

@app.route("/pay/<plan>")
def pay(plan):
    days={"daily":1,"weekly":7,"monthly":30}[plan]
    expiry=(datetime.now()+timedelta(days=days)).isoformat()

    code=str(uuid.uuid4())[:6]

    conn=db(); cur=conn.cursor()
    cur.execute("INSERT INTO codes VALUES(NULL,?,?,?,0)",
                (code,plan,expiry))
    conn.commit(); conn.close()

    return layout(header("YOUR ACCESS CODE")+f"<h2>{code}</h2>")

# ================= LOGIN =================
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        code=request.form["code"]

        conn=db(); cur=conn.cursor()
        c=cur.execute("SELECT * FROM codes WHERE code=?", (code,)).fetchone()
        conn.close()

        if not c:
            return layout(header("INVALID")+card("Wrong code"))

        if datetime.now() > datetime.fromisoformat(c["expiry"]):
            return layout(header("EXPIRED")+card("Code expired"))

        session["code"]=code
        return redirect("/dashboard")

    return layout(header("LOGIN")+"""
    <form method="POST">
    Code:<input name="code"><br>
    <button>Login</button>
    </form>
    """)

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    u=get_user()
    if not u:
        return layout(header("LOCKED")+card("Login & Subscribe"))

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("SIGNALS")
    for r in rows:
        out+=card(f"{r['symbol']} | {r['status']}")
    return layout(out)

# ================= MEDIA =================
@app.route("/images")
def images():
    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM media WHERE type='image'").fetchall()
    conn.close()

    out=header("IMAGES")
    for m in rows:
        out+=card(f"<img src='/static/uploads/{m['filename']}' width='100%'>")
    return layout(out)

@app.route("/videos")
def videos():
    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM media WHERE type='video'").fetchall()
    conn.close()

    out=header("VIDEOS")
    for m in rows:
        if m["filename"]:
            out+=card(f"<video controls width='100%'><source src='/static/uploads/{m['filename']}'></video>")
        elif m["link"]:
            out+=card(f"<iframe src='{m['link']}' width='100%' height='300'></iframe>")
    return layout(out)

# ================= NEWS =================
@app.route("/news")
def news_page():
    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    conn.close()

    out=header("FOREX NEWS")
    for n in rows:
        out+=card(f"<b>{n['title']}</b><br>{n['content']}")
    return layout(out)

# ================= ADMIN =================
@app.route("/admin", methods=["POST","GET"])
def admin():
    if request.method=="POST":
        if request.form["pass"]=="admin123":
            session["admin"]=True

    if not session.get("admin"):
        return layout(header("ADMIN LOGIN")+"""
        <form method="POST"><input name="pass"><button>Login</button></form>
        """)

    return layout(header("ADMIN DASHBOARD")+
        button("Manage Trades","/admin/manage_trades")+
        button("Add Signal","/admin/add_trade")+
        button("Media","/admin/media")+
        button("News","/admin/news")
    )

# ================= ADD TRADE =================
@app.route("/admin/add_trade", methods=["POST","GET"])
def add_trade():
    if not session.get("admin"): return redirect("/admin")

    if request.method=="POST":
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
                    (request.form["symbol"],request.form["entry"],
                     request.form["tp"],request.form["sl"],"UPCOMING"))
        conn.commit(); conn.close()
        return redirect("/admin")

    return layout(header("ADD SIGNAL")+"""
    <form method="POST">
    Symbol:<input name="symbol"><br>
    Entry:<input name="entry"><br>
    TP:<input name="tp"><br>
    SL:<input name="sl"><br>
    <button>Add</button>
    </form>
    """)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
