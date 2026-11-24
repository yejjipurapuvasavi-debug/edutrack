from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import sqlite3, os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
DB = os.path.join(os.path.dirname(__file__), "edutrack.db")

def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con

def init_db():
    con=db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, display_name TEXT, student_id TEXT);
    CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, student_id TEXT UNIQUE, name TEXT, branch TEXT, section TEXT, year TEXT, semester INTEGER, internal REAL, internal_max REAL, external REAL, external_max REAL, mid1 REAL, mid1_max REAL, mid2 REAL, mid2_max REAL, semester_points REAL, attendance REAL);
    CREATE TABLE IF NOT EXISTS marks_log(id INTEGER PRIMARY KEY, student_id TEXT, field TEXT, old_value TEXT, new_value TEXT, updated_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS attendance_log(id INTEGER PRIMARY KEY, student_id TEXT, period TEXT, percentage REAL);
    """)
    if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
        accounts=[
          ("admin","Admin@123","admin","Administrator",None),
          ("faculty","Faculty@123","faculty","Faculty Member",None),
          ("25KD1A05X8","Student@123","student","V. Bhuvana Kruthi","25KD1A05X8"),
          ("25KD1A05X4","Student@123","student","V. Gayathri","25KD1A05X4")]
        for u,p,r,n,s in accounts:
            con.execute("INSERT INTO users(username,password,role,display_name,student_id) VALUES(?,?,?,?,?)",(u,generate_password_hash(p),r,n,s))
    if con.execute("SELECT COUNT(*) FROM students").fetchone()[0]==0:
        rows=[
        ("25KD1A05X8","V. Bhuvana Kruthi","CSE","F","2nd Year",3,27,30,60,70,140,150,130,150,9.0,95),
        ("25KD1A05X4","V. Gayathri","CSE","F","2nd Year",3,25,30,62,70,135,150,140,150,8.9,85)]
        con.executemany("""INSERT INTO students(student_id,name,branch,section,year,semester,internal,internal_max,external,external_max,mid1,mid1_max,mid2,mid2_max,semester_points,attendance)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
        for sid,period,pct in [("25KD1A05X8","Semester 3",95),("25KD1A05X4","Semester 3",85)]:
            con.execute("INSERT INTO attendance_log(student_id,period,percentage) VALUES(?,?,?)",(sid,period,pct))
    con.commit(); con.close()

def login_required(f):
    @wraps(f)
    def wrapped(*args,**kwargs):
        if not session.get("user"): return redirect(url_for("login"))
        return f(*args,**kwargs)
    return wrapped

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapped(*args,**kwargs):
            if session.get("role") not in roles: return redirect(url_for("dashboard"))
            return f(*args,**kwargs)
        return wrapped
    return deco

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form.get("username","").strip()
        password=request.form.get("password","")
        con=db(); user=con.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone(); con.close()
        if user and check_password_hash(user["password"],password):
            session.update(user=user["display_name"],username=user["username"],role=user["role"],student_id=user["student_id"])
            return redirect(url_for("dashboard"))
        flash("Those sign-in details don't match. Please try again.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    con=db()
    if session["role"]=="student":
        student=con.execute("SELECT * FROM students WHERE student_id=?",(session["student_id"],)).fetchone()
        con.close()
        return render_template("student.html",student=student)
    students=con.execute("SELECT * FROM students ORDER BY branch,section,student_id").fetchall()
    branches=con.execute("SELECT COUNT(DISTINCT branch) FROM students").fetchone()[0]
    stats={"students":len(students),"branches":branches,"sections":len(set((s["branch"],s["section"]) for s in students))}
    con.close()
    return render_template("staff.html",students=students,stats=stats)

@app.route("/students")
@login_required
@role_required("admin","faculty")
def students():
    con=db()
    branch=request.args.get("branch","")
    section=request.args.get("section","")
    query="SELECT * FROM students WHERE 1=1"; args=[]
    if branch: query+=" AND branch=?"; args.append(branch)
    if section: query+=" AND section=?"; args.append(section)
    query+=" ORDER BY student_id"
    rows=con.execute(query,args).fetchall()
    branches=[r[0] for r in con.execute("SELECT DISTINCT branch FROM students ORDER BY branch")]
    con.close()
    return render_template("students.html",students=rows,branches=branches,branch=branch,section=section)

@app.route("/marks/<student_id>",methods=["GET","POST"])
@login_required
@role_required("admin","faculty")
def edit_marks(student_id):
    con=db(); s=con.execute("SELECT * FROM students WHERE student_id=?",(student_id,)).fetchone()
    if not s: con.close(); return redirect(url_for("students"))
    fields={"internal":("Internal","internal_max"),"external":("External","external_max"),"mid1":("Mid 1","mid1_max"),"mid2":("Mid 2","mid2_max"),"semester_points":("Semester points",None),"attendance":("Attendance",None)}
    if request.method=="POST":
        for field,(label,maxfield) in fields.items():
            raw=request.form.get(field,"").strip()
            if raw=="" or raw==str(s[field]): continue
            try: val=float(raw)
            except ValueError: continue
            if field=="attendance" and not 0<=val<=100: continue
            if maxfield and s[maxfield] is not None and not 0 <= val <= float(s[maxfield]): continue
            con.execute("INSERT INTO marks_log(student_id,field,old_value,new_value,updated_by) VALUES(?,?,?,?,?)",(student_id,field,str(s[field]),str(val),session["user"]))
            con.execute(f"UPDATE students SET {field}=? WHERE student_id=?",(val,student_id))
        con.commit(); flash("Student record updated successfully.","success")
        con.close(); return redirect(url_for("edit_marks",student_id=student_id))
    con.close(); return render_template("edit_marks.html",s=s)

@app.route("/add-student",methods=["POST"])
@login_required
@role_required("admin")
def add_student():
    data=[request.form.get(k,"").strip() for k in ["student_id","name","branch","section","year"]]
    if not all(data): flash("Please complete all student details.","error")
    else:
        con=db()
        try: con.execute("INSERT INTO students(student_id,name,branch,section,year,semester) VALUES(?,?,?,?,?,?)",(*data,int(request.form.get("semester",1))))
        except sqlite3.IntegrityError: flash("That student ID already exists.","error")
        else: flash("Student added. Marks can now be entered.","success")
        con.commit(); con.close()
    return redirect(url_for("students"))

@app.route("/api/student/<student_id>")
@login_required
def student_api(student_id):
    if session["role"]=="student" and session["student_id"]!=student_id: return jsonify({"error":"forbidden"}),403
    con=db(); s=con.execute("SELECT * FROM students WHERE student_id=?",(student_id,)).fetchone()
    logs=con.execute("SELECT period,percentage FROM attendance_log WHERE student_id=? ORDER BY id",(student_id,)).fetchall()
    con.close()
    if not s:return jsonify({"error":"not found"}),404
    return jsonify({"student":dict(s),"attendance":[dict(x) for x in logs]})

@app.route("/attendance/<student_id>",methods=["POST"])
@login_required
@role_required("admin","faculty")
def attendance(student_id):
    period=request.form.get("period","").strip()
    try: pct=float(request.form.get("percentage",""))
    except ValueError: pct=-1
    if period and 0<=pct<=100:
        con=db(); con.execute("INSERT INTO attendance_log(student_id,period,percentage) VALUES(?,?,?)",(student_id,period,pct))
        con.execute("UPDATE students SET attendance=? WHERE student_id=?",(pct,student_id)); con.commit(); con.close()
        flash("Attendance period saved.","success")
    else: flash("Enter a period and a percentage from 0 to 100.","error")
    return redirect(url_for("edit_marks",student_id=student_id))

@app.route("/activity")
@login_required
@role_required("admin")
def activity():
    con=db(); logs=con.execute("SELECT * FROM marks_log ORDER BY created_at DESC LIMIT 100").fetchall(); con.close()
    return render_template("activity.html",logs=logs)

@app.route("/report/<student_id>")
@login_required
def report(student_id):
    if session["role"]=="student" and session["student_id"]!=student_id: return redirect(url_for("dashboard"))
    con=db(); s=con.execute("SELECT * FROM students WHERE student_id=?",(student_id,)).fetchone(); con.close()
    if not s:return redirect(url_for("dashboard"))
    return render_template("report.html",s=s)

if __name__=="__main__":
    init_db()
    app.run(debug=True)
