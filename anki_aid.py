import csv
import json
import os 
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask, send_from_directory
from flask import flash
from flask import redirect
from flask import render_template 
from flask import request 
from flask import send_file
from flask import session
from flask_mail import Mail
from flask_mail import Message
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from tempfile import TemporaryDirectory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import default_exceptions
from config import DOWNLOAD_FOLDER, SECRET_KEY
from database import db
from database import dictionaryCN, dictionaryJP
from database import levelCN, levelJP
from database import sentencesCN, sentencesEN, sentencesJP 
from database import transCN_EN, transJP_EN
from functions import *
from io import BytesIO

# App setup
app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)
mail = Mail(app)
app.secret_key = SECRET_KEY
Session(app)

# Index
@app.route("/")
def index():
    return render_template("index.html")

# Sentence finder
@app.route("/card_builder/<string:selected_language>", methods=["GET", "POST"])
def card_builder(selected_language):

    session["language"] = selected_language
    output_fields = ["sentence", "translation", "transcription", "word"] # Options inside select
    
    return render_template("card_builder.html", language=selected_language, output_fields=output_fields)

# Query database and return result (JSON)
@app.route("/get_sentences", methods=["POST", "GET"])
def get_sentences():
    session["settings"] = request.form

    # NOT IMPLEMENTED File validation   
    file = request.files["file"]
    filename = secure_filename(file.filename)
    
    tables = get_tables(session["language"])
    all_matched_sentences = {}
    current_selected_sentences = {}

    usr_vocabulary = get_usr_vocabulary(file, filename) # gets list of user vocabulary
    for word in usr_vocabulary:
        query_results = find_sentences(tables, word, session["settings"]["trans"])
        
        # Store all and first matching sentence
        if query_results:
            all_matched_sentences[word] = [1, (query_results)] # 1 tracks currently selected sentence
            current_selected_sentences[word] = all_matched_sentences[word][1][1] # initially store first matching sentence

    session["all_matched_sentences"] = all_matched_sentences
    session["output_sentences"] = current_selected_sentences

    data = json.dumps(current_selected_sentences)
  
    return data
    

# User requests alternative sentence
@app.route("/reload", methods=["POST"])
def reload ():

    # Get sentences to reload
    words = request.form.getlist("reload")
        
    sentences = session["all_matched_sentences"]
    selected = session["output_sentences"]

    # Store new sentences to be returned
    new = {}
    # Iterate across words with sentence change requested
    for word in words:
        # Current index of selected sentence
        index = sentences[word][0]
        # Store total number of sentences found
        length = len(sentences[word]) - 1
        # Update sentence if another sentence is available
        if index < length:
            # Update selected sentence index
            new_index = index + 1
            sentences[word][0] = new_index
            # Store new selected sentences and update currently selected sentence
            new[word] = sentences[word][new_index]
            selected[word] = new[word]
        else:
            # ADD FEEDBACK TO SHOW NO MORE SENTENCES AVAILABLE / LOOP ROUND TO BEGINNING
            continue
            
        # Future: Add new route for user to rollback the sentences
        
    new = json.dumps(new)
    return new

# Download selected sentences following user chosen structure
@app.route("/download", methods=["POST"])
def download():
    
    
    # Get user selected data structure and store values as a list
    download_struct = request.form.to_dict().values()
    fields = []
    for item in download_struct:
        fields.append(item)

    # Get sentences from session and data output options
    output_sentences = session["output_sentences"]
    
    # Create file
    
    filename = f"{datetime.now().strftime('%Y%m%d%H%M')}.txt"

    with open(f"{DOWNLOAD_FOLDER}/{filename}", "x", encoding="utf-8") as output:
    
# Iterate across selected sentences
        for entry in output_sentences:
            # Iterate accross all form fields and add data to download file (tab separated)
            length = len(download_struct) - 1
            count = 0
            while count < length:
                if fields[count] == "word":
                    output.write(f"{entry}\t")
                else:
                    output.write(f"{output_sentences[entry][fields[count]]}\t")
                count += 1
            # Add final field and escape to new line.
            if fields[count] == "word":
                    output.write(f"{entry}\n")
            else:
                output.write(f"{output_sentences[entry][fields[count]]}\n")
        
    return send_file(f"{DOWNLOAD_FOLDER}/{filename}", as_attachment=True, attachment_filename=filename)

# Renders page template only
@app.route("/about")
def about():
    return render_template("about.html")

# Renders page template and sends email
@app.route("/contact", methods=["GET", "POST"])
def contact():

    # HTML contact form options
    requests = ["Feature", "Data", "Other"]
    
    # Send email (LONG RUNTIME USE @async)
    if request.method == "POST":
        text = request.form.get("message")
        subject = request.form.get("subject")
        msg = Message(subject, recipients=["contact.ankimate@gmail.com"])
        msg.body = text
        mail.send(msg)

        flash("Message sent", "success")
        return redirect("/contact")
    
    if request.method == "GET":
        return render_template("contact.html", requests=requests)
        
    return redirect("/contact")


# Scheduled cleanup of downloads directory
def cleanup():
    files = os.listdir(DOWNLOAD_FOLDER)
    for f in files:
        os.remove(os.path.join(DOWNLOAD_FOLDER, f))

schedule = BackgroundScheduler(daemon=True)
schedule.add_job(cleanup, "interval", minutes=15)
schedule.start()


# Check errors
def errorhandler(e):
    # Email re. exceptions in alert
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    alert = [500]
    if e.code in alert:
        subject = f"{e.code}: {e.name}"
        text = f"Error text:{e.description}.\nRoute: {request.url}"
        msg = Message(subject, recipients=["contact.ankimate@gmail.com"])
        msg.body = text
        mail.send(msg)
    # Display error page
    return render_template("error.html", error=e.code, message=e.name, description=e.description), e.code

class FileError(HTTPException):
    code = 507
    description = 'File error'

app.register_error_handler(FileError, 507)

def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.desciprtion,
    })
    return response

# ATTRIBUTE (CS50)
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)