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
def home():
    return layout(header("WELCOME")+card("PESAMATRIX AI PLATFORM"))

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
        out+=card(f"{r['symbol']} | {r['status']}")
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
        button("Payments","/admin/payments")+
        button("Logs","/admin/logs")+
        button("Manage Trades","/admin/manage_trades")+
        button("Add Signal","/admin/add_trade")+
        button("Media","/admin/media")+
        button("News","/admin/news")
    )

# ================= ADMIN LOGS =================
@app.route("/admin/logs")
def admin_logs():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()
    rows=cur.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()

    out=header("USER LOGS")
    for l in rows:
        out+=card(f"{l['code']} | {l['ip']} | {l['date']}")
    return layout(out)

# ================= ADMIN MEDIA =================
@app.route("/admin/media", methods=["POST","GET"])
def admin_media():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()

    if request.method=="POST":
        f=request.files.get("file")
        link=request.form.get("link")
        type=request.form.get("type")

        if f and f.filename:
            f.save(os.path.join(UPLOAD_FOLDER,f.filename))
            cur.execute("INSERT INTO media VALUES(NULL,?,?,?)",(f.filename,None,type))
        elif link:
            cur.execute("INSERT INTO media VALUES(NULL,?,?,?)",(None,link,type))

        conn.commit()

    conn.close()

    return layout(header("MEDIA")+"""
    <form method="POST" enctype="multipart/form-data">
    File:<input type="file" name="file"><br>
    OR Link:<input name="link"><br>
    <select name="type">
    <option value="image">Image</option>
    <option value="video">Video</option>
    </select><br>
    <button>Upload</button>
    </form>
    """)

# ================= ADMIN NEWS =================
@app.route("/admin/news", methods=["POST","GET"])
def admin_news():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()

    if request.method=="POST":
        cur.execute("INSERT INTO news VALUES(NULL,?,?,?)",
                    (request.form["title"],
                     request.form["content"],
                     str(datetime.now())))
        conn.commit()

    conn.close()

    return layout(header("ADD NEWS")+"""
    <form method="POST">
    Title:<input name="title"><br>
    Content:<textarea name="content"></textarea><br>
    <button>Add</button>
    </form>
    """)

# ================= ADMIN ADD TRADE =================
@app.route("/admin/add_trade", methods=["POST","GET"])
def add_trade():
    if not session.get("admin"): return redirect("/admin")

    if request.method=="POST":
        conn=db(); cur=conn.cursor()
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
                    (request.form["symbol"],request.form["entry"],
                     request.form["tp"],request.form["sl"],"UPCOMING"))
        conn.commit(); conn.close()
        return redirect("/admin/manage_trades")

    return layout(header("ADD SIGNAL")+"""
    <form method="POST">
    Symbol:<input name="symbol"><br>
    Entry:<input name="entry"><br>
    TP:<input name="tp"><br>
    SL:<input name="sl"><br>
    <button>Add</button>
    </form>
    """)

# ================= ADMIN MANAGE TRADES =================
@app.route("/admin/manage_trades", methods=["POST","GET"])
def manage_trades():
    if not session.get("admin"): return redirect("/admin")

    conn=db(); cur=conn.cursor()

    if request.method=="POST":
        cur.execute("UPDATE trades SET status=? WHERE id=?",
                    (request.form["status"],request.form["id"]))
        conn.commit()

    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("MANAGE TRADES")
    for r in rows:
        out+=card(f"""
        {r['symbol']} | {r['status']}
        <form method="POST">
        <input type="hidden" name="id" value="{r['id']}">
        <select name="status">
        <option>UPCOMING</option>
        <option>RUNNING</option>
        <option>EXPIRED</option>
        </select>
        <button>Update</button>
        </form>
        """)
    return layout(out)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
