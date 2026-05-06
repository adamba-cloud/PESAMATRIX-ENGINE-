import os, sqlite3, uuid, requests
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= UI =================
BG="#0b1220"; CARD="#111a2e"; BLUE="#38bdf8"; WHITE="white"; GREEN="#22c55e"

def layout(c): return f"<body style='margin:0;background:{BG};color:{WHITE};font-family:Arial'>{c}</body>"
def header(t): return f"<div style='background:{CARD};padding:20px;text-align:center'><h1 style='color:{BLUE}'>PESAMATRIX</h1><h2>{t}</h2></div>"
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

    conn.commit(); conn.close()

init()

# ================= USER =================
def get_user():
    code=session.get("code")
    if not code: return None
    conn=db(); cur=conn.cursor()
    u=cur.execute("SELECT * FROM users WHERE code=?", (code,)).fetchone()
    conn.close()
    if not u: return None
    if datetime.now()>datetime.fromisoformat(u["expiry"]): return None
    return dict(u)

# ================= HOME =================
@app.route("/")
def home():
    return layout(f"""
    <div style='text-align:center;padding:40px'>
        <h1 style='color:{BLUE};font-size:45px'>PESAMATRIX AI</h1>
        <p>Forex Signals • AI Trading</p>

        <p>📞 Contact: +254781585319 / +254717434943</p>
        <p>🎵 TikTok: <a href='https://tiktok.com/@smartgoldsignals' target='_blank'>@smartgoldsignals</a></p>

        <a href='/register'>Register</a> | <a href='/login'>Login</a> | <a href='/admin'>Admin</a>
    </div>

    {card("<b>ABOUT US</b><br>Pesamatrix AI provides high-probability forex signals powered by smart trading strategies and AI analysis.")}

    <div style='display:grid;grid-template-columns:1fr 1fr'>
        {card(button("📊 Signals","/signals"))}
        {card(button("📰 News","/news"))}
        {card(button("🎥 Videos","/videos"))}
        {card(button("🖼 Images","/images"))}
        {card(button("👤 Dashboard","/dashboard"))}
        {card(button("💳 Subscribe","/subscribe"))}
    </div>
    """)

# ================= NEWS =================
@app.route("/news")
def news():
    return layout(header("FOREX NEWS")+card("Connect your News API"))

# ================= VIDEOS =================
@app.route("/videos")
def videos():
    return layout(header("VIDEOS") + card("""
    <iframe src="https://www.tiktok.com/embed/7230000000000000000"
    width="100%" height="400"></iframe>
    """))

# ================= IMAGES =================
@app.route("/images")
def images():
    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out=header("IMAGES")
    for m in rows:
        if m["filename"]:
            out+=card(f"<img src='/static/uploads/{m['filename']}' width='100%'>")
    return layout(out)

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        code=str(uuid.uuid4())[:6]
        expiry=(datetime.now()+timedelta(days=1)).isoformat()

        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                    (request.form["name"],request.form["phone"],code,expiry,"free"))
        conn.commit(); conn.close()

        return layout(header("YOUR CODE")+f"<h2>{code}</h2>")

    return layout(header("REGISTER")+"""
    <form method="POST">
    Name:<input name="name"><br>
    Phone:<input name="phone"><br>
    <button>Create</button>
    </form>
    """)

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        session["code"]=request.form["code"]
        return redirect("/dashboard")

    return layout(header("LOGIN")+"""
    <form method="POST">
    Code:<input name="code">
    <button>Login</button>
    </form>
    """)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    u=get_user()
    if not u: return redirect("/login")

    return layout(header("DASHBOARD")+
        card(f"""
        Name:{u['name']}<br>
        Plan:{u['plan']}<br>
        Expiry:{u['expiry']}
        """)+
        button("Upgrade Plan","/subscribe")
    )

# ================= SUBSCRIBE =================
@app.route("/subscribe")
def subscribe():
    return layout(header("SUBSCRIBE")+
        card(button("Daily - $5","/pay/daily"))+
        card(button("Weekly - $15","/pay/weekly"))+
        card(button("Monthly - $30","/pay/monthly"))
    )

@app.route("/pay/<plan>")
def pay(plan):
    u=get_user()
    if not u: return redirect("/login")

    days={"daily":1,"weekly":7,"monthly":30}[plan]
    expiry=(datetime.now()+timedelta(days=days)).isoformat()

    conn=db(); cur=conn.cursor()
    cur.execute("UPDATE users SET expiry=?, plan=? WHERE code=?",
                (expiry,plan,u["code"]))
    conn.commit(); conn.close()

    return redirect("/dashboard")

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    u=get_user()
    if not u: return redirect("/login")

    if u["plan"]=="free":
        return layout(header("LOCKED")+card("Upgrade to view signals"))

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("SIGNALS")
    for r in rows:
        out+=card(f"{r['symbol']} | Entry:{r['entry']} TP:{r['tp']} SL:{r['sl']} | {r['status']}")
    return layout(out)

# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form["pass"]=="admin123":
            session["admin"]=True

    if not session.get("admin"):
        return layout(header("ADMIN LOGIN")+"""
        <form method="POST"><input name="pass"><button>Login</button></form>
        """)

    return layout(header("ADMIN DASHBOARD")+
        button("Users","/admin/users")+
        button("Trades","/admin/trades")+
        button("Add Signal","/admin/add_trade")+
        button("Generate Code","/admin/generate_code")+
        button("Media","/admin/media")
    )

# ================= GENERATE CODE =================
@app.route("/admin/generate_code")
def generate_code():
    code=str(uuid.uuid4())[:6]
    return layout(header("GENERATED CODE")+f"<h2>{code}</h2>")

# ================= ADD TRADE =================
@app.route("/admin/add_trade", methods=["GET","POST"])
def add_trade():
    if not session.get("admin"): return redirect("/admin")

    if request.method=="POST":
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
                    (request.form["symbol"],request.form["entry"],
                     request.form["tp"],request.form["sl"],"ACTIVE"))
        conn.commit(); conn.close()
        return redirect("/admin/trades")

    return layout(header("ADD SIGNAL")+"""
    <form method="POST">
    Symbol:<input name="symbol"><br>
    Entry:<input name="entry"><br>
    TP:<input name="tp"><br>
    SL:<input name="sl"><br>
    <button>Add</button>
    </form>
    """)

# ================= ADMIN USERS =================
@app.route("/admin/users")
def admin_users():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM users").fetchall()
    conn.close()

    out=header("USERS")
    for u in rows:
        out+=card(f"{u['name']} | {u['plan']}")
    return layout(out)

# ================= ADMIN TRADES =================
@app.route("/admin/trades")
def admin_trades():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("TRADES")
    for r in rows:
        out+=card(f"{r['symbol']} | {r['status']}")
    return layout(out)

# ================= MEDIA =================
@app.route("/admin/media", methods=["GET","POST"])
def admin_media():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()

    if request.method=="POST":
        f=request.files["file"]
        if f:
            filename=f.filename
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            cur.execute("INSERT INTO media VALUES(NULL,?,?,?)",
                        (filename,None,"image"))
            conn.commit()

    conn.close()

    return layout(header("UPLOAD MEDIA")+"""
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file">
    <button>Upload</button>
    </form>
    """)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
