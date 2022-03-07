from distutils.log import error
from re import search
import secrets
from unittest import result
from flask import Flask, render_template, request, redirect, make_response, flash, session
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
from functools import wraps
import secrets

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('secret_app_key')

app.config["MYSQL_HOST"] = os.environ.get('MYSQL_HOST')
app.config["MYSQL_USER"] = os.environ.get('MYSQL_USER')
app.config["MYSQL_PASSWORD"] = os.environ.get('MYSQL_PASSWORD')
app.config["MYSQL_DB"] = os.environ.get('MYSQL_DB')

load_dotenv('.env')
mysql = MySQL(app)


# checking if user is logged in or not and redirecting to login page if not logged in.

# def login_required(test):
#     @wraps(test)
#     def wrap(*args, **kwargs):
#         user_id = request.cookies.get('session_id')
#         cur = mysql.connection.cursor()
#         cur.execute(
#             "SELECT * FROM tbl_user WHERE session_id = %s", [user_id])
#         current_user = cur.fetchone()[3]
#         cur.close()
#         if user_id and current_user and user_id == current_user:
#             return redirect('/dashboard')
#         else:
#             return render_template('login.html')
#     return wrap


# checking if user is logged in or not.
def is_logged_in():
    # getting the session id from the cookie
    user_id = request.cookies.get('session_id')
    if user_id:
        # getting the session id from the database
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM tbl_user WHERE session_id = %s", [user_id])
        current_user = cur.fetchone()[3]
        cur.close()

        # checking the session id with session id in database.
        if user_id and current_user and user_id == current_user:
            return True
        else:
            return False
    else:
        return False


# sanitize user input. i hope this helps from SQL injection attacks


def clean(string):
    clean_string = ""
    valid_character = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL@MNOPQRSTUVWXYZ1234567890 ,.!?()[]{}<>\\/'
    for char in string:
        if char.isalnum() or char in valid_character:
            clean_string += char
    return clean_string

# generating session id for the user.


def generate_session_id():
    global default_user_id
    default_user_id = secrets.token_hex(16)
    return default_user_id


@app.route("/", methods=["GET", "POST"])
def home():
    # if user is logged in, redirecting to dashboard page else redirecting to login page.
    if request.method == 'GET':
        if is_logged_in() == True:
            return redirect('/dashboard')
        else:
            return render_template("pages/home.html")

    elif request.method == 'POST':
        # getting the user input from the form.
        user_name = request.form["username"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        # checking if the user is registered or not.
        cur.execute(
            'SELECT * FROM tbl_user WHERE user_name = %s AND user_password = %s', (user_name, password,))
        user_account = cur.fetchone()
        if user_account:
            # if user is registered, generating session id and logging in the user.
            id = user_account[0]
            response = make_response(redirect('/dashboard'))
            s_id = generate_session_id()
            response.set_cookie('session_id', s_id)
            cur = mysql.connection.cursor()
            cur.execute(
                'UPDATE tbl_user SET session_id = %s WHERE user_id = %s', (s_id, id))
            mysql.connection.commit()
            cur.close()
            return response
        else:
            return render_template("pages/home.html", info="wrong user_name or password")


@ app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        if is_logged_in() == True:
            user_id = request.cookies.get('session_id')
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT user_id FROM tbl_user WHERE session_id = %s", [user_id])
            current_user_id = cur.fetchone()
            # fetching the data from search form
            search = clean(request.args.get('search') or '')
            # if some data is entered in the search form, searching the data in the database.
            if search:
                cur.execute("SELECT * FROM tbl_student WHERE student_name LIKE %s AND user_id = %s", (
                    "%" + search + "%", current_user_id[0]))
                student_account = cur.fetchall()
                student_account_list = []
                if student_account:
                    for i in student_account:
                        student_dict = {
                            "id": i[0],
                            "name": i[1],
                            "email": i[2],
                            "phone": i[3],
                            "collage": i[4],
                            "degree": i[5],
                            "specialisation": i[6],
                            "gender": i[7],
                            "internship": i[8],
                            "notes": i[9],
                            "location": i[10],
                            "user_id": i[11]
                        }
                        student_account_list.append(student_dict)
                    return render_template("pages/dashboard.html", search=search, student_account_list=student_account_list)
                else:
                    return render_template("pages/dashboard.html", search=search, info="No student found")
            # if no data is entered in the search form, showing all the student details on the dashboard page.
            else:
                cur.execute(
                    'SELECT * FROM tbl_student WHERE user_id = %s', (current_user_id))
                student_account = cur.fetchall()
                student_account_list = []
                if student_account:
                    for i in student_account:
                        student_dict = {
                            "id": i[0],
                            "name": i[1],
                            "email": i[2],
                            "phone": i[3],
                            "collage": i[4],
                            "degree": i[5],
                            "specialisation": i[6],
                            "gender": i[7],
                            "internship": i[8],
                            "notes": i[9],
                            "location": i[10],
                            "user_id": i[11]
                        }
                        student_account_list.append(student_dict)
                    cur.close()
                    return render_template("pages/dashboard.html", student_account_list=student_account_list)
                # if student is not found showing the message.
                else:
                    return render_template("pages/dashboard.html", student_account_list=[])
        # redirecting to login page if user is not logged in.
        else:
            return redirect("/")

    else:
        return redirect("/")


@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "GET":
        user_id = request.cookies.get('session_id')
        if is_logged_in() == True:
            # sending empty form data to the add student page to avoid errors.
            form_student = {
                "name": "",
                "email": "",
                "collage": "",
                "telephone": "",
                "gender": "",
                "location": "",
                "specialisation": "",
                "degree": "",
                "notes": "",
                'internship': "",
            }

            return render_template("pages/add_student.html", form_student=form_student)
        else:
            flash("You are not logged in", "error")
            return redirect("dashboard")
    elif request.method == "POST":
        # getting the user input from the form.
        student_name = request.form["student_name"]
        student_email = request.form["email"]
        student_collage = request.form["collage_name"]
        student_telephone = request.form["telephone"]
        student_gender = request.form["gender"]
        student_location = request.form["location"]
        student_specialisation = request.form["specialisation"]
        student_degree = request.form.get("degree")
        student_notes = request.form["notes"]
        student_internship = request.form["type_of_internship"]
        # storing the data in dictionary for easy access in the template.
        form_student = {
            "name": student_name,
            "email": student_email,
            "collage": student_collage,
            "telephone": student_telephone,
            "gender": student_gender,
            "location": student_location,
            "specialisation": student_specialisation,
            "degree": student_degree,
            "notes": student_notes,
            'internship': student_internship,

        }
        # checking if all the fields are filled and if not showing the error message.
        try:
            if not student_name:
                raise Exception("student_name is required")
            if not student_email:
                raise Exception("please enter a valid email")
            if not student_collage:
                raise Exception("collage_name is required")
            if not student_telephone or len(student_telephone) != 10:
                raise Exception("please enter a valid telephone number")
            else:
                try:
                    student_telephone = int(student_telephone)
                except:
                    raise Exception("please enter a valid telephone number")
            if not student_gender:
                raise Exception("please select gender")
            if not student_location:
                raise Exception("please enter a location")
            if not student_degree:
                raise Exception("please select a degree")
            if not student_notes:
                raise Exception("please enter notes")
            if not student_specialisation:
                raise Exception("please select specialisation")
            if not student_internship:
                raise Exception("please select type of internship")
            else:
                # getting current user id using session id.
                user_id = request.cookies.get('session_id')
                cur = mysql.connection.cursor()
                cur.execute(
                    "SELECT user_id FROM tbl_user WHERE session_id = %s", [user_id])
                current_user_id = cur.fetchone()
                # inserting the data into the database.
                cur.execute(
                    'INSERT INTO tbl_student(student_name, student_email, contact_nos, collage_name, student_degree, specialisation, gender, internship, notes, location, user_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (student_name, student_email, student_telephone, student_collage, student_degree, student_specialisation, student_gender, student_internship, student_notes, student_location, current_user_id))
                mysql.connection.commit()
                cur.close()
                flash("student added", "success")
                return redirect("/dashboard")
        # showing the error message if any error occurs.
        except Exception as error:
            flash(str(error), "error")
            return render_template("pages/add_student.html", form_student=form_student)


@ app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        new_user = {
            "user_name": ""
        }
        return render_template("pages/signup.html", new_user=new_user)
    elif request.method == "POST":
        details = request.form
        user_name = details["user_name"]
        password = details["user_password"]
        c_password = details["confirm_password"]
        # checking if user name is not empty and if user name is empty sending empty form data to the signup page.
        if user_name:
            new_user = {
                "user_name": user_name,
            }
        else:
            new_user = {
                "user_name": "",
            }
        # checking if all the fields are filled and password and confirm password are same.
        try:
            if not user_name:
                raise Exception("please enter a user name")
            if not password:
                raise Exception("Please enter a password")
            elif not c_password:
                raise Exception("Please select subjects ")
            elif password != c_password:
                raise Exception("Passwords do not match enter same password")
            else:
                cur = mysql.connection.cursor()
                cur.execute(
                    'SELECT * FROM tbl_user WHERE user_name = %s', (user_name,))
                user_account = cur.fetchone()
                # raising an error if user name is already registered.
                if user_account:
                    raise Exception("User already exists")
                else:
                    cur.execute(
                        'INSERT INTO tbl_user (user_name, user_password) VALUES (%s, %s)', (user_name, password))
                    mysql.connection.commit()
                    return redirect("/")
        # showing the error message if any error occurs and sending the form data to the signup page.
        except Exception as error:
            return render_template("pages/signup.html", error=error, new_user=new_user)


@ app.route("/update/<id>", methods=["GET", "POST"])
def update(id):
    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT * FROM tbl_student WHERE id = %s', [id])
    student_account = cur.fetchone()
    cur.close()
    # adding the details in dictionary for easy access in the template.
    if student_account:
        student = {
            "id": student_account[0],
            "name": student_account[1],
            "email": student_account[2],
            "phone": student_account[3],
            "collage": student_account[4],
            "degree": student_account[5],
            "specialisation": student_account[6],
            "gender": student_account[7],
            "internship": student_account[8],
            "notes": student_account[9],
            "location": student_account[10],
            "user_id": student_account[11]
        }

    if request.method == "GET":
        # checking if the student account exists or not.
        if student and is_logged_in() == True:
            return render_template("pages/update.html", student=student)
        else:
            return redirect("/dashboard")

    elif request.method == "POST":
        # getting the form data and use clean function for avoiding sql injection.
        student_name = clean(request.form.get("student_name") or "")
        student_email = clean(request.form.get("email") or "")
        student_collage = clean(request.form.get("collage_name") or "")
        student_telephone = clean(request.form.get("telephone") or "")
        student_gender = clean(request.form.get("gender") or "")
        student_location = clean(request.form.get("location") or "")
        student_specialisation = clean(
            request.form.get("specialisation") or "")
        student_degree = clean(request.form.get("degree") or "")
        student_notes = clean(request.form.get("notes") or "")
        student_internship = clean(
            request.form.get("type_of_internship") or "")
        id1 = id

    # sending data to the form to be updated after reloading the page
        form_student = {
            "name": student_name,
            "email": student_email,
            "phone": student_telephone,
            "collage": student_collage,
            "degree": student_degree,
            "specialisation": student_specialisation,
            "gender": student_gender,
            "internship": student_internship,
            "notes": student_notes,
            "location": student_location
        }
        try:
            # checking if form feild is not empty.
            if not student_name:
                raise Exception("student_name is required")
            if not student_email:
                raise Exception("please enter a valid email")
            if not student_collage:
                raise Exception("collage_name is required")
            # checking the length of the telephone number and converting it to int.
            if not student_telephone and len(student_telephone) != 10:
                raise Exception("please enter a valid telephone number")
            else:
                try:
                    student_telephone = int(student_telephone)
                except:
                    raise Exception("please enter a valid telephone number")
            if not student_gender:
                raise Exception("please select gender")
            if not student_location:
                raise Exception("please enter a location")
            if not student_degree:
                raise Exception("please select a degree")
            if not student_notes:
                raise Exception("please enter notes")
            if not student_specialisation:
                raise Exception("please select specialisation")
            if not student_internship:
                raise Exception("please select type of internship")
            else:
                user_id = request.cookies.get('session_id')
                cur = mysql.connection.cursor()
                cur.execute(
                    "SELECT user_id FROM tbl_user WHERE session_id = %s", [user_id])
                current_user_id = cur.fetchone()[0]
                # updating the student account.
                cur.execute(
                    "UPDATE tbl_student SET student_name=%s, student_email=%s, contact_nos=%s, collage_name=%s, student_degree=%s, specialisation=%s, gender=%s, internship=%s, notes=%s, location=%s, user_id=%s WHERE id=%s",
                    (student_name, student_email, student_telephone, student_collage, student_degree, student_specialisation, student_gender, student_internship, student_notes, student_location, int(current_user_id), int(id1)))
                mysql.connection.commit()
                cur.close()
                flash("succesfully edited student info", 'success')
                return redirect("/dashboard")
        except Exception as error:
            flash(str(error), 'error')
            return render_template("pages/update.html", error=error, student=student)
        finally:
            cur.close()


@ app.route("/delete_student/<id>", methods=["GET", "POST"])
def delete_student(id):
    if is_logged_in() == True:
        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM tbl_student WHERE id = %s', [id])
            student_detail = cur.fetchone()
            # checking if the student account exists or not.
            if not student_detail:
                raise Exception("This student is not found")

            else:
                # deleting the student account from the database.
                cur.execute("DELETE FROM tbl_student WHERE id = %s", [id])
                mysql.connection.commit()
                cur.close()
                flash("successfully deleted row")
                return redirect("/dashboard")
        except Exception as error:
            flash(str(error), 'error')
            return redirect("/dashboard")
        finally:
            cur.close()
    else:
        flash("You are not logged in", "error")

        return redirect("/")


@ app.route("/logout")
def logout():
    # deleting the session id from the database.
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            'UPDATE tbl_user SET session_id = %s WHERE session_id = %s', (None, request.cookies.get('session_id')))
        mysql.connection.commit()
    finally:
        cur.close()
    # deleting the session id from the browser cookie.
    response = make_response(redirect('/'))
    response.set_cookie('session_id', "")
    flash("You have been logged out")
    return response

# error handling if the page is not found.


@ app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/404.html"), 400

# error handling if their is an error in the server.


@ app.errorhandler(500)
def internal_server_error(e):
    return render_template("pages/500.html"), 500


if __name__ == '__main__':
    app.run(debug=True)
