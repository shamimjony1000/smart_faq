from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import google.generativeai as genai
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import hashlib
import secrets
import re

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))

# Database setup
def get_db_connection():
    conn = sqlite3.connect('arogga_faq.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create conversations table with user_id
    conn.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        is_user BOOLEAN NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper functions for authentication
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    return stored_password == hash_password(provided_password)

def is_valid_email(email):
    """Check if email is valid"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Check if username is valid (alphanumeric and underscore only)"""
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

# FAQ data
faq_data = """
Arogga Cash
What is arogga cash?
This is a virtual wallet to store arogga Cash in your account.

How do I check my arogga cash balance?
You can check your arogga cash in Account screen.

When will the arogga money expire?
Any arogga Cash deposited in your arogga wallet through returns will never expire. At times, our marketing team may deposit promotional cash which will have an expiry that is communicated to you via an SMS.

Can I add money to my arogga cash?
No, you are unable to transfer or add money to your arogga cash.

How can I redeem my arogga cash?
If you have any money in your arogga cash, it will be automatically deducted from your next order amount and you will only have to pay for the balance amount (if any).

Can I transfer money from my arogga cash to the bank account?
No, you are unable to transfer money from your arogga cash to the bank account.

How much arogga money can I redeem in an order?
There is no limit for redemption of arogga cash

Payment Options
What payment methods does Arogga accept?
Arogga offers both Cash on Delivery (COD) and online payment options. Online payment methods include bKash, Nagad, and credit/debit cards. Additionally, Arogga offers an "Arogga Cash" virtual wallet where you can accumulate cashback that will be automatically deducted from future orders.

What online payment methods are available?
Arogga accepts several online payment methods including:
1. bKash: A popular mobile payment platform in Bangladesh.
2. Nagad: Another mobile payment platform widely used in Bangladesh.
3. Credit/Debit Cards: Arogga accepts major credit and debit cards.
4. Arogga Cash: A virtual wallet where you can accumulate cashback. This cashback is automatically deducted from your next order.

Can I pay cash when my order is delivered?
Yes, Arogga offers Cash on Delivery (COD) option where customers can pay for their order in cash when it's delivered.

How does Arogga Cash work with payments?
Customers cannot add money to their Arogga Cash, transfer it to a bank account, or use it for other orders. If a customer has Arogga Cash, it will be automatically deducted from the order amount during checkout. For orders where the customer chooses "cash on delivery", they can only withdraw the amount back via bKash.

Promotions
How do I apply a coupon code on my order?
You can apply a coupon on the cart screen while placing an order. If you are getting a message that the coupon code has failed to apply, it may be because you are not eligible for the offer.

Does arogga offers return of the medicine?
Yes, Arogga does accept returns of the medicine from customer. We have 7 days return policy for eligible items. Please check our return section for more details.

Return
How does Arogga's return policy work?
Arogga offers a flexible return policy for items ordered with us. Under this policy, unopened and unused items must be returned within 7 days from the date of delivery. The return window will be listed in the returns section of the order, once delivered. Items are not eligible for return under the following circumstances: - If items have been opened, partially used or disfigured. Please check the package carefully at the time of delivery before opening and using. - If the item's packaging/box or seal has been tampered with. Do not accept the delivery if the package appears to be tampered with. - If it is mentioned on the product details page that the item is non-returnable. - If the return window for items in an order has expired. No items can be returned after 7 days from the the delivery date. - If any accessories supplied with the items are missing. - If the item does not have the original serial number/UPC number/barcode affixed, which was present at the time of delivery. - If there is any damage/defect which is not covered under the manufacturer's warranty. - If the item is damaged due to visible misuse. - Any refrigerated items like insulin or products that are heat sensitive are non-returnable. - Items related to baby care, food & nutrition, healthcare devices and sexual wellness such as but not limited to diapers, health drinks, health supplements, glucometers, glucometer strips/lancets, health monitors, condoms, pregnancy/fertility kits, etc.

Do you sell medicine strips in full or it can be single units too?
We sell in single units to give customers flexibility in selecting specific amounts of medicine required. We provide single units of medicine as our pharmacist can cut strips.

I have broken the seal, can I return it?
No, you can not return any items with a broken seal.

Can I return medicine that is partially consumed?
No, you cannot return partially consumed items. Only unopened items that have not been used can be returned.

Can I ask for a return if the strip is cut?
We provide customers with the option of purchasing medicines as single units. Even if ordering a single tablet of paracetamol, we can deliver that. It is common to have medicines in your order with some strips that are cut. If you want to get a full strip in your order, please order a full strip amount and you will get it accordingly. If you do not order a full strip, you will get cut pieces. If you have ordered 4 single units which are cut pieces and want to return, all 4 pieces must be returned. We do not allow partial return of 1 or 2 pieces.
"""

# Function to get response from Gemini
def get_gemini_response(question):
    # Configure the model
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    prompt = f"""
    You are a helpful customer service assistant for Arogga, a medicine delivery service.
    Answer the following question based on the FAQ information provided below.
    If the question is not directly addressed in the FAQ, use the information to provide the most relevant answer.
    If the question is completely unrelated to the FAQ topics, politely inform that you can only answer questions related to Arogga's services.
    
    FAQ INFORMATION:
    {faq_data}
    
    USER QUESTION: {question}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required')
            return render_template('signup.html')
        
        if not is_valid_username(username):
            flash('Username must contain only letters, numbers, and underscores')
            return render_template('signup.html')
        
        if not is_valid_email(email):
            flash('Invalid email address')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return render_template('signup.html')
        
        # Check if username or email already exists
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                                    (username, email)).fetchone()
        
        if existing_user:
            conn.close()
            flash('Username or email already exists')
            return render_template('signup.html')
        
        # Create new user
        password_hash = hash_password(password)
        conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, password_hash))
        conn.commit()
        
        # Get the user ID for the session
        user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('An error occurred during registration')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Main routes
@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    # Ensure username is available in the template
    username = session.get('username', 'User')
    return render_template('index.html', username=username)

@app.route('/conversations', methods=['GET'])
def get_conversations():
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    conversations = conn.execute('SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC', 
                               (user_id,)).fetchall()
    conn.close()
    
    result = []
    for conversation in conversations:
        result.append({
            'id': conversation['id'],
            'title': conversation['title'],
            'created_at': conversation['created_at']
        })
    
    return jsonify(result)

@app.route('/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    conversation = conn.execute('SELECT * FROM conversations WHERE id = ? AND user_id = ?', 
                              (conversation_id, user_id)).fetchone()
    
    if not conversation:
        conn.close()
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = conn.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at', 
                          (conversation_id,)).fetchall()
    conn.close()
    
    result = {
        'id': conversation['id'],
        'title': conversation['title'],
        'created_at': conversation['created_at'],
        'messages': []
    }
    
    for message in messages:
        result['messages'].append({
            'id': message['id'],
            'is_user': bool(message['is_user']),
            'content': message['content'],
            'created_at': message['created_at']
        })
    
    return jsonify(result)

@app.route('/conversation', methods=['POST'])
def create_conversation():
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.json
    title = data.get('title', 'New Conversation')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO conversations (user_id, title) VALUES (?, ?)', (user_id, title))
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': conversation_id, 'title': title})

@app.route('/ask', methods=['POST'])
def ask():
    if request.method == 'POST':
        if not is_logged_in():
            return jsonify({'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        
        # Check if request is JSON
        try:
            if request.is_json:
                data = request.get_json()
                question = data.get('question')
                conversation_id = data.get('conversation_id')
                print(f"Received JSON data: {data}")
            else:
                # Fallback for form data
                question = request.form.get('question')
                conversation_id = request.form.get('conversation_id')
                print(f"Received form data: question={question}, conversation_id={conversation_id}")
            
            if not question:
                return jsonify({'error': 'No question provided'}), 400
                
            # Get answer from Gemini
            answer = get_gemini_response(question)
            
            # Save to database if conversation_id is provided
            if conversation_id:
                try:
                    conversation_id = int(conversation_id)
                    conn = get_db_connection()
                    
                    # Check if conversation exists and belongs to the user
                    conversation = conn.execute('SELECT * FROM conversations WHERE id = ? AND user_id = ?', 
                                             (conversation_id, user_id)).fetchone()
                    
                    if not conversation:
                        # Create new conversation with first question as title
                        cursor = conn.cursor()
                        title = question[:50] + '...' if len(question) > 50 else question
                        cursor.execute('INSERT INTO conversations (user_id, title) VALUES (?, ?)', 
                                     (user_id, title))
                        conversation_id = cursor.lastrowid
                    
                    # Save user question
                    conn.execute('INSERT INTO messages (conversation_id, is_user, content) VALUES (?, ?, ?)', 
                               (conversation_id, True, question))
                    
                    # Save assistant answer
                    conn.execute('INSERT INTO messages (conversation_id, is_user, content) VALUES (?, ?, ?)', 
                               (conversation_id, False, answer))
                    
                    conn.commit()
                    conn.close()
                    
                    return jsonify({'answer': answer, 'conversation_id': conversation_id})
                except Exception as e:
                    print(f"Database error: {str(e)}")
                    return jsonify({'answer': answer, 'error': str(e)})
            
            return jsonify({'answer': answer})
        except Exception as e:
            print(f"Error in /ask route: {str(e)}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
