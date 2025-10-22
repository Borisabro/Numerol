from collections import deque
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session
from numerology import life_path, expression, COLOR_MAP

BASEDIR = Path(__file__).resolve().parent
IMAGES_DIR = BASEDIR / "static" / "images"

app = Flask(__name__)
app.secret_key = "change_me_please"  # replace with secure value in production

# Store global history (in-memory). In production, switch to persistent DB like SQLite.
history: deque = deque(maxlen=10)

AVAILABLE_BACKGROUNDS = [img.name for img in IMAGES_DIR.glob("bg*")]
DEFAULT_BG = AVAILABLE_BACKGROUNDS[0] if AVAILABLE_BACKGROUNDS else None


def add_to_history(calc_type: str, value: str, result: int):
    history.appendleft({
        "type": calc_type,
        "value": value,
        "result": result,
        "color": COLOR_MAP.get(calc_type, "#000000"),
    })


@app.context_processor
def inject_global():
    return {
        "history": list(history),
        "background": session.get("background", DEFAULT_BG),
        "available_backgrounds": AVAILABLE_BACKGROUNDS,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        calc_type = request.form.get("calc_type")
        try:
            if calc_type == "life_path":
                date_str = request.form.get("birth_date", "")
                num, desc = life_path(date_str)
                add_to_history("life_path", date_str, num)
                flash(f"Ваш жизненный путь: {num}. {desc}", "success")
            elif calc_type == "expression":
                name = request.form.get("full_name", "")
                num, desc = expression(name)
                add_to_history("expression", name, num)
                flash(f"Ваше число судьбы: {num}. {desc}", "success")
            else:
                flash("Неизвестный тип расчёта", "danger")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/set_background/<bg>")
def set_background(bg: str):
    if bg in AVAILABLE_BACKGROUNDS:
        session["background"] = bg
    else:
        flash("Недопустимое изображение", "warning")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)