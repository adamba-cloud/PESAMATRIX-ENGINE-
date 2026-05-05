import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# ================= ADMIN SECURITY =================
ADMIN_PASSWORD = "admin123"

# ================= UPLOAD CONFIG =================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ================= DATABASE =================
conn = sqlite3.connect("trades.db", check_same_thread=False)
cur = conn.cursor()

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
    code TEXT UNIQUE,
    expiry_date TEXT
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

cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    media_url TEXT,
    media_type TEXT,
    created_at TEXT
)
""")

conn.commit()


# ================= ROOT =================
@app.route("/")
def root():
    return redirect("/public")


# ================= PUBLIC PAGE =================
@app.route("/public")
def public():
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    html_posts = ""

    for p in posts:
        media = ""

        if p[4] == "image":
            media = f"<img src='/{p[3]}' style='width:100%;border-radius:10px;'>"

        elif p[4] == "video":
            media = f"""
            <video controls style="width:100%;border-radius:10px;">
                <source src="/{p[3]}" type="video/mp4">
            </video>
            """

        html_posts += f"""
        <div style="background:#1e293b;margin:10px;padding:15px;border-radius:12px">
            <h3>{p[1]}</h3>
            <p>{p[2]}</p>
            {media}
        </div>
        """

    return f"""
    <html>
    <head>
        <title>PESAMATRIX</title>
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:#0f172a;
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
                font-size:40px;
                color:#38bdf8;
            }}

            .section {{
                padding:20px;
            }}

            input,button {{
                padding:10px;
                margin-top:8px;
                width:250px;
                border:none;
                border-radius:8px;
            }}

            button {{
                background:#22c55e;
                color:white;
                cursor:pointer;
            }}
        </style>
    </head>

    <body>

    <div class="nav">
        <h2>🚀 PESAMATRIX</h2>
        <a href="/login" style="color:#38bdf8;">Admin</a>
    </div>

    <div class="hero">
        <h1>AI Trading Signal Platform</h1>
        <p>Forex • Crypto • Smart Signals</p>
    </div>

    <div class="section">
        <h2>About</h2>
        <p>We deliver high accuracy trading signals in real time.</p>

        <h2>Contacts</h2>
        <p>📞 +254 700 000 000</p>
        <p>📧 support@pesamatrix.com</p>
        <p>📱 Telegram | Instagram | Twitter</p>

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
            <input name="name" placeholder="Name"><br>
            <input name="contact" placeholder="Phone or Email"><br>
            <button>Join</button>
        </form>
    </div>

    </body>
    </html>
    """


# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    cur.execute(
        "INSERT INTO users (name, contact, created_at) VALUES (?, ?, ?)",
        (request.form["name"], request.form["contact"], datetime.now().isoformat())
    )
    conn.commit()
    return redirect("/public")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Wrong password"

    return """
    <form method="post">
        <input name="password" placeholder="Admin Password">
        <button>Login</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= ADMIN DASHBOARD =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cur.fetchall()

    return render_template_string("""
    <body style="background:#0f172a;color:white;font-family:Arial">

    <h1>🚀 ADMIN DASHBOARD</h1>

    <a href="/logout">Logout</a>

    <h3>Create Trade</h3>
    <form action="/trade" method="post">
        <input name="symbol" placeholder="Symbol"><br>
        <input name="side"><br>
        <input name="entry"><br>
        <input name="sl"><br>
        <input name="tp"><br>
        <button>Create</button>
    </form>

    <h3>Update Status</h3>
    <form action="/update_status" method="post">
        <input name="id" placeholder="Trade ID"><br>
        <select name="status">
            <option>ACTIVE</option>
            <option>EXPIRED</option>
            <option>UPCOMING</option>
        </select>
        <button>Update</button>
    </form>

    <h3>Upload Media (Image / Video)</h3>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input name="title" placeholder="Title"><br>
        <input name="content" placeholder="Content"><br>
        <input type="file" name="file"><br>
        <button>Upload</button>
    </form>

    <h3>Live Trades</h3>
    {% for t in trades %}
    <div style="background:#1e293b;margin:10px;padding:10px">
        <b>{{t[1]}}</b> {{t[2]}}<br>
        Entry: {{t[3]}} SL: {{t[4]}} TP: {{t[5]}}<br>
        Status: {{t[6]}}
    </div>
    {% endfor %}

    </body>
    """, trades=trades)


# ================= UPLOAD MEDIA =================
@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        return redirect("/login")

    file = request.files["file"]

    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        media_type = "image"
        if filename.lower().endswith((".mp4", ".mov", ".avi")):
            media_type = "video"

        cur.execute("""
        INSERT INTO posts (title, content, media_url, media_type, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["content"],
            path,
            media_type,
            datetime.now().isoformat()
        ))

        conn.commit()

    return redirect("/admin")


# ================= TRADE =================
@app.route("/trade", methods=["POST"])
def trade():
    now = datetime.now()
    expiry = now + timedelta(hours=4)

    cur.execute("""
        INSERT INTO trades (symbol, side, entry, sl, tp, status, created_at, expiry_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["symbol"],
        request.form["side"],
        float(request.form["entry"]),
        float(request.form["sl"]),
        float(request.form["tp"]),
        "ACTIVE",
        now.isoformat(),
        expiry.isoformat()
    ))

    conn.commit()
    return redirect("/admin")


# ================= STATUS UPDATE =================
@app.route("/update_status", methods=["POST"])
def update_status():
    cur.execute("UPDATE trades SET status=? WHERE id=?",
                (request.form["status"], request.form["id"]))
    conn.commit()
    return redirect("/admin")


# ================= ACCESS SYSTEM =================
@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        result = cur.fetchone()

        if result and datetime.now() < datetime.fromisoformat(result[2]):
            session["access"] = True
            return redirect("/signals")

        return "Invalid code"

    return """
    <form method="post">
        <input name="code">
        <button>Unlock</button>
    </form>
    """


# ================= SIGNALS =================
@app.route("/signals")
def signals():
    if not session.get("access"):
        return redirect("/access")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    rows = cur.fetchall()

    html = "<h1>Premium Signals</h1>"

    for r in rows:
        html += f"""
        <div style='background:#1e293b;margin:10px;padding:10px'>
            {r[1]} {r[2]}<br>
            Entry: {r[3]} SL: {r[4]} TP: {r[5]}<br>
            Status: {r[6]}
        </div>
        """

    return html


# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
