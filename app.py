import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai
import speech_recognition as sr
from flask_mail import Mail, Message
from models import db, Reflection

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:CandyCane123@reflectionsdb.cvy88ysg020q.us-east-1.rds.amazonaws.com/reflectionsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# db = SQLAlchemy(app)
db.init_app(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Import the model
from models import db, Reflection



@app.before_request
def create_tables():
    db.create_all()

# Function to interact with OpenAI API
def chat_with_openai(question):
    response = openai.Completion.create(
        engine="text-davinci-004",
        prompt=question,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError:
        return "Could not request results; check your network connection."

# Home Route - To display form and chatbot interaction
@app.route('/')
def index():
    return render_template('index.html')

# Route to add questions
@app.route('/add_question', methods=['POST'])
def add_question():
    # Logic to add user-input questions to the list
    return redirect(url_for('index'))

# Route to start reflection (chat with OpenAI)
@app.route('/start_reflection', methods=['POST'])
def start_reflection():
    questions = request.form.getlist('questions')
    reflections = []
    for question in questions:
        response = chat_with_openai(question)
        reflections.append({"question": question, "response": response})
    
    # Save to DB
    for reflection in reflections:
        new_reflection = Reflection(questions=reflection['question'], response=reflection['response'])
        db.session.add(new_reflection)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    reflections = Reflection.query.filter(Reflection.date.between(start_date, end_date)).all()

    summary = ""
    for reflection in reflections:
        summary += f"Question: {reflection.questions}\nResponse: {reflection.response}\n\n"
    
    return jsonify({"summary": summary})

@app.route('/send_summary', methods=['POST'])
def send_summary():
    summary = request.form['summary']
    recipients = request.form.getlist('recipients')

    msg = Message('Weekly Reflection Summary',
                  sender='your-email@example.com',
                  recipients=recipients)
    msg.body = summary
    mail.send(msg)
    
    return "Summary Sent!"


if __name__ == "__main__":
    app.run(debug=True)
