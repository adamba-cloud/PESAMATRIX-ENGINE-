import os
import sqlite3
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, redirect, session, render_template_string

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_PASSWORD = "admin123"

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
        media = f"<img src='{p[3]}' class='media'>" if p[3] else ""
        html_posts += f"""
        <div class='card fade'>
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
                font-family: 'Segoe UI';
                background:#0f172a;
                color:white;
            }}

            .nav {{
                display:flex;
                justify-content:space-between;
                padding:20px;
                background:#111827;
            }}

            .logo {{
                height:40px;
            }}

            .hero {{
                text-align:center;
                padding:60px 20px;
            }}

            .hero h1 {{
                font-size:40px;
                background: linear-gradient(to right,#38bdf8,#22c55e);
                -webkit-background-clip:text;
                color:transparent;
            }}

            .section {{
                padding:40px;
            }}

            .grid {{
                display:grid;
                grid-template-columns:1fr 1fr;
                gap:20px;
            }}

            .card {{
                background:#1e293b;
                padding:20px;
                border-radius:12px;
                transition:0.3s;
            }}

            .card:hover {{
                transform:translateY(-5px);
            }}

            input,button {{
                padding:12px;
                width:100%;
                margin-top:10px;
                border:none;
                border-radius:8px;
            }}

            button {{
                background:#22c55e;
                color:white;
                cursor:pointer;
            }}

            .media {{
                width:100%;
                border-radius:10px;
                margin-top:10px;
            }}

            .fade {{
                animation:fadeIn 1s ease;
            }}

            @keyframes fadeIn {{
                from {{opacity:0; transform:translateY(10px)}}
                to {{opacity:1}}
            }}
        </style>
    </head>

    <body>

    <div class="nav">
        <img src="/static/logo.png" class="logo">
        <a href="/login">Admin</a>
    </div>

    <div class="hero">
        <h1>AI-Powered Trading Signals</h1>
        <p>Trade smarter. Not harder.</p>
    </div>

    <div class="section grid">
        <div class="card">
            <h2>About</h2>
            <p>Premium forex & crypto signals powered by smart analytics.</p>
        </div>

        <div class="card">
            <h2>Contacts</h2>
            <p>📞 +254...</p>
            <p>📱 Telegram | Instagram</p>
        </div>
    </div>

    <div class="section">
        <h2>Services</h2>
        <div class="grid">
            <div class="card">🎥 Free Videos</div>
            <div class="card">📰 Market News</div>
            <div class="card">🔐 Premium Signals</div>
            <div class="card"><a href="/access">Unlock Signals</a></div>
        </div>
    </div>

    <div class="section">
        <h2>Market Intelligence</h2>
        {html_posts}
    </div>

    <div class="section">
        <h2>Join Platform</h2>
        <form action="/register" method="post">
            <input name="name" placeholder="Name">
            <input name="contact" placeholder="Phone or Email">
            <button>Join Now</button>
        </form>
    </div>

    </body>
    </html>
    """


# ================= ADMIN DASHBOARD =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    cur.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cur.fetchall()

    return render_template_string("""
    <html>
    <head>
        <style>
            body {margin:0;font-family:Arial;background:#0f172a;color:white;}
            .sidebar {width:220px;background:#111827;height:100vh;position:fixed;padding:20px;}
            .sidebar a {display:block;color:#38bdf8;margin:10px 0;text-decoration:none;}
            .main {margin-left:240px;padding:20px;}
            .card {background:#1e293b;padding:20px;margin-bottom:15px;border-radius:12px;}
            input,select,button {width:100%;padding:10px;margin-top:8px;border-radius:8px;border:none;}
            button {background:#22c55e;color:white;}
            .trade {background:#111827;padding:10px;margin-top:10px;border-radius:10px;}
        </style>
    </head>

    <body>

    <div class="sidebar">
        <img src="/static/logo.png" width="150"><br><br>
        <a href="/admin">Dashboard</a>
        <a href="/generate">Access Codes</a>
        <a href="/logout">Logout</a>
    </div>

    <div class="main">

        <div class="card">
            <h3>🚀 Deploy Trade</h3>
            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol">
                <input name="side">
                <input name="entry">
                <input name="sl">
                <input name="tp">
                <button>Deploy</button>
            </form>
        </div>

        <div class="card">
            <h3>🧠 Update Status</h3>
            <form action="/update_status" method="post">
                <input name="id" placeholder="Trade ID">
                <select name="status">
                    <option>ACTIVE</option>
                    <option>EXPIRED</option>
                    <option>UPCOMING</option>
                </select>
                <button>Update</button>
            </form>
        </div>

        <div class="card">
            <h3>📊 Live Trades</h3>
            {% for t in trades %}
            <div class="trade">
                <b>{{t[1]}}</b> {{t[2]}}<br>
                Entry: {{t[3]}} | SL: {{t[4]}} | TP: {{t[5]}}<br>
                Status: {{t[6]}}
            </div>
            {% endfor %}
        </div>

    </div>

    </body>
    </html>
    """, trades=trades)


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
    return "<form method='post'><input name='password'><button>Login</button></form>"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= CORE FUNCTIONS =================
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


@app.route("/update_status", methods=["POST"])
def update_status():
    cur.execute("UPDATE trades SET status=? WHERE id=?",
                (request.form["status"], request.form["id"]))
    conn.commit()
    return redirect("/admin")


@app.route("/generate")
def generate():
    if not session.get("admin"):
        return redirect("/login")

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute("INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
                (code, expiry.isoformat()))
    conn.commit()

    return redirect("/admin")


# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
