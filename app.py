import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

# ================= CONFIG =================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DATABASE =================
def db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

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
        code TEXT,
        expiry TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        media TEXT,
        type TEXT,
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
    conn.close()


init_db()

# ================= SETTINGS HELPERS =================
def get_setting(key, default=""):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = db()
    cur = conn.cursor()
    cur.execute("REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


# ================= HOME PAGE =================
@app.route("/")
def home():
    return render_template_string(f"""
    <html>
    <head>
        <title>PESAMATRIX</title>
        <style>
            body {{
                margin:0;
                font-family:{get_setting("font","Arial")};
                background:{get_setting("bg","#0f172a")};
                color:white;
            }}
            .nav {{
                display:flex;
                justify-content:space-between;
                padding:15px;
                background:#111827;
            }}
            .grid {{
                display:grid;
                grid-template-columns:repeat(2,1fr);
                gap:15px;
                padding:20px;
            }}
            .card {{
                background:#1e293b;
                padding:20px;
                border-radius:12px;
                text-align:center;
            }}
            a {{
                color:#38bdf8;
                text-decoration:none;
                font-weight:bold;
            }}
        </style>
    </head>
    <body>

    <div class="nav">
        <h2>{get_setting("logo","🚀 PESAMATRIX")}</h2>
        <a href="/login">Admin</a>
    </div>

    <div class="grid">

        <div class="card"><a href="/videos">🎥 Free Videos</a></div>
        <div class="card"><a href="/news">📰 Trading News</a></div>
        <div class="card"><a href="/access">🔐 Premium Signals</a></div>
        <div class="card"><a href="/posts">📊 Latest Posts</a></div>
        <div class="card"><a href="/register">🟢 Join</a></div>
        <div class="card"><a href="/signals">📈 Signals</a></div>

    </div>

    </body>
    </html>
    """)

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                    (request.form["name"], request.form["contact"], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return redirect("/")

    return "<form method='post'><input name='name'><input name='contact'><button>Join</button></form>"


# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return "<form method='post'><input name='password'><button>Login</button></form>"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        for key in ["about","phone","email","social","logo","bg","font"]:
            if key in request.form:
                set_setting(key, request.form[key])

    return """
    <h1>ADMIN PANEL</h1>

    <form method='post'>
        <input name='about' placeholder='About'><br>
        <input name='phone' placeholder='Phone'><br>
        <input name='email' placeholder='Email'><br>
        <input name='social' placeholder='Social'><br>
        <input name='logo' placeholder='Logo'><br>
        <input name='bg' placeholder='Background'><br>
        <input name='font' placeholder='Font'><br>
        <button>Save</button>
    </form>

    <br>
    <a href="/generate_code">Generate Code</a><br>
    <a href="/codes">Saved Codes</a><br>
    <a href="/upload">Upload Media</a><br>
    <a href="/trade">Create Trade</a><br>
    """


# ================= CODE GENERATOR =================
@app.route("/generate_code")
def generate_code():
    if not session.get("admin"):
        return redirect("/login")

    code = str(uuid.uuid4())[:8].upper()
    expiry = datetime.now() + timedelta(days=7)

    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO access_codes VALUES (NULL,?,?)",
                (code, expiry.isoformat()))
    conn.commit()
    conn.close()

    return f"CODE: {code}"


@app.route("/codes")
def codes():
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM access_codes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<h1>CODES</h1>"
    for r in rows:
        out += f"<div>{r['code']} | {r['expiry']}</div>"
    return out


# ================= UPLOAD =================
@app.route("/upload", methods=["GET","POST"])
def upload():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        media_type = "image"
        if filename.endswith(("mp4","mov")):
            media_type = "video"

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?,?)",
                    (request.form["title"], request.form["content"], path, media_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return "<form method='post' enctype='multipart/form-data'><input name='title'><input name='content'><input type='file' name='file'><button>Upload</button></form>"


# ================= TRADE =================
@app.route("/trade", methods=["GET","POST"])
def trade():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO trades VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (request.form["symbol"], request.form["side"],
                     float(request.form["entry"]), float(request.form["sl"]),
                     float(request.form["tp"]), "ACTIVE",
                     datetime.now().isoformat(),
                     (datetime.now()+timedelta(hours=4)).isoformat()))
        conn.commit()
        conn.close()
        return redirect("/admin")

    return "<form method='post'><input name='symbol'><input name='side'><input name='entry'><input name='sl'><input name='tp'><button>Create</button></form>"


# ================= ACCESS =================
@app.route("/access", methods=["GET","POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        row = cur.fetchone()
        conn.close()

        if row:
            session["access"] = True
            return redirect("/signals")

        return "Invalid code"

    return "<form method='post'><input name='code'><button>Unlock</button></form>"


# ================= SIGNALS (LOCKED) =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<h1>LOCKED SIGNALS</h1>"
    for r in rows:
        out += f"<div>{r['symbol']} {r['side']} | {r['status']}</div>"

    return out


# ================= NEWS =================
@app.route("/news")
def news():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<h1>NEWS</h1>"
    for r in rows:
        out += f"<div>{r['title']} - {r['content']}</div>"

    return out


# ================= VIDEOS =================
@app.route("/videos")
def videos():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE type='video'")
    rows = cur.fetchall()
    conn.close()

    out = "<h1>VIDEOS</h1>"
    for r in rows:
        out += f"<video controls width='300'><source src='/{r['media']}'></video>"

    return out


# ================= POSTS =================
@app.route("/posts")
def posts():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    out = "<h1>POSTS</h1>"
    for r in rows:
        out += f"<div>{r['title']}</div>"

    return out


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
