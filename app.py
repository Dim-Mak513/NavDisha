# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# --- Database setup (PostgreSQL on Render) ---
# PostgreSQL connection from Render environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///internships.db"   # fallback for local dev
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.String(10))
    gender = db.Column(db.String(20))
    course = db.Column(db.String(100))
    gpa = db.Column(db.String(10))
    skills = db.Column(db.Text)
    locations = db.Column(db.Text)
    roles = db.Column(db.Text)
    user_location = db.Column(db.String(200))


class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    tags = db.Column(db.Text)
    stipend = db.Column(db.String(50))
    url = db.Column(db.String(500))


# --- Translation filter ---
def translate_text(text):
    lang = session.get("lang", "en")
    if not text or lang == "en":
        return text
    try:
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except Exception:
        return text


app.jinja_env.filters["tr"] = translate_text


# --- Routes ---
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

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_name"] = user.name
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

        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/student", methods=["GET", "POST"])
def student_info():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    uid = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name") or ""
        age = request.form.get("age") or ""
        gender = request.form.get("gender") or ""
        course = request.form.get("course") or ""
        gpa = request.form.get("gpa") or ""
        skills = ",".join(request.form.getlist("skills"))
        locations = ",".join(request.form.getlist("locations"))
        roles = ",".join(request.form.getlist("roles"))
        user_location = request.form.get("user_location") or ""

        profile = Profile.query.filter_by(user_id=uid).first()
        if profile:
            profile.name = name
            profile.age = age
            profile.gender = gender
            profile.course = course
            profile.gpa = gpa
            profile.skills = skills
            profile.locations = locations
            profile.roles = roles
            profile.user_location = user_location
        else:
            profile = Profile(
                user_id=uid,
                name=name,
                age=age,
                gender=gender,
                course=course,
                gpa=gpa,
                skills=skills,
                locations=locations,
                roles=roles,
                user_location=user_location,
            )
            db.session.add(profile)

        db.session.commit()
        return redirect(url_for("recommendations"))

    # fetch profile if exists
    profile = Profile.query.filter_by(user_id=uid).first()

    # distinct locations & roles
    locations = [loc[0] for loc in db.session.query(Internship.location).distinct() if loc[0]]
    roles = [role[0] for role in db.session.query(Internship.title).distinct() if role[0]]

    # build tag pool
    tag_rows = Internship.query.with_entities(Internship.description, Internship.tags).all()
    all_tags = set()
    for desc, tags in tag_rows:
        combined = " ".join([x for x in [desc, tags] if x])
        for token in combined.replace(",", " ").split():
            clean = "".join(ch for ch in token if ch.isalpha())
            if len(clean) > 2:
                all_tags.add(clean.capitalize())
    skills_list = sorted(all_tags)

    return render_template("student_info.html", profile=profile, locations=locations, roles=roles, skills_list=skills_list)


@app.route("/recommendations")
def recommendations():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    profile = Profile.query.filter_by(user_id=session["user_id"]).first()
    internships = Internship.query.all()

    recos = []
    if profile:
        skills = [s.strip().lower() for s in (profile.skills or "").split(",") if s.strip()]
        pref_roles = [r.strip().lower() for r in (profile.roles or "").split(",") if r.strip()]
        pref_locations = [l.strip().lower() for l in (profile.locations or "").split(",") if l.strip()]

        for it in internships:
            job = {
                "id": it.id,
                "title": it.title,
                "location": it.location,
                "description": it.description,
                "tags": it.tags,
            }

            job_title = (job.get("title") or "").lower()
            job_location = (job.get("location") or "").lower()
            job_tags = (job.get("tags") or "").lower()

            score = 0
            total = 0

            # Skills weight = 50
            total += 50
            if skills:
                skill_matches = sum(1 for s in skills if s in job_tags)
                if skill_matches:
                    score += int(50 * min(1.0, skill_matches / max(1, len(skills))))

            # Role weight = 30
            total += 30
            if pref_roles and any(r in job_title for r in pref_roles):
                score += 30

            # Location weight = 20
            total += 20
            if pref_locations and any(l in job_location for l in pref_locations):
                score += 20

            if score > 0:
                percentage = int(round((score / total) * 100))
                recos.append({"job": job, "percentage": percentage})

        recos.sort(key=lambda x: x["percentage"], reverse=True)

    name = session.get("user_name")
    return render_template("recommendations.html", recos=recos[:6], name=name)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# --- Main ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensures tables exist
    app.run(debug=True)
