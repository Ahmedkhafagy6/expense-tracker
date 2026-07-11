import os
from datetime import date
from flask import Flask, jsonify, request, session, redirect, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///expenses.db")
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    note = db.Column(db.String(200))
    day = db.Column(db.Date, default=date.today)

with app.app_context():
    db.create_all()

PAGE = """
<!doctype html><title>Expense Tracker</title>
<style>body{font-family:sans-serif;max-width:640px;margin:2em auto}input,select{margin:4px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left}</style>
<h2>Expense Tracker — {{user}}</h2>
<form method=post action="/add">
  <input name=amount type=number step=0.01 placeholder="Amount" required>
  <select name=category>{% for c in ["Food","Coffee","Gym","Transport","Bills","Other"] %}<option>{{c}}</option>{% endfor %}</select>
  <input name=note placeholder="Note">
  <button>Add</button>
</form>
<h3>This month by category</h3>
<table>{% for cat, total in totals %}<tr><td>{{cat}}</td><td>{{"%.2f"|format(total)}}</td></tr>{% endfor %}
<tr><th>Total</th><th>{{"%.2f"|format(grand)}}</th></tr></table>
<h3>Latest expenses</h3>
<table>{% for e in expenses %}<tr><td>{{e.day}}</td><td>{{e.category}}</td><td>{{e.note or ""}}</td><td>{{"%.2f"|format(e.amount)}}</td></tr>{% endfor %}</table>
<p><a href="/logout">Logout</a></p>
"""

AUTH = """
<!doctype html><title>Login</title>
<style>body{font-family:sans-serif;max-width:320px;margin:4em auto}input{display:block;margin:8px 0;width:100%}</style>
<h2>{{mode}}</h2>
<form method=post><input name=username placeholder=Username required>
<input name=password type=password placeholder=Password required><button>{{mode}}</button></form>
<p>{{msg}}</p><a href="{{alt_link}}">{{alt_text}}</a>
"""

@app.route("/health")
def health():
    return jsonify(status="ok")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(username=request.form["username"]).first():
            return render_template_string(AUTH, mode="Register", msg="Username taken", alt_link="/login", alt_text="Login instead")
        u = User(username=request.form["username"], password_hash=generate_password_hash(request.form["password"]))
        db.session.add(u); db.session.commit()
        return redirect("/login")
    return render_template_string(AUTH, mode="Register", msg="", alt_link="/login", alt_text="Login instead")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(username=request.form["username"]).first()
        if u and check_password_hash(u.password_hash, request.form["password"]):
            session["uid"], session["uname"] = u.id, u.username
            return redirect("/")
        return render_template_string(AUTH, mode="Login", msg="Wrong credentials", alt_link="/register", alt_text="Register instead")
    return render_template_string(AUTH, mode="Login", msg="", alt_link="/register", alt_text="Register instead")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def home():
    if "uid" not in session:
        return redirect("/login")
    first = date.today().replace(day=1)
    expenses = Expense.query.filter_by(user_id=session["uid"]).order_by(Expense.day.desc()).limit(20).all()
    month = Expense.query.filter(Expense.user_id == session["uid"], Expense.day >= first).all()
    totals = {}
    for e in month:
        totals[e.category] = totals.get(e.category, 0) + e.amount
    return render_template_string(PAGE, user=session["uname"], expenses=expenses,
                                  totals=sorted(totals.items()), grand=sum(totals.values()))

@app.route("/add", methods=["POST"])
def add():
    if "uid" not in session:
        return redirect("/login")
    db.session.add(Expense(user_id=session["uid"], amount=float(request.form["amount"]),
                           category=request.form["category"], note=request.form["note"]))
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)