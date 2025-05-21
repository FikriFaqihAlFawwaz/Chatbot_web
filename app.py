import os
import mysql.connector
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import fitz  # PyMuPDF (for PDF text extraction)

# Importing your models
from models import llm, vector_store  # Import llm (Groq model) and vector_store from models
from database import save_chat, get_chat_history  # Your Firestore functions
from api.endpoints.rag import upload_files  # Assuming the upload_files function is defined in rag.py

print(os.urandom(24))

# Configure Gemini model (Model 2)
genai.configure(api_key="AIzaSyCcWXytihpqgyyrEVIzbdboJhqc209GFyQ")
gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # Update the model ID here

# Initialize conversation history
conversation_history = []

# MySQL database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # your MySQL username
        password="",  # your MySQL password
        database="chatbot"  # your MySQL database name
    )

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Define your 404 error handler to redirect to the index page
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))

# General Chat Route
@app.route('/chat/general/', methods=['POST'])
def general_chat():
    try:
        query = request.json.get('query')
        model_name = request.json.get('model_name')

        # Assuming 'llm' is your model for processing the query
        response = llm.chat(query, model=model_name)  # Implement this function in your models

        return jsonify({"response": response, "model": model_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Coder Chat Route
@app.route('/coder/coder/', methods=['POST'])
def coder_chat():
    try:
        query = request.json.get('query')
        model_name = request.json.get('model_name')

        # Implement this function in your models to handle coding queries
        response = llm.code_chat(query, model=model_name)

        return jsonify({"response": response, "model": model_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# RAG Upload Route
@app.route('/rag/upload/', methods=['POST'])
def rag_upload():
    try:
        files = request.files.getlist('files')
        skip_duplicates = request.form.get('skip_duplicates', 'false') == 'true'

        # Implement the function for processing files and uploading to the database
        results = upload_files(files, skip_duplicates)  # Implement the function in rag.py

        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PDF Upload Route (Chat PDF)
@app.route('/pdf/upload', methods=['POST'])
def chat_pdf():
    try:
        # Get the uploaded PDF file
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            # Save the PDF to a temporary file
            temp_path = os.path.join("uploads", file.filename)
            file.save(temp_path)

            # Extract text from the PDF
            doc = fitz.open(temp_path)
            pdf_text = ""
            for page in doc:
                pdf_text += page.get_text()

            # You can process the extracted text as needed
            return jsonify({"status": "success", "extracted_text": pdf_text})
        else:
            return jsonify({"status": "error", "message": "Invalid file format. Only PDF files are allowed."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Chat PDF page route
@app.route('/chat-pdf', methods=['GET', 'POST'])
def chat_pdf_page():
    if request.method == 'POST':
        try:
            # Process the uploaded PDF
            file = request.files['file']
            if file and file.filename.endswith('.pdf'):
                # Save the PDF to a temporary file
                temp_path = os.path.join("uploads", file.filename)
                file.save(temp_path)

                # Extract text from the PDF
                doc = fitz.open(temp_path)
                pdf_text = ""
                for page in doc:
                    pdf_text += page.get_text()

                # Return the extracted text for chatbot interaction
                return render_template('chat_pdf.html', extracted_text=pdf_text)
            else:
                flash('Only PDF files are allowed!', 'danger')
                return redirect(url_for('chat_pdf_page'))
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
            return redirect(url_for('chat_pdf_page'))

    return render_template('chat_pdf.html', extracted_text=None)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            user_prompt = request.form.get('prompt', '').strip()
            selected_model = request.form.get('model', 'model1')  # Get the selected model

            if not user_prompt:
                return jsonify({'response': "Input cannot be empty."})

            # Add user prompt to conversation history
            conversation_history.append({'role': 'User', 'content': user_prompt})

            # Format history for context
            formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])

            # Select the appropriate model based on user selection
            if selected_model == 'model2':
                # Use Gemini model for Model 2 with the correct method
                response = gemini_model.generate_content(contents=user_prompt)
                bot_reply = response.text if response else "Sorry, but Gemini didn't want to answer that!"
            else:
                # Use Groq model (llm) for Model 1
                bot_reply = llm.predict(user_prompt)

            # Add AI response to history
            conversation_history.append({'role': 'Bot Assistant', 'content': bot_reply})
            
            save_chat(user_prompt, bot_reply)

            return jsonify({'response': bot_reply})

        except Exception as e:
            return jsonify({'response': f"An error occurred: {e}"})

    return render_template('index.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists!', 'danger')
        else:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            conn.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))

        conn.close()

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):  # Check if password is correct
            session['user_id'] = user[0]  # Store user ID in session
            session['email'] = user[1]  # Store email in session
            session['name'] = user[4]  # Store user's name
            session['avatar'] = "https://placehold.co/40x40"  # Set a placeholder avatar
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

        conn.close()

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
