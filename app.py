from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DATABASE ---------- #
def get_db():
    db_path = os.path.join(os.getcwd(), "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        score INTEGER DEFAULT 0
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        day TEXT,
        study_minutes INTEGER DEFAULT 0,
        game_minutes INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

create_tables()

# ---------- HELPER ---------- #
def check_login():
    return 'user' in session

# ---------- AUTH ---------- #
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)", (u,p))
            conn.commit()
            flash("Account created!")
            return redirect('/login')
        except:
            flash("Username already exists!")
            return redirect('/register')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
        conn.close()
        if user:
            session['user'] = u
            return redirect('/dashboard')
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- DASHBOARD ---------- #
@app.route('/dashboard')
def dashboard():
    if not check_login():
        return redirect('/login')
    user = session.get('user')
    conn = get_db()
    rows = conn.execute("SELECT * FROM sessions WHERE username=?", (user,)).fetchall()
    conn.close()

    dates = [r['day'] for r in rows] or ["Mon","Tue","Wed","Thu","Fri"]
    minutes = [r['study_minutes'] for r in rows] or [30,45,20,60,50]

    study_total = sum([r['study_minutes'] for r in rows]) if rows else sum(minutes)
    game_total = sum([r['game_minutes'] for r in rows]) if rows else 20

    xp = study_total * 2
    level = max(1, xp // 50)
    sessions_count = len(rows) if rows else len(minutes)
    streak = 3
    coach_message = "Stay consistent 💪 You are improving!"

    return render_template(
        "dashboard.html",
        user=user,
        dates=dates,
        minutes=minutes,
        study_total=study_total,
        game_total=game_total,
        xp=xp,
        level=level,
        sessions=sessions_count,
        streak=streak,
        coach_message=coach_message
    )

# ---------- ADD STUDY ---------- #
@app.route('/add_study', methods=['POST'])
def add_study():
    if not check_login():
        return redirect('/login')
    minutes = int(request.form['minutes'])
    day = datetime.now().strftime("%a")
    conn = get_db()
    conn.execute("INSERT INTO sessions (username, day, study_minutes) VALUES (?, ?, ?)",
                 (session['user'], day, minutes))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------- ADD GAME ---------- #
@app.route('/add_game', methods=['POST'])
def add_game():
    if not check_login():
        return redirect('/login')
    minutes = int(request.form['minutes'])
    day = datetime.now().strftime("%a")
    conn = get_db()
    conn.execute("INSERT INTO sessions (username, day, game_minutes) VALUES (?, ?, ?)",
                 (session['user'], day, minutes))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------- PROFILE ---------- #
@app.route('/profile')
def profile():
    if not check_login():
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

# ---------- LEADERBOARD ---------- #
@app.route('/leaderboard')
def leaderboard():
    if not check_login():
        return redirect('/login')
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY score DESC").fetchall()
    conn.close()
    users = [dict(u) for u in users]
    for u in users:
        if 'score' not in u or u['score'] is None:
            u['score'] = 0
    return render_template('leaderboard.html', users=users)

# ---------- ANALYTICS ---------- #
@app.route('/analytics')
def analytics():
    if not check_login():
        return redirect('/login')
    user = session['user']
    conn = get_db()
    rows = conn.execute("SELECT day, SUM(study_minutes) AS study, SUM(game_minutes) AS game "
                        "FROM sessions WHERE username=? GROUP BY day", (user,)).fetchall()
    conn.close()

    week_days = [r['day'] for r in rows]
    study_minutes = [r['study'] or 0 for r in rows]
    game_minutes = [r['game'] or 0 for r in rows]

    return render_template('analytics.html',
                           week_days=week_days,
                           study_minutes=study_minutes,
                           game_minutes=game_minutes)

# ---------- BADGES ---------- #
@app.route('/badges')
def badges():
    if not check_login():
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.close()
    score = user['score'] if user['score'] else 0
    if score >= 50:
        badge = "🏆 Pro"
    elif score >= 20:
        badge = "⭐ Intermediate"
    else:
        badge = "🔥 Beginner"
    return render_template('badges.html', badge=badge)

# ---------- AUTO SESSION ---------- #
@app.route('/auto_session')
def auto_session():
    return jsonify({"status": "success"})

# ---------- TEST ROUTE ---------- #
@app.route('/test')
def test():
    return "Server is working ✅"

# ---------- RUN ---------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
