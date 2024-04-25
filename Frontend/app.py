from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import requests
import json
import os
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AUTH = 'http://localhost:8080'  
PREF_API = 'http://localhost:8081'
Chat_History_API = ''
CHAT_API =''

def is_logged_in():
    return 'email' in session

@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('chatbot'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        response = requests.post(f'{AUTH}/login', json={'email': email, 'password': password})
        if response.status_code == 200:
            session['email'] = email
            return redirect(url_for('chatbot'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        response = requests.post(f'{AUTH}/signup', json={'email': email, 'password': password})
        if response.status_code == 200:
            session['email'] = email
            return redirect(url_for('chatbot'))
        else:
            return render_template('signup.html', error='Signup failed')
    else:
        return render_template('signup.html')


"""
@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        logger.info(f'Verify email request received for email: {email}')
        response = requests.post(f'{AUTH}/verify-email', json={'email': email, 'code': code})
        if response.status_code == 200:
            return redirect(url_for('login'))
        else:
            logger.error(f'Verify email failed for email: {email}')
            return render_template('verify.html', error='Verification failed', email=email)
    else:
        email = request.args.get('email')
        return render_template('verify.html', email=email)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    email = request.form['email']
    logger.info(f'Resend verification email request received for email: {email}')
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'email': email})
    response = requests.post(f'{AUTH}/resend-verification', headers=headers, data=data)

    if response.status_code == 200:
        logger.info(f'Verification email resent for email: {email}')
        return redirect(url_for('some_success_route'))  # Redirect to a success route
    else:
        logger.error(f'Failed to resend verification email for email: {email}')
        return render_template('verify.html', error='Failed to resend verification email', email=email)
    """
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/chatbot')
def chatbot():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        preferences = request.form.getlist('preference')
        response = requests.post(f'{PREF_API}/preference_save', json={'email': session['email'], 'preferences': preferences})
        if response.status_code == 200:
            return redirect(url_for('chatbot'))
        else:
            return render_template('chatbot.html', error='Failed to save preferences')
    else:
        response = requests.get(f'{PREF_API}/preferences', params={'email': session['email']})
        if response.status_code == 200:
            # Check if response JSON is a list or dictionary
            if isinstance(response.json(), list):
                user_preferences = []
            else:
                user_preferences = response.json().get('preferences', [])
            return render_template('chatbot.html', user_preferences=user_preferences)
        else:
            return render_template('chatbot.html', error='Failed to retrieve preferences')

@app.route('/send_message', methods=['POST'])
def send_message():
    if not is_logged_in():
        return jsonify({'message': 'You must be logged in to send messages.'}), 401

    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'message': 'Message cannot be empty.'}), 400

    # Send the user's message and email to the LLM API
    response = requests.post(CHAT_API, json={'email': session['email'], 'message': message})
    if response.status_code == 200:
        bot_response = response.json().get('response')
        return jsonify({'message': bot_response, 'user': 'bot'}), 200
    else:
        return jsonify({'message': 'Failed to get response from LLM.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')