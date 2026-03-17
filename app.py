from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------- DATABASE ---------- #

def get_db():
    db_path = os.path.join(os.getcwd(), "database.db")  # ✅ Render-safe path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        score INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()


@app.before_first_request
def init_db():
    create_table()


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
            conn.execute(
                "INSERT INTO users (username,password) VALUES (?,?)",
                (u,p)
            )
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
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u,p)
        ).fetchone()
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


# ---------- HELPER ---------- #

def check_login():
    return 'user' in session


# ---------- DASHBOARD ---------- #

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect('/login')

    # SAFE DATA
    dates = ["Mon","Tue","Wed","Thu","Fri"]
    minutes = [30,45,20,60,50]

    study_total = sum(minutes)
    game_total = 20

    xp = study_total * 2
    level = max(1, xp // 50)

    sessions = len(minutes)
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
        sessions=sessions,
        streak=streak,
        coach_message=coach_message
    )


# ---------- ADD GAME ---------- #

@app.route('/add_game', methods=['POST'])
def add_game():
    return redirect('/dashboard')


# ---------- AUTO SESSION (FIXED) ---------- #

@app.route('/auto_session')
def auto_session():
    return jsonify({"status": "success"})


# ---------- PROFILE ---------- #

@app.route('/profile')
def profile():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (session['user'],)
    ).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


# ---------- LEADERBOARD ---------- #

@app.route('/leaderboard')
def leaderboard():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    users = conn.execute(
        "SELECT * FROM users ORDER BY score DESC"
    ).fetchall()
    conn.close()

    users = [dict(u) for u in users]

    # ✅ Fix NULL scores
    for u in users:
        if u['score'] is None:
            u['score'] = 0

    return render_template('leaderboard.html', users=users)


# ---------- ANALYTICS ---------- #

@app.route('/analytics')
def analytics():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    total = len(users)

    # ✅ Safe score handling
    scores = []
    for u in users:
        if u['score'] is None:
            scores.append(0)
        else:
            scores.append(u['score'])

    avg = sum(scores) / total if total > 0 else 0

    return render_template(
        'analytics.html',
        total=total,
        avg=round(avg, 2)
    )


# ---------- BADGES ---------- #

@app.route('/badges')
def badges():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (session['user'],)
    ).fetchone()
    conn.close()

    score = user['score'] if user['score'] else 0

    if score >= 50:
        badge = "🏆 Pro"
    elif score >= 20:
        badge = "⭐ Intermediate"
    else:
        badge = "🔥 Beginner"

    return render_template('badges.html', badge=badge)


# ---------- TEST ROUTE ---------- #

@app.route('/test')
def test():
    return "Server is working ✅"


# ---------- RUN ---------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
