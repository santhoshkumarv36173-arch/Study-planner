from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, StudyPlan, PlanTask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'studyplanner-secret-2024')

# Use PostgreSQL on production (Render), SQLite locally
database_url = os.environ.get('DATABASE_URL', 'sqlite:///studyplanner.db')

# Render provides postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Prevent DB connection issues
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True
}

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def format_time(hour):
    total_minutes = round(hour * 60)
    h = total_minutes // 60
    m = total_minutes % 60

    suffix = "AM" if h < 12 else "PM"

    display_h = h if h <= 12 else h - 12

    if display_h == 0:
        display_h = 12

    return f"{display_h}:{m:02d} {suffix}"

def generate_plan_tasks(subjects_list, hours):
    tasks = []

    total_subjects = len(subjects_list)

    break_duration = 0.25
    time_per_subject = hours / total_subjects

    current_time = 9

    for i, subject in enumerate(subjects_list):

        start = current_time
        end = current_time + time_per_subject

        tasks.append({
            "time": f"{format_time(start)} - {format_time(end)}",
            "task": f"Study {subject}",
            "type": "study"
        })

        current_time = end

        if i != total_subjects - 1:

            break_end = current_time + break_duration

            tasks.append({
                "time": f"{format_time(current_time)} - {format_time(break_end)}",
                "task": "Break ☕",
                "type": "break"
            })

            current_time = break_end

    tasks.append({
        "time": "Final 15 mins",
        "task": "Quick Revision 🔁",
        "type": "revision"
    })

    return tasks

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(
            username=username,
            email=email,
            password_hash=hashed
        )

        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):

            login_user(user)

            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash('You have been logged out.', 'success')

    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():

    plans = StudyPlan.query.filter_by(
        user_id=current_user.id
    ).order_by(
        StudyPlan.created_at.desc()
    ).all()

    total_tasks = sum(len(p.tasks) for p in plans)

    completed_tasks = sum(
        sum(1 for t in p.tasks if t.completed)
        for p in plans
    )

    return render_template(
        'dashboard.html',
        plans=plans,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks
    )

@app.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():

    plan = None

    if request.method == 'POST':

        subjects_raw = request.form.get('subjects', '')
        hours_raw = request.form.get('hours', '')
        action = request.form.get('action', 'preview')

        subjects_list = [
            s.strip()
            for s in subjects_raw.split(',')
            if s.strip()
        ]

        if not subjects_list:
            flash('Please enter at least one subject.', 'error')
            return render_template('planner.html')

        try:
            hours = float(hours_raw)

            if hours <= 0:
                raise ValueError

        except ValueError:
            flash('Please enter a valid number of hours.', 'error')
            return render_template('planner.html')

        tasks_data = generate_plan_tasks(subjects_list, hours)

        if action == 'save':

            title = f"Plan: {', '.join(subjects_list)}"

            new_plan = StudyPlan(
                user_id=current_user.id,
                title=title,
                subjects=subjects_raw,
                hours=hours
            )

            db.session.add(new_plan)
            db.session.flush()

            for t in tasks_data:

                task = PlanTask(
                    plan_id=new_plan.id,
                    time_slot=t['time'],
                    task=t['task'],
                    task_type=t['type']
                )

                db.session.add(task)

            db.session.commit()

            flash('Study plan saved!', 'success')

            return redirect(
                url_for(
                    'view_plan',
                    plan_id=new_plan.id
                )
            )

        plan = {
            "subjects": subjects_raw,
            "hours": hours,
            "tasks": tasks_data
        }

    return render_template(
        'planner.html',
        plan=plan
    )

@app.route('/plan/<int:plan_id>')
@login_required
def view_plan(plan_id):

    plan = StudyPlan.query.filter_by(
        id=plan_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template(
        'view_plan.html',
        plan=plan
    )

@app.route('/plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):

    plan = StudyPlan.query.filter_by(
        id=plan_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(plan)
    db.session.commit()

    flash('Plan deleted.', 'success')

    return redirect(url_for('dashboard'))

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):

    task = PlanTask.query.get_or_404(task_id)

    if task.plan.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    task.completed = not task.completed

    db.session.commit()

    return jsonify({
        'completed': task.completed,
        'progress': task.plan.progress
    })

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )