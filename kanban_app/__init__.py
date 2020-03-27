from flask_login import LoginManager, UserMixin, login_user, login_required,logout_user,current_user
from wtforms import StringField, PasswordField, BooleanField, DateField, SelectField, SubmitField
from flask import Flask, render_template, redirect, url_for, send_from_directory, flash, request
from wtforms.validators import InputRequired, Email, Length, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from datetime import datetime
import sys
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
prj_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = "sqlite:///{}".format(os.path.join(prj_dir,"users.db"))
app.config['SQLALCHEMY_DATABASE_URI'] = db_dir
Bootstrap(app)
db = SQLAlchemy(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(50),unique = True)
    email = db.Column(db.String(100),unique = True)
    password = db.Column(db.String(20))
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    
class Task(db.Model, UserMixin):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    description = db.Column(db.String(100))
    begin = db.Column(db.Date, default = datetime.now())
    end = db.Column(db.Date)
    typ = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
db.create_all()
db.session.commit()

todayd = datetime.today()
today = str(todayd.month) + '-' + str(todayd.day) + '-' + str(todayd.year)

class Login(FlaskForm):
    username = StringField('Username',validators = [InputRequired(),Length(min=3,max=50)])
    password = PasswordField('Password',validators = [InputRequired(),Length(min=8,max=80)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log in')

class Signup(FlaskForm):
    email = StringField('Email',validators=[InputRequired(),Email(message='Invalid Email'),Length(max=100)])
    username = StringField('Username',validators = [InputRequired(),Length(min=3,max=50)])
    password = PasswordField('Password',validators = [InputRequired(),Length(min=8,max=80)])
    submit = SubmitField('Sign Up')

class add(FlaskForm):
    title = StringField('Title',validators = [InputRequired,Length(max = 50)],render_kw={"placeholder": "Write Title Here"})
    description = StringField('Description',validators = [InputRequired(), Length(max = 100)],render_kw={"placeholder": "Write Description Here"})
    begin = DateField('Start Date',format='%m-%d-%Y',render_kw={"placeholder": today})
    end = DateField('Deadline', format='%m-%d-%Y', validators = [DataRequired(), Length(min=10,max=12)],render_kw={"placeholder": "MM-DD-YYYY"})
    typ = SelectField('Status',choices = [( 'todo', 'To Do'), ( 'inprogress','In Progress'), ('complete','Complete')])
    submit = SubmitField('Submit')



@app.route('/login', methods = ['GET','POST'])
def login():
    form = Login() 

    if form.validate_on_submit():
        #return '<h1>' + form.username.data +' '+form.password.data + '</h1>'
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password,form.password.data):
                login_user(user,remember=form.remember.data)
                return redirect(url_for('board'))
            
        return redirect(url_for('login_failed'))

    return render_template('login.html',form = form)


@app.route('/public/<path:path>')
def send_resource(path):
    return send_from_directory('public', path)

@app.route('/login_failed', methods = ['GET','POST'])
def login_failed():
    form = Login() 

    if form.validate_on_submit():
        #return '<h1>' + form.username.data +' '+form.password.data + '</h1>'
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password,form.password.data):
                login_user(user,remember=form.remember.data)
                return redirect(url_for('board'))
            
        return redirect(url_for('login_failed'))

    return render_template('login_failed.html',form=form)

@app.route('/', methods = ['GET','POST'])
@app.route('/signup', methods = ['GET','POST'])
def signup():
    form = Signup()

    if form.validate_on_submit():
        h_pass = generate_password_hash(form.password.data,method = 'sha256')     
        new_user = User(username = form.username.data,email=form.email.data,password=h_pass)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html',form=form)

@app.route('/board')
@login_required
def board():

    todo = Task.query.filter_by(typ='todo').all()
    inprogress = Task.query.filter_by(typ='inprogress').all()
    complete = Task.query.filter_by(typ='complete').all()

    return render_template('board.html', todo=todo, inprogress=inprogress, complete=complete, name =current_user.username)


@app.route("/add", methods=["GET", "POST"])
def addtask():

    form = add()

    if form.is_submitted():
        #print('<h1>' + form.typ.data + '</h1>')
        new_task = Task(title = form.title.data,description=form.description.data,begin=form.begin.data,end=form.end.data,typ=form.typ.data)
        db.session.add(new_task)
        db.session.commit()
        flash('<h1> Great! Your new task has been added.</h1>')
        return redirect(url_for('addtask'))

    return render_template('add.html',form=form,name =current_user.username)

@app.route('/todo', methods=['POST', 'GET'])
def todo():

    todo = Task.query.filter_by(typ='todo').all()

    return render_template('todo.html',todo=todo,name =current_user.username)

@app.route('/inprogress', methods=['POST', 'GET'])
def inprog():

    inprogress = Task.query.filter_by(typ='inprogress').all()

    return render_template('inprogress.html',inprogress=inprogress,name =current_user.username)

@app.route('/complete', methods=['POST', 'GET'])
def complete():

    complete = Task.query.filter_by(typ='complete').all()

    return render_template('complete.html',complete=complete,name =current_user.username)

@app.route('/delete', methods = ['POST'])
def delete():

    title = request.form.get('title')
    task = Task.query.filter_by(title=title).first()
    db.session.delete(task)
    db.session.commit()

    return redirect(url_for('board'))

@app.route('/start', methods = ['POST'])
def start():

    title = request.form.get('title')
    task = Task.query.filter_by(title=title).first()
    task.typ = 'inprogress'
    db.session.commit()
    
    return redirect(url_for('inprog'))

@app.route('/mark_complete', methods = ['POST'])
def mark_complete():

    title = request.form.get('title')
    task = Task.query.filter_by(title=title).first()
    task.typ = 'complete'
    db.session.commit()

    return redirect(url_for('complete'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    

if __name__ == '__main__':
    app.run(debug=True)

