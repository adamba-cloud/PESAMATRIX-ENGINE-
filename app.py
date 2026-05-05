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
        media = f"<img src='{p[3]}' width='100%'>" if p[3] else ""
        html_posts += f"""
        <div style='background:#1e293b;margin:10px;padding:10px'>
            <b>{p[1]}</b><p>{p[2]}</p>{media}
        </div>
        """

    return f"""
    <body style='background:#0f172a;color:white;font-family:Arial'>
        <h1>🚀 PESAMATRIX</h1>

        <h2>About</h2>
        <p>Trading signals & education</p>

        <h2>Contacts</h2>
        <p>📞 +254...</p>

        <h2>Services</h2>
        <p>🔐 Signals (Locked)</p>
        <a href='/access'>Unlock</a>

        <h2>Videos & News</h2>
        {html_posts}

        <h2>Join</h2>
        <form action='/register' method='post'>
            <input name='name' placeholder='Name'><br>
            <input name='contact'><br>
            <button>Join</button>
        </form>

        <br><a href='/login'>Admin</a>
    </body>
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
    <form method='post'>
        <input name='password'>
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

    cur.execute("SELECT * FROM access_codes ORDER BY id DESC")
    codes = cur.fetchall()

    return render_template_string("""
    <body style="background:#0f172a;color:white;font-family:Arial">

    <h1>ADMIN DASHBOARD</h1>

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

    <h3>Update Trade Status</h3>
    <form action="/update_status" method="post">
        <input name="id" placeholder="Trade ID"><br>
        <select name="status">
            <option>ACTIVE</option>
            <option>EXPIRED</option>
            <option>UPCOMING</option>
        </select>
        <button>Update</button>
    </form>

    <h3>Upload Post (Video/Image/News)</h3>
    <form action="/post" method="post">
        <input name="title" placeholder="Title"><br>
        <input name="content" placeholder="Content"><br>
        <input name="media_url" placeholder="Image/Video URL"><br>
        <button>Post</button>
    </form>

    <h3>Trades</h3>
    {% for t in trades %}
        <div style="background:#1e293b;margin:10px;padding:10px">
            ID {{t[0]}} | {{t[1]}} {{t[2]}}<br>
            Entry: {{t[3]}} SL: {{t[4]}} TP: {{t[5]}}<br>
            Status: {{t[6]}}
        </div>
    {% endfor %}

    <h3>Access Codes</h3>
    <a href="/generate">Generate New Code</a>

    {% for c in codes %}
        <div style="background:#111827;margin:5px;padding:5px">
            {{c[1]}} (expires {{c[2]}})
        </div>
    {% endfor %}

    </body>
    """, trades=trades, codes=codes)


# ================= CREATE TRADE =================
@app.route("/trade", methods=["POST"])
def trade():
    now = datetime.now()
    expiry = now + timedelta(hours=4)

    cur.execute("""
        INSERT INTO trades 
        (symbol, side, entry, sl, tp, status, created_at, expiry_at)
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


# ================= UPDATE STATUS =================
@app.route("/update_status", methods=["POST"])
def update_status():
    cur.execute("UPDATE trades SET status=? WHERE id=?",
                (request.form["status"], request.form["id"]))
    conn.commit()
    return redirect("/admin")


# ================= POSTS =================
@app.route("/post", methods=["POST"])
def post():
    cur.execute("""
        INSERT INTO posts (title, content, media_url, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["title"],
        request.form["content"],
        request.form["media_url"],
        datetime.now().isoformat()
    ))
    conn.commit()
    return redirect("/admin")


# ================= ACCESS =================
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
    <form method='post'>
        <input name='code'>
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

    html = "<h1>Signals</h1>"
    for r in rows:
        html += f"""
        <div style='background:#1e293b;margin:10px;padding:10px'>
            {r[1]} {r[2]}<br>
            Entry: {r[3]} SL: {r[4]} TP: {r[5]}<br>
            Status: {r[6]}
        </div>
        """

    return html


# ================= GENERATE CODE =================
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
