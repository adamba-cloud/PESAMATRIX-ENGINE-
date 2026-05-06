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

def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

# ================= ADMIN MEDIA PREVIEW =================
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

# ================= INIT DB =================
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
    if not code:
        return None

    conn=db();cur=conn.cursor()
    u=cur.execute("SELECT * FROM users WHERE code=?",(code,)).fetchone()
    conn.close()

    if not u:
        return None

    if datetime.now() > datetime.fromisoformat(u["code_expiry"]):
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
    if not u:
        return redirect("/login")

    return layout(header("DASHBOARD")+
        card(f"Name:{u['name']}<br>Code:{u['code']}<br>Paid:{u['is_paid']}")+
        card(link("View Signals","/signals"))
    )

# ================= SIGNALS =================
@app.route("/signals")
def signals():
    u=get_user()
    if not u:
        return layout(header("LOCKED")+"Login required")

    if not u["is_paid"]:
        return layout(header("LOCKED")+"Please pay"+link("Payment","/payments"))

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
    conn=db();cur=conn.cursor()
    rows=cur.execute("SELECT * FROM media").fetchall()
    conn.close()

    out=header("MEDIA")

    for m in rows:
        if m["filename"]:
            out+=card(f"<img src='/static/uploads/{m['filename']}' width='100%'>")

        if m["link"]:
            out+=card(f"<iframe width='100%' height='250' src='{m['link']}'></iframe>")

    return layout(out)

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
        link("Media Upload","/admin/media")+"<br>"+
        link("Manage Media","/admin/media/manage")
    )

# ================= ADMIN MEDIA =================
@app.route("/admin/media", methods=["GET","POST"])
def admin_media():
    if not session.get("admin"):
        return redirect("/admin")

    conn=db();cur=conn.cursor()

    if request.method=="POST":

        if "file" in request.files:
            f=request.files["file"]
            if f and f.filename:
                filename=f.filename.replace(" ","_")
                path=os.path.join(UPLOAD_FOLDER,filename)
                f.save(path)

                cur.execute("INSERT INTO media VALUES(NULL,?,?,?)",
                            (filename,None,"image"))

        link=request.form.get("link")
        if link:
            cur.execute("INSERT INTO media VALUES(NULL,?,?,?)",
                        (None,link,"video"))

        conn.commit()

    conn.close()

    return layout(header("UPLOAD MEDIA")+"""
    <form method='POST' enctype='multipart/form-data'>
    File:<input type='file' name='file'><br>
    Link:<input name='link'><br>
    <button>Upload</button>
    </form>
    """ + show_admin_media())

# ================= DELETE MEDIA =================
@app.route("/admin/delete_media/<int:id>")
def delete_media(id):
    if not session.get("admin"):
        return redirect("/admin")

    conn=db();cur=conn.cursor()
    m=cur.execute("SELECT * FROM media WHERE id=?",(id,)).fetchone()

    if m and m["filename"]:
        path=os.path.join(UPLOAD_FOLDER,m["filename"])
        if os.path.exists(path):
            os.remove(path)

    cur.execute("DELETE FROM media WHERE id=?",(id,))
    conn.commit()
    conn.close()

    return redirect("/admin/media")

# ================= EDIT MEDIA =================
@app.route("/admin/edit_media/<int:id>", methods=["GET","POST"])
def edit_media(id):
    if not session.get("admin"):
        return redirect("/admin")

    conn=db();cur=conn.cursor()

    if request.method=="POST":
        link=request.form.get("link")

        if link:
            cur.execute("UPDATE media SET link=? WHERE id=?",(link,id))

        if "file" in request.files:
            f=request.files["file"]
            if f and f.filename:
                filename=f.filename.replace(" ","_")
                path=os.path.join(UPLOAD_FOLDER,filename)
                f.save(path)

                cur.execute("UPDATE media SET filename=?, link=NULL WHERE id=?",
                            (filename,id))

        conn.commit()
        return redirect("/admin/media")

    m=cur.execute("SELECT * FROM media WHERE id=?",(id,)).fetchone()
    conn.close()

    return layout(header("EDIT MEDIA")+f"""
    <form method="POST" enctype="multipart/form-data">
    Link:<input name="link" value="{m['link'] if m['link'] else ''}"><br>
    File:<input type="file" name="file"><br>
    <button>Update</button>
    </form>
    """)

# ================= RUN =================
if __name__=="__main__":
    app.run(debug=True)
