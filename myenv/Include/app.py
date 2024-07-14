from flask import Flask, render_template, request, jsonify, send_from_directory
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from twilio.rest import Client

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Set the upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Twilio credentials
TWILIO_ACCOUNT_SID = 'SID'
TWILIO_AUTH_TOKEN = 'Token'
TWILIO_PHONE_NUMBER = '#'
USER_PHONE_NUMBER = '#'

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_video', methods=['POST'])
def add_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video part in the request"}), 400

    file = request.files['video']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Store video metadata in Firestore
        timestamp = datetime.now().isoformat()
        doc_ref = db.collection('VideoCollection').document()
        doc_ref.set({
            'filename': filename,
            'timestamp': timestamp
        })

        # Send SMS notification
        message = client.messages.create(
            body=f"Motion detected! Video ID: {doc_ref.id}, Time: {timestamp}",
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER
        )

        return jsonify({
            "document_id": doc_ref.id,
            "timestamp": timestamp
        })

@app.route('/videos')
def videos():
    # Fetch video metadata from Firestore
    videos = []
    docs = db.collection('VideoCollection').stream()
    for doc in docs:
        videos.append(doc.to_dict())

    return render_template('videos.html', videos=videos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
