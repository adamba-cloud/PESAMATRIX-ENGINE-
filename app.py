import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
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
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
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


# ---------------- TRADE LOGIC ----------------
def execute_trade(symbol, side, entry, sl, tp):
    return {
        "symbol": symbol,
        "side": side,
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "status": "ACTIVE"
    }


# ---------------- CLASSIFY TRADE STATUS ----------------
def classify_trade(expiry):
    if not expiry:
        return "UNKNOWN"

    now = datetime.now()
    exp = datetime.fromisoformat(expiry)

    if now > exp:
        return "EXPIRED"

    return "ACTIVE"


# ---------------- LIVE API ----------------
@app.route("/api/live")
def live_data():
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 20")
    trades = cur.fetchall()

    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 10")
    posts = cur.fetchall()

    cur.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 10")
    notes = cur.fetchall()

    return jsonify({
        "trades": trades,
        "posts": posts,
        "notifications": notes
    })


# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 10")
    trades = cur.fetchall()

    cur.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 5")
    posts = cur.fetchall()

    cur.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 5")
    notes = cur.fetchall()

    return render_template_string("""
    <html>
    <head>
        <title>PESAMATRIX DASHBOARD</title>
        <style>
            body { margin:0; font-family: Arial; background:#0f172a; color:white; }
            .sidebar { width:220px; height:100vh; background:#111827; position:fixed; padding:20px; }
            .sidebar a { display:block; color:#38bdf8; margin:12px 0; text-decoration:none; }
            .main { margin-left:240px; padding:20px; }
            .card { background:#1e293b; padding:15px; border-radius:10px; margin-bottom:15px; }
            input, button { width:100%; padding:10px; margin-top:8px; border-radius:6px; border:none; }
            button { background:#22c55e; color:white; cursor:pointer; }
            .box { background:#1e293b; padding:10px; border-radius:8px; margin-top:10px; }
            .active { border-left:5px solid #22c55e; }
            .expired { border-left:5px solid #ef4444; opacity:0.6; }
            .upcoming { border-left:5px solid #facc15; }
        </style>
    </head>

    <body>

    <div class="sidebar">
        <h3>🚀 PESAMATRIX</h3>
        <a href="/">Dashboard</a>
        <a href="/access">Access Page</a>
        <a href="/generate">Generate Code</a>
    </div>

    <div class="main">

        <h1>📊 LIVE TRADING DASHBOARD</h1>

        <!-- TRADE FORM -->
        <div class="card">
            <h3>Send Trade Signal</h3>
            <form action="/trade" method="post">
                <input name="symbol" placeholder="Symbol" required>
                <input name="side" placeholder="BUY / SELL" required>
                <input name="entry" placeholder="Entry" required>
                <input name="sl" placeholder="SL" required>
                <input name="tp" placeholder="TP" required>
                <button>Send Signal</button>
            </form>
        </div>

        <!-- TRADES -->
        <div class="card">
            <h3>Live Trades (Active / Expired)</h3>
            <div id="tradesBox"></div>
        </div>

        <!-- POSTS -->
        <div class="card">
            <h3>Posts</h3>
            <div id="postsBox"></div>
        </div>

        <!-- NOTIFICATIONS -->
        <div class="card">
            <h3>Notifications</h3>
            <div id="notesBox"></div>
        </div>

    </div>

    <script>
        async function loadData(){
            const res = await fetch("/api/live");
            const data = await res.json();

            // trades
            let t = "";
            data.trades.forEach(x=>{
                let status = x[6];
                let cls = status === "EXPIRED" ? "expired" : "active";

                t += `<div class="box ${cls}">
                        <b>${x[1]}</b><br>
                        ${x[2]} @ ${x[3]}<br>
                        SL: ${x[4]} TP: ${x[5]}<br>
                        <small>${status}</small>
                      </div>`;
            });

            document.getElementById("tradesBox").innerHTML = t;

            // posts
            let p = "";
            data.posts.forEach(x=>{
                p += `<div class="box"><b>${x[1]}</b><p>${x[2]}</p></div>`;
            });
            document.getElementById("postsBox").innerHTML = p;

            // notifications
            let n = "";
            data.notifications.forEach(x=>{
                n += `<div class="box">${x[1]} <br><small>${x[2]}</small></div>`;
            });
            document.getElementById("notesBox").innerHTML = n;
        }

        setInterval(loadData, 3000);
        loadData();
    </script>

    </body>
    </html>
    """, trades=trades, posts=posts, notes=notes)


# ---------------- TRADE ----------------
@app.route("/trade", methods=["POST"])
def trade():
    data = request.form

    now = datetime.now()
    expiry = now + timedelta(hours=4)

    result = execute_trade(
        data["symbol"],
        data["side"],
        data["entry"],
        data["sl"],
        data["tp"]
    )

    cur.execute("""
        INSERT INTO trades 
        (symbol, side, entry, sl, tp, status, created_at, expiry_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["symbol"],
        result["side"],
        result["entry"],
        result["sl"],
        result["tp"],
        "ACTIVE",
        now.isoformat(),
        expiry.isoformat()
    ))

    cur.execute(
        "INSERT INTO notifications (message, created_at) VALUES (?, ?)",
        (f"📢 {result['symbol']} {result['side']} @ {result['entry']}", now.isoformat())
    )

    conn.commit()
    return redirect("/")


# ---------------- POSTS ----------------
@app.route("/post", methods=["POST"])
def post():
    cur.execute(
        "INSERT INTO posts (title, content, media_url, created_at) VALUES (?, ?, ?, ?)",
        (
            request.form["title"],
            request.form["content"],
            request.form.get("media_url", ""),
            datetime.now().isoformat()
        )
    )
    conn.commit()
    return redirect("/")


# ---------------- ACCESS ----------------
@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        code = request.form["code"]

        cur.execute("SELECT * FROM access_codes WHERE code=?", (code,))
        result = cur.fetchone()

        if result and datetime.now() < datetime.fromisoformat(result[2]):
            session["access"] = True
            return redirect("/")

        return "Invalid code"

    return "<h2>Enter Access Code</h2><form method='post'><input name='code'><button>Enter</button></form>"


# ---------------- GENERATE ----------------
@app.route("/generate")
def generate():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.now() + timedelta(days=1)

    cur.execute(
        "INSERT INTO access_codes (code, expiry_date) VALUES (?, ?)",
        (code, expiry.isoformat())
    )
    conn.commit()

    return f"CODE: {code} (24h valid)"


# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
