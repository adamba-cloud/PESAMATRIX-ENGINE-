import os, sqlite3, uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, make_response

app = Flask(__name__)
app.secret_key = "change_this_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= UI =================
BG = "#0b1220"
CARD = "#111a2e"
BLUE = "#38bdf8"
WHITE = "white"

def layout(content):
    return f"<body style='margin:0;font-family:Arial;background:{BG};color:{WHITE}'>{content}</body>"

def header(title):
    return f"<div style='background:{CARD};padding:20px;text-align:center'><h1 style='color:{BLUE}'>PESAMATRIX</h1><h2>{title}</h2></div>"

def card(c):
    return f"<div style='background:{CARD};padding:15px;margin:10px;border-radius:10px'>{c}</div>"

def link(t,u):
    return f"<a href='{u}' style='color:{BLUE}'>{t}</a>"

def show_admin_media():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out = "<h2 style='color:#38bdf8;padding:10px'>Uploaded Media</h2>"

    for m in rows:
        preview = ""

        if m["filename"]:
            preview = f"<img src='/static/uploads/{m['filename']}' width='150'>"

        elif m["link"]:
            preview = f"<iframe width='150' height='100' src='{m['link']}'></iframe>"

        out += f"""
        <div style="background:#111a2e;padding:10px;margin:10px;border-radius:10px">
            {preview}<br>

            <a href="/admin/edit_media/{m['id']}" style="color:#38bdf8">✏ Edit</a> |
            <a href="/admin/delete_media/{m['id']}" style="color:red">🗑 Delete</a>
        </div>
        """

    return out

# ================= DB =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn=db();cur=conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        name TEXT, phone TEXT,
        code TEXT,
        code_expiry TEXT,
        is_paid INTEGER DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY,
        symbol TEXT, entry TEXT, sl TEXT, tp TEXT, status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS media(
    id INTEGER PRIMARY KEY,
    filename TEXT,
    link TEXT,
    type TEXT
)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY,
        code TEXT,
        amount TEXT,
        status TEXT,
        created_at TEXT
    )""")

    conn.commit();conn.close()

init()

# ================= AUTH =================
def get_user():
    code = session.get("code") or request.cookies.get("code")
    if not code: return None

    conn=db();cur=conn.cursor()
    u=cur.execute("SELECT * FROM users WHERE code=?",(code,)).fetchone()
    conn.close()

    if not u: return None
    if datetime.now()>datetime.fromisoformat(u["code_expiry"]):
        return None

    session["code"]=code
    return dict(u)

# ================= LANDING =================
@app.route("/")
def home():
    content = f"""
    <div style="padding:60px;text-align:center">
        <h1 style="color:{BLUE};font-size:50px">PESAMATRIX AI</h1>
        <p>Forex Signals • AI Trading • Smart Profits</p>
        {link("Register","/register")} | {link("Login","/login")} | {link("Admin","/admin")}
    </div>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);padding:20px">
        <a href="/signals">{card("📊 Live Signals")}</a>
        <a href="/news">{card("📰 Market News")}</a>
        <a href="/videos">{card("🎥 Trading Videos")}</a>
        <a href="/images">{card("🖼 Images")}</a>
        <a href="/signals">{card("🔐 Premium Signals")}</a>
        <a href="/dashboard">{card("👤 Dashboard")}</a>
        <a href="/payments">{card("💰 Payment Info")}</a>
    </div>

    {card("<h3 style='color:"+BLUE+"'>ABOUT US</h3>We provide high accuracy forex signals and AI-powered trading tools.")}

    {card(f'''
    <h3 style="color:{BLUE}">CONTACT</h3>
    📞 <a href="tel:+254781585319" style="color:{BLUE}">Call</a><br>
    📞 <a href="tel:+254717434943" style="color:{BLUE}">Call</a><br>
    🎵 <a href="https://tiktok.com/@smartgoldsignals" style="color:{BLUE}">TikTok</a>
    ''')}

    {card(f'''
    <h3 style="color:{BLUE}">PAYMENT</h3>
    Mpesa Paybill: <b>322372</b><br>
    Account: Your Code
    ''')}
    """
    return layout(content)

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        code=str(uuid.uuid4())[:8].upper()
        expiry=datetime.now()+timedelta(hours=24)

        conn=db();cur=conn.cursor()
        cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?,0)",
        (request.form["name"],request.form["phone"],code,expiry.isoformat()))
        conn.commit();conn.close()

        return layout(header("CODE")+"<h1>"+code+"</h1>"+link("Login","/login"))

    return layout(header("REGISTER")+"""
    <form method="POST">
    Name:<input name="name"><br>
    Phone:<input name="phone"><br>
    <button>Create</button>
    </form>""")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        conn=db();cur=conn.cursor()
        u=cur.execute("SELECT * FROM users WHERE code=?",(request.form["code"],)).fetchone()
        conn.close()

        if u and datetime.now()<datetime.fromisoformat(u["code_expiry"]):
            session["code"]=u["code"]
            resp=make_response(redirect("/dashboard"))
            resp.set_cookie("code",u["code"],max_age=86400)
            return resp

    return layout(header("LOGIN")+"""
    <form method="POST">
    Code:<input name="code">
    <button>Login</button>
    </form>""")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    u=get_user()
    if not u: return redirect("/login")

    return layout(header("DASHBOARD")+
        card(f"Name:{u['name']}<br>Code:{u['code']}<br>Paid:{u['is_paid']}")+
        card(link("View Signals","/signals"))+
        card(link("Media","/media"))
    )

# ================= SIGNAL LOCK =================
@app.route("/signals")
def signals():
    u=get_user()
    if not u:
        return layout(header("LOCKED")+"Login required")

    if not u["is_paid"]:
        return layout(header("LOCKED")+"Please pay to unlock signals"+link("Payment","/payments"))

    conn=db();cur=conn.cursor()
    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("SIGNALS")
    for r in rows:
        out+=card(f"{r['symbol']} | {r['entry']} | {r['tp']} | {r['sl']} | {r['status']}")
    return layout(out)

# ================= MEDIA =================
@app.route("/media")
def media():
    conn = db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out = header("MEDIA GALLERY")

    if not rows:
        out += card("No media uploaded yet")

    for m in rows:

        # IMAGE / VIDEO FILE
        if m["filename"]:
            out += card(f"""
                <img src='/static/uploads/{m["filename"]}' 
                style='width:100%;border-radius:10px'>
            """)

        # VIDEO LINK
        if m["link"]:
            link = m["link"]

            if "youtube.com/watch?v=" in link:
                link = link.replace("watch?v=", "embed/")

            if "youtu.be/" in link:
                link = link.replace("youtu.be/", "youtube.com/embed/")

            out += card(f"""
                <iframe width='100%' height='250'
                src='{link}'
                frameborder='0'
                allowfullscreen
                style='border-radius:10px'>
                </iframe>
            """)

    return layout(out)

# ================= NEWS =================
@app.route("/news")
def news():
    return layout(header("NEWS")+card("Market updates coming soon"))

#==============IMAGES================================
@app.route("/images")
def images():
    conn=db();cur=conn.cursor()
    rows = cur.execute("SELECT * FROM media WHERE type='image'").fetchall()
    conn.close()

    out = header("🖼 IMAGE GALLERY")

    out += """
    <div style="
        display:grid;
        grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
        gap:10px;
        padding:15px;
    ">
    """

    for m in rows:
        out += f"""
        <div style="overflow:hidden;border-radius:10px">
            <img src="/static/uploads/{m['filename']}"
            style="width:100%;height:150px;object-fit:cover;cursor:pointer"
            onclick="openModal('/static/uploads/{m['filename']}')">
        </div>
        """

    out += "</div>"

    # Modal Viewer
    out += """
    <div id="modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.9);justify-content:center;align-items:center;z-index:999">
        <img id="modalImg" style="max-width:90%;max-height:90%">
    </div>

    <script>
    function openModal(src){
        document.getElementById('modal').style.display='flex';
        document.getElementById('modalImg').src=src;
    }
    document.getElementById('modal').onclick=function(){
        this.style.display='none';
    }
    </script>
    """

    return layout(out)

#=================VIDEOS========================
@app.route("/videos")
def videos():
    conn=db();cur=conn.cursor()
    rows = cur.execute("SELECT * FROM media WHERE type='video'").fetchall()
    conn.close()

    out = header("🎥 TRADING VIDEOS")

    out += """
    <div style="
        display:grid;
        grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
        gap:15px;
        padding:15px;
    ">
    """

    for m in rows:

        # Uploaded video
        if m["filename"]:
            out += f"""
            <div style="background:#111a2e;padding:10px;border-radius:10px">
                <video controls style="width:100%;border-radius:10px">
                    <source src="/static/uploads/{m['filename']}">
                </video>
            </div>
            """

        # Embedded link (YouTube/TikTok)
        elif m["link"]:
            out += f"""
            <div style="background:#111a2e;padding:10px;border-radius:10px">
                <iframe width="100%" height="200"
                src="{m['link']}"
                frameborder="0" allowfullscreen
                style="border-radius:10px"></iframe>
            </div>
            """

    out += "</div>"

    return layout(out)

# ================= PAYMENT =================
@app.route("/payments")
def payments():
    u=get_user()
    acc = u["code"] if u else "Your Code"
    return layout(header("PAYMENT")+
        card(f"Mpesa Paybill:322372<br>Account:{acc}")+
        card("After payment, admin will unlock your account.")
    )

# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form["pass"]=="admin123":
            session["admin"]=True
            return redirect("/admin")

    if not session.get("admin"):
        return layout(header("ADMIN LOGIN")+"""
        <form method="POST">
        <input name="pass">
        <button>Login</button>
        </form>""")

    return layout(header("ADMIN")+
    link("Users","/admin/users")+"<br>"+
    link("Trades","/admin/trades")+"<br>"+
    link("Media Upload","/admin/media")+"<br>"+
    link("Manage Media","/admin/media/manage")+"<br>"+   # ✅ ADDED HERE
    link("Payments","/admin/payments")
)

# ================= ADMIN USERS =================
@app.route("/admin/users", methods=["GET","POST"])
def admin_users():
    if not session.get("admin"): return redirect("/admin")

    conn=db();cur=conn.cursor()

    if request.method=="POST":
        if "extend" in request.form:
            new=datetime.now()+timedelta(hours=24)
            cur.execute("UPDATE users SET code_expiry=? WHERE code=?",(new.isoformat(),request.form["code"]))
        if "unlock" in request.form:
            cur.execute("UPDATE users SET is_paid=1 WHERE code=?",(request.form["code"],))

        conn.commit()

    rows=cur.execute("SELECT * FROM users").fetchall()
    conn.close()

    out=header("USERS")
    for u in rows:
        out+=card(f"""
        {u['name']} | {u['code']} | Paid:{u['is_paid']}
        <form method='POST'>
        <input name='code' value='{u['code']}'>
        <button name='extend'>Extend 24h</button>
        <button name='unlock'>Unlock</button>
        </form>
        """)
    return layout(out)
# ================= ADMIN TRADES =================
@app.route("/admin/trades", methods=["GET","POST"])
def admin_trades():
    if not session.get("admin"): return redirect("/admin")

    conn=db();cur=conn.cursor()

    if request.method=="POST":
        cur.execute("INSERT INTO trades VALUES(NULL,?,?,?,?,?)",
        (request.form["symbol"],request.form["entry"],request.form["sl"],request.form["tp"],request.form["status"]))
        conn.commit()

    rows=cur.execute("SELECT * FROM trades").fetchall()
    conn.close()

    out=header("TRADES")
    out+=("""
    <form method='POST'>
    Symbol<input name='symbol'>
    Entry<input name='entry'>
    SL<input name='sl'>
    TP<input name='tp'>
    Status<input name='status'>
    <button>Create</button>
    </form>
    """)

    for r in rows:
        out+=card(f"{r['symbol']} | {r['status']}")
    return layout(out)

# ================= ADMIN MEDIA =================
@app.route("/admin/media", methods=["GET","POST"])
def admin_media():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    # ================= UPLOAD HANDLER =================
    if request.method == "POST":

        # FILE UPLOAD
        if "file" in request.files:
            f = request.files["file"]

            if f and f.filename:
                filename = f.filename.replace(" ", "_")
                path = os.path.join(UPLOAD_FOLDER, filename)
                f.save(path)

                # detect type
                ext = filename.split(".")[-1].lower()
                if ext in ["mp4", "mov", "avi", "webm"]:
                    mtype = "video"
                else:
                    mtype = "image"

                cur.execute(
                    "INSERT INTO media VALUES(NULL,?,?,?)",
                    (filename, None, mtype)
                )

        # LINK UPLOAD (YouTube / TikTok)
        link = request.form.get("link")
        if link:
            cur.execute(
                "INSERT INTO media VALUES(NULL,?,?,?)",
                (None, link, "video")
            )

        conn.commit()

    conn.close()

    # ================= PAGE UI =================
    return layout(
        header("UPLOAD MEDIA") +

        """
        <div style='padding:15px'>
        <form method='POST' enctype='multipart/form-data'>

            Upload File:<br>
            <input type='file' name='file'><br><br>

            OR Video Link:<br>
            <input name='link'><br><br>

            <button style='padding:10px;background:#38bdf8;color:white;border:none;border-radius:8px'>
                Upload
            </button>

        </form>
        </div>
        """

        # 👇 THIS SHOWS YOUR UPLOADED MEDIA
        + show_admin_media()
    )
    
# =================DELETE ROUTE=====================
@app.route("/admin/delete_media/<int:id>")
def delete_media(id):
    if not session.get("admin"):
        return redirect("/admin")

    conn = db(); cur = conn.cursor()

    # get file first
    m = cur.execute("SELECT * FROM media WHERE id=?", (id,)).fetchone()

    if m:
        # delete file from storage
        if m["filename"]:
            path = os.path.join(UPLOAD_FOLDER, m["filename"])
            if os.path.exists(path):
                os.remove(path)

        # delete from DB
        cur.execute("DELETE FROM media WHERE id=?", (id,))
        conn.commit()

    conn.close()
    return redirect("/admin/media")

 # ================ EDIT ROUTE =====================
 @app.route("/admin/edit_media/<int:id>", methods=["GET","POST"])
def edit_media(id):
    if not session.get("admin"):
        return redirect("/admin")

    conn = db(); cur = conn.cursor()

    if request.method == "POST":
        new_link = request.form.get("link")

        # replace link
        if new_link:
            cur.execute("UPDATE media SET link=? WHERE id=?", (new_link, id))

        # replace file
        if "file" in request.files:
            f = request.files["file"]
            if f and f.filename:
                filename = f.filename.replace(" ", "_")
                path = os.path.join(UPLOAD_FOLDER, filename)
                f.save(path)

                cur.execute("UPDATE media SET filename=?, link=NULL WHERE id=?",
                            (filename, id))

        conn.commit()
        conn.close()
        return redirect("/admin/media")

    m = cur.execute("SELECT * FROM media WHERE id=?", (id,)).fetchone()
    conn.close()

    return layout(header("EDIT MEDIA") + f"""
    <form method="POST" enctype="multipart/form-data">
        Replace File:<br>
        <input type="file" name="file"><br><br>

        OR Update Link:<br>
        <input name="link" value="{m['link'] if m['link'] else ''}"><br><br>

        <button>Update</button>
    </form>
    """)
# ================= ADMIN PAYMENTS =================
@app.route("/admin/payments", methods=["GET","POST"])
def admin_payments():
    if not session.get("admin"): return redirect("/admin")

    conn=db();cur=conn.cursor()

    if request.method=="POST":
        cur.execute("INSERT INTO payments VALUES(NULL,?,?,?,?)",
        (request.form["code"],request.form["amount"],"confirmed",datetime.now().isoformat()))
        cur.execute("UPDATE users SET is_paid=1 WHERE code=?",(request.form["code"],))
        conn.commit()

    rows=cur.execute("SELECT * FROM payments").fetchall()
    conn.close()

    out=header("PAYMENTS")
    out+=("""
    <form method='POST'>
    User Code:<input name='code'>
    Amount:<input name='amount'>
    <button>Confirm Payment</button>
    </form>
    """)

    for p in rows:
        out+=card(f"{p['code']} | {p['amount']} | {p['status']}")
    return layout(out)

# ================= RUN =================
if __name__=="__main__":
    app.run(debug=True)
