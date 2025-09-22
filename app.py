# app.py
from flask import Flask, render_template, request, redirect, url_for, session,flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.secret_key = "change_this_secret_for_prod"

DB = "internships.db"

def get_db_connection():
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    return conn
# translation filter
def translate_text(text):
    # don't translate empty or already translated simple labels
    lang = session.get("lang", "en")
    if not text or lang == "en":
        return text
    try:
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except Exception:
        return text

app.jinja_env.filters["tr"] = translate_text

@app.route("/", methods=["GET", "POST"])
def language_select():
    if request.method == "POST":
        session["lang"] = request.form.get("language") or "en"
        return redirect(url_for("login"))
    return render_template("language.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful!", "success")
            return redirect(url_for("student_info"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password),
            )
            conn.commit()
            flash("Signup successful! Please log in.", "success")
        except sqlite3.IntegrityError:
            flash("Email already exists. Please log in.", "danger")
            return redirect(url_for("login"))
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/student", methods=["GET", "POST"])
def student_info():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    if request.method == "POST":
        uid = session["user_id"]
        name = request.form.get("name") or ""
        age = request.form.get("age") or ""
        gender = request.form.get("gender") or ""
        course = request.form.get("course") or ""
        gpa = request.form.get("gpa") or ""
        skills = ",".join(request.form.getlist("skills"))
        locations = ",".join(request.form.getlist("locations"))
        roles = ",".join(request.form.getlist("roles"))
        user_location = request.form.get("user_location") or ""

        existing = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (uid,)).fetchone()
        if existing:
            conn.execute("""UPDATE profiles SET 
                            name=?, age=?, gender=?, course=?, gpa=?, skills=?, 
                            locations=?, roles=?, user_location=? 
                            WHERE user_id=?""",
                         (name, age, gender, course, gpa, skills, locations, roles, user_location, uid))
        else:
            conn.execute("""INSERT INTO profiles 
                            (user_id, name, age, gender, course, gpa, skills, locations, roles, user_location) 
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                         (uid, name, age, gender, course, gpa, skills, locations, roles, user_location))
        conn.commit()
        conn.close()
        return redirect(url_for("recommendations"))

    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (session["user_id"],)).fetchone()
    locations = [r[0] for r in conn.execute("SELECT DISTINCT location FROM internships WHERE location IS NOT NULL").fetchall()]
    roles = [r[0] for r in conn.execute("SELECT DISTINCT title FROM internships WHERE title IS NOT NULL").fetchall()]
    tag_rows = conn.execute("SELECT description, tags FROM internships WHERE description IS NOT NULL OR tags IS NOT NULL").fetchall()
    conn.close()

    # build tag pool from description + tags
    all_tags = set()
    for row in tag_rows:
        combined = " ".join([x for x in row if x])
        for token in combined.replace(",", " ").split():
            clean = ''.join(ch for ch in token if ch.isalpha())
            if len(clean) > 2:
                all_tags.add(clean.capitalize())
    skills_list = sorted(all_tags)

    return render_template("student_info.html", profile=profile, locations=locations, roles=roles, skills_list=skills_list)

@app.route("/recommendations")
def recommendations():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (session["user_id"],)).fetchone()
    internships = conn.execute("SELECT * FROM internships").fetchall()
    conn.close()

    recos = []
    if profile:
        # profile fields -> lists, lowercased for matching
        skills = [s.strip().lower() for s in (profile["skills"] or "").split(",") if s.strip()]
        pref_roles = [r.strip().lower() for r in (profile["roles"] or "").split(",") if r.strip()]
        pref_locations = [l.strip().lower() for l in (profile["locations"] or "").split(",") if l.strip()]

        for it in internships:
            # convert Row -> dict for safe template access
            job = dict(it)

            job_title = (job.get("title") or "").lower()
            job_location = (job.get("location") or "").lower()
            job_tags = (job.get("tags") or "").lower()

            score = 0
            total = 0

            # Skills weight = 50
            total += 50
            if skills:
                # count matches of skills in tags (allow partial)
                skill_matches = sum(1 for s in skills if s in job_tags)
                if skill_matches:
                    # give proportion of skill matches (capped)
                    # e.g. if 2 selected skills and 1 matches -> 50*(1/2)
                    score += int(50 * min(1.0, skill_matches / max(1, len(skills))))

            # Role/title weight = 30
            total += 30
            if pref_roles and any(r in job_title for r in pref_roles):
                score += 30

            # Location weight = 20
            total += 20
            if pref_locations and any(l in job_location for l in pref_locations):
                score += 20

            # only include items with some score
            if score > 0:
                percentage = int(round((score / total) * 100))
                recos.append({"job": job, "percentage": percentage})

        # sort descending by percentage
        recos.sort(key=lambda x: x["percentage"], reverse=True)

    # pass current user's name if needed
    name = session.get("user_name")
    return render_template("recommendations.html", recos=recos[:6], name=name)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
