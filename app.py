from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secretkey"

DB = "database.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("home.html")


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


# ---------------- BADGE CHECKER ----------------

def check_badges(username):

    conn = get_db()

    sessions = conn.execute(
        "SELECT COUNT(*) as count FROM sessions WHERE username=?",
        (username,)
    ).fetchone()["count"]

    user = conn.execute(
        "SELECT level FROM users WHERE username=?",
        (username,)
    ).fetchone()

    level = user["level"]

    badges = conn.execute(
        "SELECT badge_name FROM badges WHERE username=?",
        (username,)
    ).fetchall()

    badge_names = [b["badge_name"] for b in badges]

    if sessions >= 5 and "5 Sessions" not in badge_names:
        conn.execute(
            "INSERT INTO badges(username,badge_name) VALUES(?,?)",
            (username,"5 Sessions")
        )

    if sessions >= 10 and "10 Sessions" not in badge_names:
        conn.execute(
            "INSERT INTO badges(username,badge_name) VALUES(?,?)",
            (username,"10 Sessions")
        )

    if level >= 5 and "Level 5 Achiever" not in badge_names:
        conn.execute(
            "INSERT INTO badges(username,badge_name) VALUES(?,?)",
            (username,"Level 5 Achiever")
        )

    conn.commit()
    conn.close()


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    check_badges(username)

    conn = get_db()

    user = conn.execute(
        "SELECT xp, level FROM users WHERE username=?",
        (username,)
    ).fetchone()

    xp = user["xp"]
    level = user["level"]

    rows = conn.execute(
        "SELECT date, minutes FROM sessions WHERE username=?",
        (username,)
    ).fetchall()

    dates = [r["date"] for r in rows]
    minutes = [r["minutes"] for r in rows]

    total = sum(minutes) if minutes else 0
    sessions = len(minutes)

    streak = len(set(dates))

    game_rows = conn.execute(
        "SELECT minutes FROM game_sessions WHERE username=?",
        (username,)
    ).fetchall()

    game_total = sum([r["minutes"] for r in game_rows]) if game_rows else 0

    study_total = total

    if study_total < game_total:
        coach_message = "⚠ You played more than you studied."
    elif sessions >= 3:
        coach_message = "🔥 Excellent study consistency!"
    else:
        coach_message = "👍 Keep going."

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        total=total,
        sessions=sessions,
        streak=streak,
        dates=dates,
        minutes=minutes,
        study_total=study_total,
        game_total=game_total,
        xp=xp,
        level=level,
        coach_message=coach_message
    )


# ---------------- STUDY TIMER SAVE ----------------

@app.route("/auto_session")
def auto_session():

    if "username" not in session:
        return ""

    username = session["username"]

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()

    conn.execute(
        "INSERT INTO sessions(username,date,minutes) VALUES(?,?,?)",
        (username, today, 25)
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


# ---------------- LEADERBOARD ----------------

@app.route("/leaderboard")
def leaderboard():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT username,
        SUM(minutes) as total_minutes
        FROM sessions
        GROUP BY username
        ORDER BY total_minutes DESC
        """
    ).fetchall()

    conn.close()

    return render_template("leaderboard.html", leaderboard=rows)


# ---------------- PROFILE ----------------

@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = get_db()

    user = conn.execute(
        "SELECT xp, level FROM users WHERE username=?",
        (username,)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        username=username,
        xp=user["xp"],
        level=user["level"]
    )


# ---------------- BADGES PAGE ----------------

@app.route("/badges")
def badges():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = get_db()

    rows = conn.execute(
        "SELECT badge_name FROM badges WHERE username=?",
        (username,)
    ).fetchall()

    conn.close()

    return render_template("badges.html", badges=rows)


# ---------------- ANALYTICS ----------------

@app.route("/analytics")
def analytics():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    conn = get_db()

    study_rows = conn.execute(
        "SELECT date, minutes FROM sessions WHERE username=?",
        (username,)
    ).fetchall()

    game_rows = conn.execute(
        "SELECT date, minutes FROM game_sessions WHERE username=?",
        (username,)
    ).fetchall()

    week_days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    study_minutes = [0,0,0,0,0,0,0]
    game_minutes = [0,0,0,0,0,0,0]

    for row in study_rows:
        day = datetime.strptime(row["date"], "%Y-%m-%d").weekday()
        study_minutes[day] += row["minutes"]

    for row in game_rows:
        day = datetime.strptime(row["date"], "%Y-%m-%d").weekday()
        game_minutes[day] += row["minutes"]

    conn.close()

    return render_template(
        "analytics.html",
        week_days=week_days,
        study_minutes=study_minutes,
        game_minutes=game_minutes
    )


if __name__ == "__main__":
    app.run()