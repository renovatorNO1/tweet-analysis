from flask import Flask, render_template, request, redirect, session
import mysql.connector
from sentiments import second
import os
import traceback
import sys
import requests



app = Flask(__name__)

# initializing the user cookie
app.secret_key = os.urandom(24)

# blueprint to call the second python file in the project.
app.register_blueprint(second)

# establishing a connection with mysql database made in xampp
try:
	conn = mysql.connector.connect(
		host="localhost", user="root", password="")
	
	cursor = conn.cursor()
	cursor.execute("SHOW DATABASES")
	db_names = [x[0] for x in cursor]
	users_db = 'users'
	if users_db not in db_names:
		cursor.execute("CREATE DATABASE users")
		cursor.execute("USE users")
		users_tbl_desc =  (
			"CREATE TABLE `users` ("
			"  `name` varchar(255) ,"
			"  `email` varchar(255) ,"
			"  `password` varchar(255)"
			") ENGINE=InnoDB")
		
		cursor.execute(users_tbl_desc)
	else:
		cursor.execute("USE users")
except Exception as e:
	print(traceback.format_exc())
	print(sys.exc_info()[2] )
	print("An exception occurred")

# call the login template when the url is http://localhost:5000/
@app.route('/')
def login():
	return render_template('login.html')

# call the register template when the url is http://localhost:5000/register
@app.route('/register')
def register():
	return render_template('register.html')


@app.route('/home')
def home():
	if 'user_id' in session:
		return render_template('home.html')
	else:
		return redirect('/')


@app.route('/login_validation', methods=['POST'])
def login_validation():
	email = request.form.get('email')
	password = request.form.get('password')

	cursor.execute(
		"""SELECT * from `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""".format(email, password))
	users = cursor.fetchall()
	# check if a user has already logged in
	if len(users) > 0:
		session['user_id'] = users[0][0]
		return redirect('/home')
	else:
		return redirect('/login')


@app.route('/add_user', methods=['POST'])
def add_user():

# get user login data and pass the data to database
	name = request.form.get('uname')
	email = request.form.get('uemail')
	password = request.form.get('upassword')
	cursor.execute("""INSERT INTO `users` (`name`,`email`,`password`) VALUES ('{}','{}','{}')""".format(
		name, email, password))
	conn.commit()
	cursor.execute(
		"""SELECT * from `users` WHERE `email` LIKE '{}'""".format(email))
	myuser = cursor.fetchall()
	session['user_id'] = myuser[0][0]
	return redirect('/home')


@app.route('/logout')
def logout():
# close the session
	session.pop('user_id')
	return redirect('/')


from rq import Queue
from redis import Redis
from redis_jobs import count_words_at_url
import time
import json

# Tell RQ what Redis connection to use
redis_conn = Redis()
q = Queue(connection=redis_conn)  # no args implies the default queue


@app.route('/run_job', methods=['GET' ,'POST'])
def run_job():
	# Delay execution of count_words_at_url('http://nvie.com')
	job = q.enqueue(count_words_at_url, 'http://nvie.com')
	print(job.return_value())   # => None  # Changed to job.return_value() in RQ >= 1.12.0

	# Now, wait a while, until the worker is finished
	time.sleep(2)
	print(job.return_value())   # => 889  # Changed to job.return_value() in RQ >= 1.12.0

	return json.dumps(job.return_value())

if __name__ == "__main__":
	app.run(debug=True)
