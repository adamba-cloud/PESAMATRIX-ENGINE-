import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this")

# ================= CONFIG =================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DB =================
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

    conn.commit()
    conn.close()


init_db()

# ================= HELPERS =================
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

# ================= PUBLIC PAGE =================
@app.route("/")
def public():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    html_posts = ""
    for p in posts:
        media = ""
        if p["type"] == "image":
            media = f"<img src='/{p['media']}' style='width:100%;border-radius:10px;'>"
        elif p["type"] == "video":
            media = f"""
            <video controls style="width:100%;border-radius:10px;">
                <source src="/{p['media']}">
            </video>
            """

        html_posts += f"""
        <div style="background:#1e293b;margin:10px;padding:15px;border-radius:12px">
            <h3>{p['title']}</h3>
            <p>{p['content']}</p>
            {media}
        </div>
        """

    conn.close()

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
            .hero {{
                text-align:center;
                padding:50px;
            }}
            .hero h1 {{
                color:#38bdf8;
            }}
            .section {{
                padding:20px;
            }}
            a {{
                color:#38bdf8;
            }}
        </style>
    </head>

    <body>

    <div class="nav">
        <h2>{get_setting("logo","🚀 PESAMATRIX")}</h2>
        <a href="/login">Admin</a>
    </div>

    <div class="hero">
        <h1>AI Trading Signal Platform</h1>
        <p>Forex • Crypto • Smart Signals</p>
    </div>

    <div class="section">
        <h2>About</h2>
        <p>{get_setting("about","We deliver high accuracy trading signals in real time.")}</p>

        <h2>Contacts</h2>
        <p>{get_setting("phone","+254 700 000 000")}</p>
        <p>{get_setting("email","support@pesamatrix.com")}</p>
        <p>{get_setting("social","Telegram | Instagram | Twitter")}</p>

        <h2>Services</h2>
        <p>🎥 Free Videos</p>
        <p>📰 Trading News</p>
        <p>🔐 Premium Signals</p>
        <a href="/access">Unlock Signals</a>
    </div>

    <div class="section">
        <h2>Latest Posts</h2>
        {html_posts}
    </div>

    <div class="section">
        <h2>Join</h2>
        <form action="/register" method="post">
            <input name="name" placeholder="Name"><br><br>
            <input name="contact" placeholder="Contact"><br><br>
            <button>Join</button>
        </form>
    </div>

    </body>
    </html>
    """)

# ================= ADMIN LOGIN =================
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

# ================= ADMIN DASHBOARD =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        for key in ["about","phone","email","social","logo","bg","font"]:
            if key in request.form:
                set_setting(key, request.form[key])

    return render_template_string("""
    <body style="background:#0f172a;color:white;font-family:Arial">

    <h1>🚀 SAAS ADMIN</h1>

    <h3>Website Settings</h3>
    <form method="post">
        <input name="about" placeholder="About"><br>
        <input name="phone" placeholder="Phone"><br>
        <input name="email" placeholder="Email"><br>
        <input name="social" placeholder="Social Links"><br>
        <input name="logo" placeholder="Logo Text"><br>
        <input name="bg" placeholder="Background Color"><br>
        <input name="font" placeholder="Font"><br>
        <button>Save Settings</button>
    </form>

    <h3>Upload Media</h3>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input name="title"><br>
        <input name="content"><br>
        <input type="file" name="file"><br>
        <button>Upload</button>
    </form>

    <h3>Create Trade</h3>
    <form action="/trade" method="post">
        <input name="symbol">
        <input name="side">
        <input name="entry">
        <input name="sl">
        <input name="tp">
        <button>Create</button>
    </form>

    </body>
    """)

# ================= UPLOAD =================
@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        return redirect("/login")

    file = request.files["file"]
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    media_type = "image"
    if filename.endswith(("mp4","mov")):
        media_type = "video"

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts (title,content,media,type,created_at)
        VALUES (?,?,?,?,?)
    """, (
        request.form["title"],
        request.form["content"],
        path,
        media_type,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= TRADE =================
@app.route("/trade", methods=["POST"])
def trade():
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO trades VALUES (NULL,?,?,?,?,?,?,?,?)
    """, (
        request.form["symbol"],
        request.form["side"],
        float(request.form["entry"]),
        float(request.form["sl"]),
        float(request.form["tp"]),
        "ACTIVE",
        datetime.now().isoformat(),
        (datetime.now()+timedelta(hours=4)).isoformat()
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= ACCESS SYSTEM =================
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

    out = "<h1>Premium Signals</h1>"
    for r in rows:
        out += f"<div style='background:#1e293b;margin:10px;padding:10px'>{r['symbol']} {r['side']}</div>"

    return out

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
