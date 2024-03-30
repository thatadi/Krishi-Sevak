from flask import Blueprint, render_template,request,flash,redirect,url_for
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash
from .import db 
from flask_login import login_user , login_required,logout_user,current_user
auth = Blueprint('auth',__name__)

@auth.route('/login',methods=["GET","POST"])
def login():
    if request.method =='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user :
            if check_password_hash(user.password,password):
                flash('Logged in successfully',category='success')
                login_user(user,remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again',category='error')
        else:
            flash('Email does not exist.',category='error')   
    return render_template('login.html')

@auth.route('/signup',methods=["GET","POST"])
def signup():
    if request.method == 'POST':
        email=request.form.get('email')
        firstName=request.form.get('firstName')
        password1=request.form.get('password1')
        password2=request.form.get('password2')
        lastName=request.form.get('lastName')
        farmArea=request.form.get('area')
        state=request.form.get('state')
        district=request.form.get('district')

        user=User.query.filter_by(email=email).first()
        if user:
            flash("This Email is already registered.", category="error")
            return redirect(url_for('auth.signup'))

        if password1 != password2:
            flash('Passwords do not match',category='error')
        if int(farmArea) < 2 :
             flash('Farm Area must be greater than 2 sq.m',category='error')
        if len(password1) < 7 :
             flash('Password must be greater than 7 characters',category='error')
        if len(firstName) < 1 :
             flash('First Name must be greater than 1 character',category='error')
        if len(state) < 2 :
             flash('State must be greater than 7 characters',category='error')
        if len(district) < 2 :
             flash('District must be greater than 7 characters',category='error')
        if len(email) < 4:
            flash('Email must be greater than 4 characters',category='error')
        else:
            flash('Account created!',category='success')
            new_user=User(email=email,first_name=firstName,password=generate_password_hash(password1,method='sha256'),last_name=lastName,state=state,district=district,farm_area=farmArea)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user,remember=True)
            return  redirect(url_for('views.home'))
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def loggedout():
    logout_user()
    return redirect(url_for('views.base'))