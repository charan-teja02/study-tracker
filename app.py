from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DATABASE ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
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

create_table()

# ---------------- AUTH ---------------- #

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Account created! Please login.")
            return redirect('/login')
        except:
            flash("Username already exists!")
            return redirect('/register')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", 
                            (username, password)).fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            flash("Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- HELPER ---------------- #

def check_login():
    return 'user' in session


# ---------------- PAGES ---------------- #

@app.route('/dashboard')
def dashboard():
    if not check_login():
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'])


@app.route('/profile')
def profile():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", 
                        (session['user'],)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


@app.route('/analytics')
def analytics():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    total = len(users)
    avg = sum([u['score'] for u in users]) / total if total > 0 else 0

    return render_template('analytics.html', total=total, avg=round(avg, 2))


@app.route('/leaderboard')
def leaderboard():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY score DESC").fetchall()
    conn.close()

    return render_template('leaderboard.html', users=users)


@app.route('/badges')
def badges():
    if not check_login():
        return redirect('/login')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", 
                        (session['user'],)).fetchone()
    conn.close()

    score = user['score']

    if score >= 50:
        badge = "🏆 Pro"
    elif score >= 20:
        badge = "⭐ Intermediate"
    else:
        badge = "🔥 Beginner"

    return render_template('badges.html', badge=badge)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
