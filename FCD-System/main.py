# render_template--> To render any html file, template
from flask import Flask, render_template, Response, session, request, redirect, url_for, jsonify

# used for database connections
import mysql.connector

# used for password encryption
from passlib.hash import sha256_crypt

# FlaskForm--> it is required to upload/receive input from the user,
# like it allows the user to upload video file to our object detection model.
from flask_wtf import FlaskForm

from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename

# wtforms.validators used to validate or restrict the user to upload video file with the correct format (.mp4, .avi),
# not any image, pdf or etc.
from wtforms.validators import InputRequired
import os

# cv2 Required running the YOLOv8 model
import cv2


# detection_Function is the python file that contains the code for our object detection model
# Video Detection is the Function that performs Object Detection on Input Video
from detection_Function import video_detection

# Importing the uuid module for generating unique tokens
import uuid

import pymysql

# for mail
import random
import string
from flask_mail import Message, Mail

# initializing flask, it is a requirement of flask
app = Flask(__name__)


# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'fcds.fyp@gmail.com'
app.config['MAIL_PASSWORD'] = 'zcpsvxwlgxwbnufh'
app.config['MAIL_DEFAULT_SENDER'] = 'fcds.fyp@gmail.com'
mail = Mail(app)


# a secret key on each login user server
app.secret_key = os.urandom(24)

# creating secret key
# app.config['SECRET_KEY'] = 'awaisjameel'

# when user upload any input video file, that input file will first save in the =>static->files folder,
# then analyzed by the model.
app.config['UPLOAD_FOLDER'] = 'static/files'







# -----------------------------------
# starting login, registration code
# -----------------------------------






# establishing connection with the database
conn = mysql.connector.connect(host="localhost", user="root", password='', database="change_mysql")
# by using cursor variable we can communicate with the database
cursor = conn.cursor()


# route for the login page
@app.route('/')
def login():
    # if session is in cookies, then go home page, otherwise redirect to login page
    if 'user_id' in session:
        return redirect('/home')
    else:
        return render_template('login.html')


# route for the registration page
@app.route('/register')
def register():
    # if session is in cookies, then go home page, otherwise redirect to register page
    if 'user_id' in session:
        return render_template('register.html')
    else:
        return redirect('/admin')



# route for login validation
@app.route('/login_validation', methods=['POST'])
def login_validation():
    error = None
    name = request.form.get('name')
    password = request.form.get('password')

    cursor.execute("""SELECT `user_id`, `name`, `password` FROM `users` WHERE `name` LIKE '{}'""".format(name))
    # fetching data from the database in users variable
    user = cursor.fetchone()

    # if users and password match, then set user_id in session and redirect to home page,
    # otherwise redirect to login or root (/) page
    if user and sha256_crypt.verify(password, user[2]):
        session['user_id'] = user[0]

        return redirect('/home')
    else:
        error = "Invalid Username or Password"
        return render_template('login.html', error=error)




# route for registration validation
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('uname')
    email = request.form.get('uemail')
    password = request.form.get('upassword')
    enc_pass = sha256_crypt.encrypt(password)

    # Check if the provided username already exists in the database
    cursor.execute("""SELECT * FROM `users` WHERE `name` = '{}'""".format(name))
    existing_name = cursor.fetchone()

    if existing_name:
        # Display an error message indicating that the username is already taken
        error = "Username already exists."
        return render_template('register.html', error=error)

    # If no errors, proceed with user registration
    token = str(uuid.uuid4().hex)  # Generate a unique token
    cursor.execute("""INSERT INTO `users` (`name`, `email`, `password`, `status`, `token`) VALUES
                    ('{}', '{}', '{}', 0, '{}')""".format(name, email, enc_pass, token))
    # committing that all data must insert in the database
    conn.commit()

    # Send email to user with a verification link
    msg = Message("Account Verification", sender="fcds.fyp@gmail.com", recipients=[email])
    verification_link = f"http://127.0.0.1:5000/verify/{token}"  # Update the domain and endpoint
    msg.body = f"Please click the following link to verify your account: {verification_link}"
    mail.send(msg)  # Assuming you have configured Flask-Mail as "mail"

    error = "Registration successful. Email sent to user mail for Account Verification."
    return render_template('register.html', error=error)


# Endpoint for email verification on registration.
@app.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    cursor.execute("""SELECT `email` FROM `users` WHERE `token` = '{}'""".format(token))
    user_email = cursor.fetchone()

    if user_email:
        # Update the user's status to verified (1) and remove the token
        cursor.execute("""UPDATE `users` SET `status` = 1, `token` = NULL WHERE `email` = '{}'""".format(user_email[0]))
        conn.commit()
        session['user_id'] = user_email[0][0]  # Set the user_id in session
        return redirect('/home')
    else:
        error = "Invalid verification."
        return render_template('register.html', error=error)




# Route for the password reset page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'user_id' in session:

        if request.method == 'POST':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            # Fetch user data from the session or database
            user_id = session.get('user_id')
            if user_id:
                cursor.execute(""" SELECT * FROM `users` WHERE `user_id` LIKE '{}' """.format(user_id))
                user = cursor.fetchone()

                # Verify old password
                if sha256_crypt.verify(old_password, user[3]):

                    # Verify and match new password and confirmation
                    if new_password == confirm_new_password:
                        enc_new_pass = sha256_crypt.encrypt(new_password)

                        # Update user's password in the database
                        cursor.execute(""" UPDATE `users` SET `password` = %s WHERE `user_id` = %s""",
                                       (enc_new_pass, user_id))
                        conn.commit()

                        # Clear the session and redirect to login page
                        session.clear()
                        # Redirect to the login page
                        return redirect('/')

                    else:
                        error = "Password Not Matched."
                else:
                    error = "Incorrect old password."
                return render_template('reset_password.html', error=error)

            # Redirect to login or other appropriate action if session not available
            return redirect('/')

        # Render the password reset page for GET request
        return render_template('reset_password.html', error=None)

    else:
        return redirect('/')



# Route for changing email
@app.route('/change_email', methods=['GET', 'POST'])
def change_email():
    if 'user_id' in session:

        if request.method == 'POST':
            new_email = request.form.get('new_email')

            # Fetch user data from the session or database
            user_id = session.get('user_id')
            if user_id:
                cursor.execute(""" SELECT * FROM `users` WHERE `user_id` LIKE '{}' """.format(user_id))
                user = cursor.fetchone()

                # Update user's email in the database
                cursor.execute(""" UPDATE `users` SET `email` = %s WHERE `user_id` = %s""",
                               (new_email, user_id))
                conn.commit()

                # Clear the session and redirect to login page
                session.clear()

                # Send email to new email with a notification
                msg = Message("Email Updated", sender="fcds.fyp@gmail.com", recipients=[new_email])
                msg.body = "Your email has been successfully updated."
                mail.send(msg)  # Assuming you have configured Flask-Mail as "mail"

                # Redirect to the login page
                return redirect('/')

            # Redirect to login or other appropriate action if session not available
            return redirect('/')

        # Render the email change page for GET request
        return render_template('change_email.html', error=None)

    else:
        return redirect('/')




# route for logout
@app.route('/logout')
def logout():
    # destroying session and redirecting to login or root (/) page
    session.clear()
    return redirect('/')



# generating random password here, and using function in forget password route
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


# route for the forget password
@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    # if session is in cookies, then go home page, otherwise redirect to register page
    if 'user_id' in session:
        return redirect('/home')

    if request.method == 'POST':
        name = request.form.get('uname')
        cursor.execute(""" SELECT `email` FROM `users` WHERE `name` LIKE '{}' """.format(name))
        email_result = cursor.fetchone()

        if email_result:
            email = email_result[0]
            new_password = generate_random_password()  # Generate a random password
            enc_new_pass = sha256_crypt.encrypt(new_password)  # Encrypt the new password

            # Update the user's password in the database
            cursor.execute("UPDATE `users` SET `password` = %s WHERE `email` = %s", (enc_new_pass, email))
            conn.commit()

            # Send the new password to the user's email
            msg = Message("FCD-System Password Reset", sender="fcds.fyp@gmail.com", recipients=[email])
            msg.body = f"Your New Login Password of FCD-System is=> {new_password}"
            mail.send(msg)  # Assuming you have configured Flask-Mail as "mail"

            error = "New Password Already Sent to Your Email. Please Check your Mail Inbox or Spam Folder."
        else:
            error = "Incorrect Username."
        return render_template('forget_password.html', error=error)

    return render_template('forget_password.html', error=None)








# ---------------------------------
# starting admin panel code
# ---------------------------------







@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():

    users = []  # Initialize the users variable as an empty list
    search_term = None
    show_register_button = False  # Default value, assuming button should not be shown

    if 'user_id' in session:


        if request.method == 'POST':
            form_action = request.form.get('form_action')
            search_term = request.form.get('searchUser')
            reset_table = request.form.get('resetTable')

            if form_action == 'reset':
                # Fetch all user data from the database
                cursor.execute("""SELECT `user_id`, `name`, `email` FROM `users`""")
                users = cursor.fetchall()
                search_term = ""
            elif form_action == 'search' and search_term:
                # Fetch user data based on search term
                cursor.execute("""SELECT `user_id`, `name`, `email` FROM `users`
                                          WHERE `user_id` = %s OR `name` = %s OR `email` = %s""",
                               (search_term, search_term, search_term))
                users = cursor.fetchall()
            else:
                # Fetch all user data from the database
                cursor.execute("""SELECT `user_id`, `name`, `email` FROM `users`""")
                users = cursor.fetchall()

            if request.method == 'POST':
                delete_user_id = request.form.get('deleteUserId')
                if delete_user_id:
                    cursor.execute("""DELETE FROM `users` WHERE `user_id` = %s""", (delete_user_id,))
                    conn.commit()

        # Check if the current admin's user_id is 1
        user_id = session.get('user_id')
        if user_id == 1:
            show_register_button = True

        return render_template('admin_panel.html', users=users, search_term=search_term,
                               show_register_button=show_register_button)
    else:
        return redirect('/admin')




@app.route('/admin_table', methods=['GET', 'POST'])
def admin_table():
    users = []  # Initialize the users variable as an empty list
    search_term = None


    # Check if there are existing admin users in the database
    cursor.execute("""SELECT COUNT(*) FROM `admins`""")
    num_admins = cursor.fetchone()[0]

    if num_admins > 0:
        # If there are existing admins, check if the current admin's user_id is 1
        user_id = session.get('user_id')
        if user_id is None or user_id != 1:
            # Redirect other users to home
            return redirect('/admin')

    if request.method == 'POST':
        form_action = request.form.get('form_action')
        search_term = request.form.get('searchUser')
        reset_table = request.form.get('resetTable')

        if form_action == 'reset':
            # Fetch all user data from the database
            cursor.execute("""SELECT `user_id`, `name`, `email` FROM `admins`""")
            users = cursor.fetchall()
            search_term = ""
        elif form_action == 'search' and search_term:
            # Fetch user data based on search term
            cursor.execute("""SELECT `user_id`, `name`, `email` FROM `admins`
                                      WHERE `user_id` = %s OR `name` = %s OR `email` = %s""",
                           (search_term, search_term, search_term))
            users = cursor.fetchall()
        else:
            # Fetch all user data from the database
            cursor.execute("""SELECT `user_id`, `name`, `email` FROM `admins`""")
            users = cursor.fetchall()

        if request.method == 'POST':
            delete_user_id = request.form.get('deleteUserId')
            if delete_user_id and delete_user_id != "1":  # Prevent deleting for user_id 1
                cursor.execute("""DELETE FROM `admins` WHERE `user_id` = %s""", (delete_user_id,))
                conn.commit()

    return render_template('admins_table.html', users=users, search_term=search_term)




# route for admin login validation
@app.route('/admin', methods=['POST', 'GET'])
def admin_login_validation():
    error = None
    show_registration_link = False  # Initialize the flag to show the registration link

    if 'user_id' in session:
        return redirect('/admin_panel')

    cursor.execute("""SELECT COUNT(*) FROM `admins`""")
    num_admins = cursor.fetchone()[0]

    if num_admins == 0:
        show_registration_link = True  # Set the flag to show the registration link

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        cursor.execute("""SELECT `user_id`, `name`, `password` FROM `admins` WHERE `name` LIKE '{}'""".format(name))
        # fetching data from the database in users variable
        user = cursor.fetchone()

        # if users and password match, then set user_id in session and redirect to home page,
        # otherwise redirect to login or root (/) page
        if user and sha256_crypt.verify(password, user[2]):
            session['user_id'] = user[0]

            return redirect('/admin_panel')
        else:
            error = "Invalid Username or Password"
    return render_template('admin_login.html', error=error, show_registration_link=show_registration_link)



# route for admin registration validation
@app.route('/admin_add_user', methods=['POST', 'GET'])
def admin_add_user():
    error = None  # Initialize the error variable


    # Check if there are existing admin users in the database
    cursor.execute("""SELECT COUNT(*) FROM `admins`""")
    num_admins = cursor.fetchone()[0]

    if num_admins > 0:
        # If there are existing admins, check if the current admin's user_id is 1
        user_id = session.get('user_id')
        if user_id is None or user_id != 1:
            # Redirect other users to home
            return redirect('/admin')


    if request.method == 'POST':
        name = request.form.get('uname')
        email = request.form.get('uemail')
        password = request.form.get('upassword')
        enc_pass = sha256_crypt.encrypt(password)

        # Check if there are existing admin users in the database
        cursor.execute("""SELECT COUNT(*) FROM `admins`""")
        num_admins = cursor.fetchone()[0]

        if num_admins == 0:
            # No existing admins, directly register and send to admin_panel
            cursor.execute("""INSERT INTO `admins` (`name`, `email`, `password`, `status`) VALUES
                            ('{}', '{}', '{}', 1)""".format(name, email, enc_pass))
            conn.commit()

            session['user_id'] = email  # Set the user_id in session
            return redirect('/admin_panel')

        else:
            # Check if the provided username already exists in the database
            cursor.execute("""SELECT * FROM `admins` WHERE `name` = '{}'""".format(name))
            existing_name = cursor.fetchone()

            if existing_name:
                # Display an error message indicating that the username is already taken
                error = "Username already exists."
                return render_template('admin_register.html', error=error)

            # If no errors, proceed with user registration
            token = str(uuid.uuid4().hex)  # Generate a unique token
            cursor.execute("""INSERT INTO `admins` (`name`, `email`, `password`, `status`, `token`) VALUES
                            ('{}', '{}', '{}', 0, '{}')""".format(name, email, enc_pass, token))
            # committing that all data must insert in the database
            conn.commit()

            # Send email to user with a verification link
            msg = Message("Admin Account Verification", sender="fcds.fyp@gmail.com", recipients=[email])
            verification_link = f"http://127.0.0.1:5000/admin_verify/{token}"  # Update the domain and endpoint
            msg.body = f"Please click the following link to verify your Admin Account: {verification_link}"
            mail.send(msg)  # Assuming you have configured Flask-Mail as "mail"

            error = "New Admin Registered, Mail Sent to Admin Email for Account Verification."

    return render_template('admin_register.html', error=error)




# Endpoint for email verification on admin registration.
@app.route('/admin_verify/<token>', methods=['GET'])
def admin_verify_email(token):
    cursor.execute("""SELECT `email` FROM `admins` WHERE `token` = '{}'""".format(token))
    user_email = cursor.fetchone()

    if user_email:
        # Update the user's status to verified (1) and remove the token
        cursor.execute("""UPDATE `admins` SET `status` = 1, `token` = NULL WHERE `email` = '{}'""".format(user_email[0]))
        conn.commit()
        session['user_id'] = user_email[0][0]  # Set the user_id in session
        return redirect('/admin_panel')
    else:
        error = "Invalid Admin verification."
        return render_template('admin_register.html', error=error)





# route for the admin forget password
@app.route('/admin_forget_password', methods=['GET', 'POST'])
def admin_forget_password():
    # if session is in cookies, then go home page, otherwise redirect to register page
    if 'user_id' in session:
        return redirect('/admin_panel')

    if request.method == 'POST':
        name = request.form.get('uname')
        cursor.execute(""" SELECT `email` FROM `admins` WHERE `name` LIKE '{}' """.format(name))
        email_result = cursor.fetchone()

        if email_result:
            email = email_result[0]
            new_password = generate_random_password()  # Generate a random password
            enc_new_pass = sha256_crypt.encrypt(new_password)  # Encrypt the new password

            # Update the user's password in the database
            cursor.execute("UPDATE `admins` SET `password` = %s WHERE `email` = %s", (enc_new_pass, email))
            conn.commit()

            # Send the new password to the user's email
            msg = Message("FCD-System Admin Password Reset", sender="fcds.fyp@gmail.com", recipients=[email])
            msg.body = f"Your New Admin Login Password of FCD-System is=> {new_password}"
            mail.send(msg)  # Assuming you have configured Flask-Mail as "mail"

            error = "New Password Already Sent to Your Email. Please Check your Mail Inbox or Spam Folder."
        else:
            error = "Incorrect Username."
        return render_template('admin_forget_password.html', error=error)

    return render_template('admin_forget_password.html', error=None)





# Route for the admin password reset page
@app.route('/admin_reset_password', methods=['GET', 'POST'])
def admin_reset_password():

    if 'user_id' in session:

        if request.method == 'POST':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')

            # Fetch user data from the session or database
            user_id = session.get('user_id')
            if user_id:
                cursor.execute(""" SELECT * FROM `admins` WHERE `user_id` LIKE '{}' """.format(user_id))
                user = cursor.fetchone()

                # Verify old password
                if sha256_crypt.verify(old_password, user[3]):

                    # Verify and match new password and confirmation
                    if new_password == confirm_new_password:
                        enc_new_pass = sha256_crypt.encrypt(new_password)

                        # Update user's password in the database
                        cursor.execute(""" UPDATE `admins` SET `password` = %s WHERE `user_id` = %s""",
                                       (enc_new_pass, user_id))
                        conn.commit()

                        # Clear the session and redirect to login page
                        session.clear()
                        # Redirect to the login page
                        return redirect('/admin')

                    else:
                        error = "Password Not Matched."
                else:
                    error = "Incorrect old password."
                return render_template('admin_reset_password.html', error=error)

            # Redirect to login or other appropriate action if session not available
            return redirect('/admin')

        # Render the password reset page for GET request
        return render_template('admin_reset_password.html', error=None)

    else:
        return redirect('/admin')




# route for logout
@app.route('/admin_logout')
def admin_logout():
    # destroying session and redirecting to login or root (/) page
    session.clear()
    return redirect('/admin')









# ----------------------------------
# starting code for criminal data
# ----------------------------------








# @app.route('/criminal_data', methods=['GET', 'POST'])
# def criminal_data():
#     users = []  # Initialize the users variable as an empty list
#     search_term = None
#
#     if 'user_id' in session:
#
#         if request.method == 'POST':
#             form_action = request.form.get('form_action')
#             search_term = request.form.get('searchUser')
#             reset_table = request.form.get('resetTable')
#
#             if form_action == 'reset':
#                 # Fetch all user data from the database
#                 cursor.execute("""SELECT * FROM `criminal_record`""")
#                 users = cursor.fetchall()
#                 search_term = ""
#             elif form_action == 'search' and search_term:
#                 # Fetch user data based on search term
#                 cursor.execute("""SELECT * FROM `criminal_record`
#                 WHERE `id` = %s OR `name` = %s OR `gender` = %s OR `age` = %s OR `criminal_charges` = %s""",
#                                (search_term, search_term, search_term, search_term, search_term))
#                 users = cursor.fetchall()
#             else:
#                 # Fetch all user data from the database
#                 cursor.execute("""SELECT * FROM `criminal_record`""")
#                 users = cursor.fetchall()
#
#         # return render_template('criminal_data.html', users=users)
#         return render_template('criminal_data.html', users=users, search_term=search_term)
#     else:
#             return redirect('/')






@app.route('/criminal_data', methods=['GET', 'POST'])
def criminal_data():
    users = []  # Initialize the users variable as an empty list
    search_term = None
    reset_table = None  # Initialize reset_table here

    if 'user_id' in session:

        if request.method == 'POST':
            form_action = request.form.get('form_action')
            search_term = request.form.get('searchUser')
            reset_table = request.form.get('resetTable')

            if form_action == 'reset':
                # Fetch all user data from the database
                cursor.execute("""SELECT * FROM `criminal_record`""")
                users = cursor.fetchall()
                search_term = ""
            elif form_action == 'search' and search_term:
                # Fetch user data based on search term
                cursor.execute("""SELECT * FROM `criminal_record` 
                WHERE `id` = %s OR `name` = %s OR `gender` = %s OR `age` = %s OR `criminal_charges` = %s""",
                               (search_term, search_term, search_term, search_term, search_term))
                users = cursor.fetchall()
            else:
                # Fetch all user data from the database
                cursor.execute("""SELECT * FROM `criminal_record`""")
                users = cursor.fetchall()

        # return render_template('criminal_data.html', users=users, search_term=search_term, resetTable=reset_table)
        return render_template('criminal_data.html', users=users, search_term=search_term, resetTable=reset_table)

    else:
        return redirect('/')









# ----------------------------------
# starting code for detection
# ----------------------------------











# Using FlaskForm to get input video file from user, as mentioned before.
class UploadFileForm(FlaskForm):
    # when user upload any input video file, the file path of that input video file will store in the file folder,
    # and We are calling the validators to make sure the user inputs the video in the valid video format (.mp4, .avi),
    # and user can upload the video when prompted to do so.
    file = FileField("File", validators=[InputRequired()])

    # here we have the video submit button,
    # so when user uploads video file it allows user to submit video file, and we can do the detection on it.
    submit = SubmitField("Run")


# Now we will display the output video with detection.

# Generate_frames function takes a path of input video file
# and gives us the output with bounding boxes around detected objects.
def generate_frames(path_x=''):
    # yolo_output variable stores the output for each detection, with bounding boxes around detected objects.
    # here video detection function will give us the bounding boxes around
    # the detected object with label and confidence score as output.
    yolo_output = video_detection(path_x)

    # in this loop, we're doing detection frame by frame
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)

        ''' as we are doing detection frame by frame, means we're dividing video into multiple frames,
         then do detection on each frame one by one.
         so here in loop we are encoding the detection (each video-frame one-by-one)
         Because Flask application requires the encoded image to be converted into bytes.
         We will loop over all individual frames and display them as video.
         We will display the individual frames using Yield keyword.
         When we want the individual frames to be replaced by the subsequent frames (means that frame which 
         coming after individual frame), the Content-Type, or Mini-Type will be used '''

        # here converting encoded-frame into bytes
        frame = buffer.tobytes()

        # here we are displaying each individual frame and
        # replacing detected individual frame with subsequent frame using Content-Type
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# we call generate_frames_web function when we want to access or run detection on the webcam.
def generate_frames_web(path_x):
    # yolo_output variable stores the output for each detection, with bounding boxes around detected objects.
    # here video detection function will give us the bounding boxes around
    # the detected object with label and confidence score as output.
    yolo_output = video_detection(path_x)

    # in this loop, we're doing detection frame by frame
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)

        ''' as we are doing detection frame by frame, means we're dividing video into multiple frames,
         then do detection on each frame one by one.
         so here in loop we are encoding the detection (each video-frame one-by-one)
         Because Flask application requires the encoded image to be converted into bytes.
         We will loop over all individual frames and display them as video.
         We will display the individual frames using Yield keyword.
         When we want the individual frames to be replaced by the subsequent frames (means that frame which 
         coming after individual frame), the Content-Type, or Mini-Type will be used '''

        # here converting encoded-frame into bytes
        frame = buffer.tobytes()

        # here we are displaying each individual frame and
        # replacing detected individual frame with subsequent frame using Content-Type
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# using app.route method, creating URL /home (slash home),
# whenever this URL is called, we will be redirected to the home-page of our web-app.
@app.route('/home')
def home():
    # if user_id session is in cookies, then go home page, otherwise redirect to login or root (/) page.
    # if video_path session is in cookies, session.pop remove it so that when we upload a new video or rerun the webapp,
    # the detection should happen on the new video which we uploaded and not on the previous video.
    if 'user_id' in session:
        if 'video_path' in session:
            session.pop('video_path')
        return render_template('index.html')
    else:
        return redirect('/')


# Rendering the Webcam Page
# Now lets make a Webcam page for the application

# using app.route method, creating URL /webcam (slash webcam);
# whenever this URL is called, we will be redirected to the live webcam feed and do detection on live webcam feed.
@app.route("/webcam", methods=['GET', 'POST'])
# In webcam function, we used session.clear to clear the session,
# which means that, whenever we refresh the web-page after doing detection on live webcam feed,
# so we can do detection again on new live webcam feed as well.
def webcam():
    if 'user_id' in session:
        if 'video_path' in session:
            session.pop('video_path')
        return render_template('webcamPageUi.html')
    else:
        return redirect('/')
    # session.clear()
    # return render_template('webcamPageUi.html')


# using app.route method, creating URL /FrontPage (slash FrontPage);
# whenever this URL is called, we can do detection on the uploaded/input video.
# videoPageUi.html page is basically the FrontPage we're referring to.
@app.route('/FrontPage', methods=['GET', 'POST'])
# In front function, we're basically saving our uploaded video file path (static=>files=>video.mp4)
# in the session storage, to do detection on it.
def front():
    if 'user_id' in session:
        # if 'video_path' not in session:
        #     session.pop('video_path')
        # return render_template('videoPageUi.html')
        form = UploadFileForm()
        if form.validate_on_submit():
            # Our uploaded video file path is saved here in the file variable.
            file = form.file.data
            # Then saving the file
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                   secure_filename(file.filename)))
            # here we're Using session storage to save the video file path.
            session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                 app.config['UPLOAD_FOLDER'],
                                                 secure_filename(file.filename))
        return render_template('videoPageUi.html', form=form)
    else:
        return redirect('/')


# using app.route method, creating URL /video (slash video),
# whenever this URL is called, the detection will happen on the video.
@app.route('/video')
def video():
    # as we have saved the video path in session,
    # so here using session.get we're calling the video path and doing detection on the video.
    return Response(generate_frames(path_x=session.get('video_path', None)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# Using app.route method, creating URL /webapp (slash webapp),
# whenever this URL is called, the detection will happen on the live webcam feed.
# To display the Output Video on Webcam page
@app.route('/webapp')
def webapp():
    return Response(generate_frames_web(path_x=0), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)




