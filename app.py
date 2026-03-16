from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "studytrackersecret"

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["POST"])
def register():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if existing:
        conn.close()
        return "Username already exists"

    conn.execute(
        "INSERT INTO users(username,password,xp,level) VALUES(?,?,0,1)",
        (username, password)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()

    conn.close()

    if user:
        session["username"] = username
        return redirect("/dashboard")

    return "Invalid Login"


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = get_db()

    study_rows = conn.execute(
        "SELECT date, minutes FROM sessions WHERE username=?",
        (username,)
    ).fetchall()

    dates = [r["date"] for r in study_rows]
    minutes = [r["minutes"] for r in study_rows]

    total_study = sum(minutes) if minutes else 0
    sessions_count = len(minutes)

    streak = len(set(dates))

    game_rows = conn.execute(
        "SELECT minutes FROM game_sessions WHERE username=?",
        (username,)
    ).fetchall()

    game_total = sum([r["minutes"] for r in game_rows]) if game_rows else 0

    user = conn.execute(
        "SELECT xp,level FROM users WHERE username=?",
        (username,)
    ).fetchone()

    conn.close()

    coach = "Keep studying consistently!"

    if game_total > total_study:
        coach = "⚠ Try reducing game time and focus on studying."

    return render_template(
        "dashboard.html",
        username=username,
        total=total_study,
        sessions=sessions_count,
        streak=streak,
        dates=dates,
        minutes=minutes,
        study_total=total_study,
        game_total=game_total,
        xp=user["xp"],
        level=user["level"],
        coach_message=coach
    )


# ---------------- AUTO STUDY SESSION ----------------

@app.route("/auto_session")
def auto_session():

    if "username" not in session:
        return ""

    username = session["username"]

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()

    conn.execute(
        "INSERT INTO sessions(username,date,minutes) VALUES(?,?,25)",
        (username, today)
    )

    conn.execute(
        "UPDATE users SET xp = xp + 20 WHERE username=?",
        (username,)
    )

    conn.commit()
    conn.close()

    return "ok"


# ---------------- ADD GAME TIME ----------------

@app.route("/add_game", methods=["POST"])
def add_game():

    if "username" not in session:
        return redirect("/")

    username = session["username"]
    minutes = request.form["minutes"]

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()

    conn.execute(
        "INSERT INTO game_sessions(username,date,minutes) VALUES(?,?,?)",
        (username, today, minutes)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run()
