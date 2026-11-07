from flask import Flask, render_template, jsonify, request
from database import get_db, init_db
from datetime import date, timedelta

app = Flask(__name__)

init_db()


def today():
    return date.today().isoformat()


def calculate_streak(conn):

    rows = conn.execute("""
        SELECT DISTINCT completed_on
        FROM completions
        ORDER BY completed_on DESC
    """).fetchall()

    completed_dates = {
        date.fromisoformat(row["completed_on"])
        for row in rows
    }

    current = date.today()

    if current not in completed_dates:
        current -= timedelta(days=1)

    streak = 0

    while current in completed_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard():

    conn = get_db()

    habits = conn.execute("""
        SELECT
            h.id,
            h.name,
            h.description,
            h.icon,

            CASE WHEN c.id IS NOT NULL
            THEN 1 ELSE 0 END AS completed

        FROM habits h

        LEFT JOIN completions c
        ON h.id = c.habit_id
        AND c.completed_on = ?

        ORDER BY h.id DESC
    """, (today(),)).fetchall()

    seeds = conn.execute("""
        SELECT seeds FROM app_state WHERE id = 1
    """).fetchone()["seeds"]

    total = len(habits)

    completed = sum(h["completed"] for h in habits)

    streak = calculate_streak(conn)

    plants = conn.execute("""
        SELECT
            up.id,
            p.name,
            p.emoji
        FROM user_plants up
        JOIN plants p ON up.plant_id = p.id
    """).fetchall()

    shop = conn.execute("""
        SELECT * FROM plants
    """).fetchall()

    weekly = []

    for i in range(6, -1, -1):

        day = date.today() - timedelta(days=i)

        count = conn.execute("""
            SELECT COUNT(*)
            FROM completions
            WHERE completed_on = ?
        """, (day.isoformat(),)).fetchone()[0]

        weekly.append({
            "day": day.strftime("%a"),
            "count": count
        })

    achievements = [
        {
            "name": "First Steps",
            "description": "Complete your first habit",
            "emoji": "🌱",
            "unlocked": conn.execute(
                "SELECT COUNT(*) FROM completions"
            ).fetchone()[0] >= 1
        },
        {
            "name": "Growing Strong",
            "description": "Complete 5 habits",
            "emoji": "🌿",
            "unlocked": conn.execute(
                "SELECT COUNT(*) FROM completions"
            ).fetchone()[0] >= 5
        },
        {
            "name": "Garden Lover",
            "description": "Own 3 plants",
            "emoji": "🌻",
            "unlocked": len(plants) >= 3
        },
        {
            "name": "Consistency",
            "description": "Maintain a 7-day streak",
            "emoji": "🔥",
            "unlocked": streak >= 7
        }
    ]

    result = {
        "habits": [dict(h) for h in habits],
        "seeds": seeds,
        "completed": completed,
        "total": total,
        "streak": streak,
        "plants": [dict(p) for p in plants],
        "shop": [dict(p) for p in shop],
        "weekly": weekly,
        "achievements": achievements
    }

    conn.close()

    return jsonify(result)


# ADD HABIT

@app.route("/api/habits", methods=["POST"])
def add_habit():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    icon = data.get("icon", "🌱")

    if not name or len(name) > 40:
        return jsonify({"error": "Enter a valid habit name."}), 400

    if len(description) > 100:
        return jsonify({"error": "Description is too long."}), 400

    if len(icon) > 10:
        icon = "🌱"

    conn = get_db()

    conn.execute("""
        INSERT INTO habits (name, description, icon)
        VALUES (?, ?, ?)
    """, (name, description, icon))

    conn.commit()
    conn.close()

    return jsonify({"message": "Habit added successfully!"})


# EDIT HABIT

@app.route("/api/habits/<int:habit_id>", methods=["PUT"])
def edit_habit(habit_id):

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name or len(name) > 40:
        return jsonify({"error": "Enter a valid habit name."}), 400

    if len(description) > 100:
        return jsonify({"error": "Description is too long."}), 400

    conn = get_db()

    cursor = conn.execute("""
        UPDATE habits
        SET name = ?, description = ?
        WHERE id = ?
    """, (name, description, habit_id))

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Habit not found."}), 404

    return jsonify({"message": "Habit updated!"})


# DELETE HABIT

@app.route("/api/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM habits WHERE id = ?
    """, (habit_id,))

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Habit not found."}), 404

    return jsonify({"message": "Habit deleted!"})


# COMPLETE HABIT

@app.route("/api/habits/<int:habit_id>/complete", methods=["POST"])
def complete_habit(habit_id):

    conn = get_db()

    habit = conn.execute("""
        SELECT id FROM habits WHERE id = ?
    """, (habit_id,)).fetchone()

    if not habit:
        conn.close()
        return jsonify({"error": "Habit not found."}), 404

    try:

        conn.execute("""
            INSERT INTO completions (habit_id, completed_on)
            VALUES (?, ?)
        """, (habit_id, today()))

        conn.execute("""
            UPDATE app_state
            SET seeds = seeds + 10
            WHERE id = 1
        """)

        conn.commit()

        message = "Habit completed! You earned 10 seeds 🌱"

    except Exception:

        conn.rollback()
        conn.close()

        return jsonify({
            "error": "This habit is already completed today."
        }), 409

    conn.close()

    return jsonify({"message": message})


# UNDO COMPLETION

@app.route("/api/habits/<int:habit_id>/complete", methods=["DELETE"])
def undo_completion(habit_id):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM completions
        WHERE habit_id = ? AND completed_on = ?
    """, (habit_id, today()))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Completion not found."}), 404

    conn.execute("""
        UPDATE app_state
        SET seeds = MAX(0, seeds - 10)
        WHERE id = 1
    """)

    conn.commit()
    conn.close()

    return jsonify({"message": "Completion undone."})


# BUY PLANT

@app.route("/api/plants/<int:plant_id>/buy", methods=["POST"])
def buy_plant(plant_id):

    conn = get_db()

    plant = conn.execute("""
        SELECT * FROM plants WHERE id = ?
    """, (plant_id,)).fetchone()

    if not plant:
        conn.close()
        return jsonify({"error": "Plant not found."}), 404

    seeds = conn.execute("""
        SELECT seeds FROM app_state WHERE id = 1
    """).fetchone()["seeds"]

    if seeds < plant["cost"]:
        conn.close()
        return jsonify({"error": "Not enough seeds!"}), 400

    conn.execute("""
        UPDATE app_state
        SET seeds = seeds - ?
        WHERE id = 1
    """, (plant["cost"],))

    conn.execute("""
        INSERT INTO user_plants (plant_id)
        VALUES (?)
    """, (plant_id,))

    conn.commit()
    conn.close()

    return jsonify({"message": "Plant purchased! 🌷"})


if __name__ == "__main__":
    app.run(debug=True)