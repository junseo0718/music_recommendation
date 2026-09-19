from flask import Flask, render_template, request
from requests.exceptions import RequestException
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from weather_api import get_current_weather
from recommender import get_current_season, get_recommendation_genres
from spotify_api import SpotifyConfigurationError, get_top_tracks

app = Flask(__name__, template_folder=".")
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("RENDER") == "true",
)
DATABASE = Path(__file__).with_name("users.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth"))
        return view(*args, **kwargs)
    return wrapped_view


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token
init_db()


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if "user_id" in session:
        return redirect(url_for("index"))

    mode = request.args.get("mode", "login")
    error = None

    if request.method == "POST":
        mode = request.form.get("mode", "login")
        if not secrets.compare_digest(
            request.form.get("csrf_token", ""), session.get("csrf_token", "")
        ):
            error = "요청이 만료되었습니다. 다시 시도해 주세요."
        elif mode == "signup":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            password_confirm = request.form.get("password_confirm", "")
            if not name or not email or not password:
                error = "모든 항목을 입력해 주세요."
            elif "@" not in email:
                error = "올바른 이메일 주소를 입력해 주세요."
            elif len(password) < 8:
                error = "비밀번호는 8자 이상이어야 합니다."
            elif password != password_confirm:
                error = "비밀번호가 서로 일치하지 않습니다."
            else:
                try:
                    with get_db() as connection:
                        cursor = connection.execute(
                            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                            (name, email, generate_password_hash(password)),
                        )
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    session["user_name"] = name
                    return redirect(url_for("index"))
                except sqlite3.IntegrityError:
                    error = "이미 가입된 이메일입니다. 로그인해 주세요."
        else:
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            with get_db() as connection:
                user = connection.execute(
                    "SELECT * FROM users WHERE email = ?", (email,)
                ).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "이메일 또는 비밀번호를 확인해 주세요."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("index"))

    return render_template("auth.html", mode=mode, error=error)


@app.post("/logout")
def logout():
    if secrets.compare_digest(
        request.form.get("csrf_token", ""), session.get("csrf_token", "")
    ):
        session.clear()
    return redirect(url_for("auth"))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    recommendations = []
    weather_info = None
    error = None
    city = request.form.get("city", "Bucheon").strip()
    season = get_current_season()

    if request.method == "POST":
        if not city:
            error = "도시 이름을 입력해 주세요."
        else:
            try:
                weather_info = get_current_weather(city)
                genres = get_recommendation_genres(season, weather_info["weather"])
                recommendations = get_top_tracks(genres, 10)
            except RequestException:
                error = "날씨 또는 음악 서비스에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요."
            except SpotifyConfigurationError as exc:
                error = str(exc)
            except ValueError:
                error = "도시를 찾을 수 없거나 서비스 응답을 읽을 수 없습니다. 도시 이름을 확인해 주세요."

    return render_template(
        "index.html", season=season, city=city, error=error,
        weather_info=weather_info, recommendations=recommendations,
    )


if __name__ == "__main__":
    app.run(debug=True)

