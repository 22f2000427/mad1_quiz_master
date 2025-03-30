from models.models import Users, db
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

login_bp = Blueprint('login_bp', __name__)


@login_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = Users.query.filter_by(username=username).first()  

    if user and check_password_hash(user.password_hash, password): 
        login_user(user)  

       
        if user.role == 'admin':
            return redirect(url_for('admin_bp.admin_dashboard'))  
        else:
            return redirect(url_for('user_bp.user_dashboard'))  

    flash("Invalid username or password", "danger")
    return redirect(url_for('login_bp.render_login_page'))  


@login_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get("email", "").strip()  
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    qualification = request.form.get('qualification')
    dob = request.form.get('dob', "").strip()

    
    if not email:
        flash("Email is required!", "danger")
        return redirect(url_for("login_bp.render_register_page"))

    try:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD.", "danger")
        return redirect(url_for("login_bp.render_register_page"))

    role = 'user'  

    
    existing_user = Users.query.filter(
        (Users.username == username) | (Users.email == email)
    ).first()

    if existing_user:
        flash('Username or Email already exists!', 'danger')
        return redirect(url_for('login_bp.render_register_page'))

    
    hashed_password = generate_password_hash(password)

    new_user = Users(
        username=username,
        email=email,  
        password_hash=hashed_password,
        full_name=full_name,
        qualification=qualification,
        dob=dob,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login_bp.render_login_page'))

@login_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('login_bp.render_login_page'))


@login_bp.route('/display_register_page', methods=['GET'])
def render_register_page():
    return render_template('register.html')

@login_bp.route('/display_login_page')
def render_login_page():
    return render_template('login.html')

