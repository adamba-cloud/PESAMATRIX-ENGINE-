import os, sqlite3, uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= UI =================
BG="#0b1220"; CARD="#111a2e"; BLUE="#38bdf8"; WHITE="white"; GREEN="#22c55e"

def layout(c):
    nav = f"""
    <div style='background:#0d1730;padding:10px;text-align:center'>
        <a href='/' style='color:white;margin:8px'>Home</a>
        <a href='/signals' style='color:white;margin:8px'>Signals</a>
        <a href='/news' style='color:white;margin:8px'>News</a>
        <a href='/videos' style='color:white;margin:8px'>Videos</a>
        <a href='/images' style='color:white;margin:8px'>Images</a>
        <a href='/subscribe' style='color:white;margin:8px'>Subscribe</a>
    </div>
    """
    return f"<body style='margin:0;background:{BG};color:{WHITE};font-family:Arial'>{nav}{c}</body>"

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

    cur.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY,
        phone TEXT,
        amount TEXT,
        mpesa_code TEXT,
        plan TEXT,
        status TEXT,
        date TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY,
        code TEXT,
        ip TEXT,
        device TEXT,
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
@app.route("/")
def home():
    conn=db(); cur=conn.cursor()

    # Latest signals
    signals=cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 3").fetchall()

    # Latest media
    media=cur.execute("SELECT * FROM media ORDER BY id DESC LIMIT 2").fetchall()

    conn.close()

    signal_html=""
    for s in signals:
        signal_html+=f"""
        <div style='padding:10px;border-bottom:1px solid #1e293b'>
        {s['symbol']} | {s['status']}<br>
        Entry:{s['entry']} TP:{s['tp']} SL:{s['sl']}
        </div>
        """

    media_html=""
    for m in media:
        if m["filename"]:
            media_html+=f"<img src='/static/uploads/{m['filename']}' width='100%'>"
        elif m["link"]:
            media_html+=f"<iframe src='{m['link']}' width='100%' height='200'></iframe>"

    return layout(f"""

    <!-- 🔴 ALERT BAR -->
    <div style='background:red;text-align:center;padding:8px'>
    🔥 LIVE SIGNAL RUNNING NOW • JOIN VIP TODAY
    </div>

    <!-- HERO -->
    <div style='text-align:center;padding:30px'>
        <h1 style='color:{BLUE};font-size:45px'>PESAMATRIX AI</h1>
        <p>Forex Signals • AI Trading • Smart Profits</p>

        <p>
        📞 <a href='tel:+254781585319' style='color:{BLUE}'>+254781585319</a> /
        <a href='tel:+254717434943' style='color:{BLUE}'>+254717434943</a>
        </p>

        <p>
        <a href='/register' style='color:{BLUE}'>Register</a> |
        <a href='/login' style='color:{BLUE}'>Login</a> |
        <a href='/admin' style='color:{BLUE}'>Admin</a>
        </p>
    </div>

    <!-- 📊 STATS -->
    {card(f"""
    <div style='display:grid;grid-template-columns:1fr 1fr 1fr;text-align:center'>
        <div>🔥 Win Rate<br><b>87%</b></div>
        <div>👥 Traders<br><b>1200+</b></div>
        <div>📊 Signals Today<br><b>{len(signals)}</b></div>
    </div>
    """)}

    <!-- 🤖 AI ANALYSIS -->
    {card("""
    <b>🤖 AI MARKET ANALYSIS</b><br><br>
    GOLD: BUY (92%)<br>
    EURUSD: SELL (87%)<br>
    GBPUSD: BUY (81%)
    """)}

    <!-- 📊 SIGNAL PREVIEW -->
    {card(f"""
    <b>🔥 LATEST SIGNALS</b><br><br>
    {signal_html}
    """)}

    <!-- 🎥 MEDIA -->
    {card(f"""
    <b>📺 LIVE MARKET CONTENT</b><br><br>
    {media_html}
    """)}

    <!-- 💎 CTA -->
    {card(f"""
    <h2 style='text-align:center;color:gold'>💎 VIP SIGNALS ACTIVE</h2>
    <p style='text-align:center'>Join now and start earning from forex signals</p>
    {button("🚀 SUBSCRIBE NOW","/subscribe")}
    """)}

    <!-- NAV GRID -->
    <div style='display:grid;grid-template-columns:1fr 1fr'>
        {card(button("📊 Signals","/signals"))}
        {card(button("📰 News","/news"))}
        {card(button("🎥 Videos","/videos"))}
        {card(button("🖼 Images","/images"))}
        {card(button("👤 Dashboard","/dashboard"))}
        {card(button("💳 Subscribe","/subscribe"))}
    </div>
    """)

# ================= REGISTER =================
@app.route("/register", methods=["POST","GET"])
def register():
    if request.method=="POST":
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                    (request.form["name"],request.form["phone"],"", "", "free"))
        conn.commit(); conn.close()
        return redirect("/login")

    return layout(header("REGISTER")+"""
    <form method="POST">
    Name:<input name="name"><br>
    Phone:<input name="phone"><br>
    <button>Create</button>
    </form>
    """)

# ================= LOGIN =================
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        code=request.form["code"]

        conn=db(); cur=conn.cursor()
        c=cur.execute("SELECT * FROM codes WHERE code=?", (code,)).fetchone()

        if not c:
            return layout(header("INVALID")+card("Wrong code"))

        if datetime.now() > datetime.fromisoformat(c["expiry"]):
            return layout(header("EXPIRED")+card("Code expired"))

        # TRACK
        cur.execute("INSERT INTO logs VALUES(NULL,?,?,?,?)",
                    (code,request.remote_addr,
                     request.headers.get("User-Agent"),
                     str(datetime.now())))

        conn.commit(); conn.close()

        session["code"]=code
        return redirect("/dashboard")

    return layout(header("LOGIN")+"""
    <form method="POST">
    Code:<input name="code"><br>
    <button>Login</button>
    </form>
    """)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    u=get_user()
    if not u: return redirect("/login")

    return layout(header("DASHBOARD")+
        card(f"Plan:{u['plan']}<br>Expiry:{u['expiry']}")
    )

# ================= SUBSCRIBE =================
@app.route("/subscribe", methods=["POST","GET"])
def subscribe():
    if request.method=="POST":
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO payments VALUES(NULL,?,?,?,?,?,?)",
                    (request.form["phone"],request.form["amount"],
                     request.form["mpesa"],request.form["plan"],
                     "PENDING",str(datetime.now())))
        conn.commit(); conn.close()

        return layout(header("SUBMITTED")+card("Await admin approval"))

    return layout(header("SUBSCRIBE")+"""
    Paybill: 322372<br><br>

    <form method="POST">
    Phone:<input name="phone"><br>
    Amount:<input name="amount"><br>
    Mpesa Code:<input name="mpesa"><br>

    <select name="plan">
    <option value="daily">Daily</option>
    <option value="weekly">Weekly</option>
    <option value="monthly">Monthly</option>
    </select><br>

    <button>Submit</button>
    </form>
    """)

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    u=get_user()
    if not u:
        return layout(header("LOCKED")+card("Subscribe to access"))

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("SIGNALS")
    for r in rows:
        out+=card(f"{r['symbol']} | Entry:{r['entry']} TP:{r['tp']} SL:{r['sl']} | {r['status']}")
    return layout(out)

# ================= NEWS =================
@app.route("/news")
def news():
    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    conn.close()

    out=header("NEWS")
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

    return layout(header("ADMIN")+
        button("Payments","/admin/payments")+
        button("Logs","/admin/logs")+
        button("Trades","/admin/manage_trades")+
        button("Add Signal","/admin/add_trade")+
        button("Media","/admin/media")+
        button("News","/admin/news")
    )

# ================= ADMIN PAYMENTS =================
@app.route("/admin/payments", methods=["POST","GET"])
def admin_payments():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()

    if request.method=="POST":
        pid=request.form["id"]
        plan=request.form["plan"]

        days={"daily":1,"weekly":7,"monthly":30}[plan]
        expiry=(datetime.now()+timedelta(days=days)).isoformat()
        code=str(uuid.uuid4())[:6]

        cur.execute("UPDATE payments SET status='APPROVED' WHERE id=?", (pid,))
        cur.execute("INSERT INTO codes VALUES(NULL,?,?,?,0)", (code,plan,expiry))

        conn.commit()

    rows=cur.execute("SELECT * FROM payments WHERE status='PENDING'").fetchall()
    conn.close()

    out=header("PAYMENTS")
    for p in rows:
        out+=card(f"""
        {p['phone']} | {p['amount']}<br>
        Mpesa:{p['mpesa_code']}<br>
        <form method="POST">
        <input type="hidden" name="id" value="{p['id']}">
        <input type="hidden" name="plan" value="{p['plan']}">
        <button>Approve</button>
        </form>
        """)
    return layout(out)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
