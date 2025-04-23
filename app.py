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
    conn = sqlite3.connect('shamim_faq.db')
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
About Shamim
Who is Shamim Md. Jony?
Shamim Md. Jony is a passionate machine learning engineer and software developer from Chittagong, Bangladesh. With a strong academic background and hands-on experience in AI, he specializes in building scalable, real-world applications using modern ML and LLM technologies.

What is your current position?
I am currently working as a Software Engineer at Prachine Bangla Ecommerce Limited since November 2024.

What are your responsibilities at Prachine Bangla Ecommerce Limited?
My key responsibilities include:
- Managing the main AWS Lightsail server infrastructure.
- Developing and scaling e-commerce solutions to support high traffic and large product catalogs.
- Integrating AI-powered chatbots to enhance customer support and engagement.
- Collaborating on API development and third-party service integrations such as payment gateways, shipping, and more.

How do you handle the server infrastructure for Prachine Bangla Ecommerce Limited?
I am responsible for managing the main AWS Lightsail server, ensuring its smooth operation and scalability to accommodate a large e-commerce platform.

What kind of e-commerce solutions do you develop and scale?
I work on developing solutions that support high traffic, optimize the browsing experience, and scale the system to manage a large product catalog effectively.

What role do AI-powered chatbots play in your work?
I integrate AI-powered chatbots into our platform to improve customer support, automate responses, and enhance engagement with users.

Do you work with third-party services?
Yes, I collaborate on API development and integrate third-party services such as payment gateways and shipping solutions into the e-commerce platform.

What industries or domains has he worked in?
Shamim has worked primarily in the e-commerce industry, with strong contributions to:
- AI-enhanced online shopping experiences
- Chatbot integrations
- Sentiment analysis in the airline industry
- Hate speech detection in Bangla language content

What real-world AI applications has he built?
- Smart FAQ Chatbot: Uses LangChain and LLMs to answer user queries intelligently.
- E-commerce Assistant: AI system to help customers find products faster and improve UX.
- Sentiment Classifier: Applied deep learning to analyze customer sentiments about airlines.
- Hate Speech Detector: Identifies offensive language in Bangla using ML/NLP techniques.

What experience does he have with cloud services?
He is skilled in deploying and managing models and services on cloud platforms, especially:
- AWS Lightsail: Server management for high-traffic eCommerce.
- Google Cloud: Used for ML model hosting and experimentation.

What tools and frameworks is he comfortable with?
- LangChain, Hugging Face, PyTorch, TensorFlow
- Flask, FastAPI (for APIs and ML model serving)
- Laravel & PHP (for backend systems)
- MongoDB, MySQL, SQLite (for data management)

Professional Experience
What is his role at Prachine Bangla Ecommerce Ltd.?
As a Software Engineer, Shamim is:
- Maintaining and scaling AWS-based eCommerce infrastructure
- Creating AI-powered features like chatbots
- Integrating APIs for payment, shipping, etc.
- Leading tech improvements for better performance and UX

What kind of opportunities is he seeking?
He is actively looking for challenging projects or remote roles focused on:
- Large Language Models (LLMs)
- Advanced machine learning applications
- AI innovation in real-world products

Qualifications
What makes Shamim a strong candidate for ML roles?
- Strong academic foundation (CGPA 3.88 in BSc)
- Real-world deployment experience
- Demonstrated success in both backend and AI development
- Certification from DeepLearning.AI, a leader in ML education

What's unique about his AI approach?
Shamim blends practical deployment skills with theoretical understanding. He's not just focused on building models, but also on ensuring they work in production and deliver real business value.

Where can I see his work or contributions?
- GitHub: github.com/shamimjony1000
- LinkedIn: linkedin.com/in/shamim-jony

Location
ADDRESS:
Khulshi-1, Chittagong, Bangladesh

Contact
How can I contact Shamim for professional opportunities?
You can reach out to Shamim through his LinkedIn profile at linkedin.com/in/shamim-jony or via email. He is open to discussing remote work opportunities, consulting projects, and collaborations in the field of machine learning and AI development.

শামীম মো. জনি কে?
শামীম মো. জনি চট্টগ্রাম, বাংলাদেশের একজন উদ্যমী মেশিন লার্নিং প্রকৌশলী এবং সফটওয়্যার ডেভেলপার। কৃত্রিম বুদ্ধিমত্তায় একটি শক্তিশালী একাডেমিক পটভূমি এবং বাস্তব অভিজ্ঞতা নিয়ে, তিনি আধুনিক এমএল এবং এলএলএম প্রযুক্তি ব্যবহার করে স্কেলেবল, বাস্তব-বিশ্বের অ্যাপ্লিকেশন তৈরিতে বিশেষজ্ঞ।

আপনার বর্তমান পদ কি?
আমি বর্তমানে ২০২৪ সালের নভেম্বর মাস থেকে প্রাচীনে বাংলা ই-কমার্স লিমিটেডে সফটওয়্যার প্রকৌশলী হিসেবে কর্মরত আছি।

প্রাচীনে বাংলা ই-কমার্স লিমিটেডে আপনার দায়িত্বগুলো কী কী?
আমার প্রধান দায়িত্বগুলোর মধ্যে রয়েছে:

প্রধান AWS লাইটসেল সার্ভার অবকাঠামো পরিচালনা করা।
উচ্চ ট্র্যাফিক এবং বৃহৎ পণ্য ক্যাটালগ সমর্থন করার জন্য ই-কমার্স সলিউশন তৈরি এবং স্কেল করা।
গ্রাহক সহায়তা এবং সম্পৃক্ততা বাড়াতে এআই-চালিত চ্যাটবট সংহত করা।
API ডেভেলপমেন্ট এবং তৃতীয় পক্ষের পরিষেবা যেমন পেমেন্ট গেটওয়ে, শিপিং এবং আরও অনেক কিছুর সাথে সহযোগিতা করা।
আপনি প্রাচীনে বাংলা ই-কমার্স লিমিটেডের জন্য সার্ভার অবকাঠামো কীভাবে সামলান?
আমি প্রধান AWS লাইটসেল সার্ভার পরিচালনার জন্য দায়ী, যা একটি বৃহৎ ই-কমার্স প্ল্যাটফর্মের মসৃণ পরিচালনা এবং স্কেলেবিলিটি নিশ্চিত করে।

আপনি কী ধরনের ই-কমার্স সলিউশন তৈরি এবং স্কেল করেন?
আমি এমন সলিউশন তৈরিতে কাজ করি যা উচ্চ ট্র্যাফিক সমর্থন করে, ব্রাউজিংয়ের অভিজ্ঞতা অপ্টিমাইজ করে এবং কার্যকরভাবে একটি বৃহৎ পণ্য ক্যাটালগ পরিচালনা করার জন্য সিস্টেমকে স্কেল করে।

আপনার কাজে এআই-চালিত চ্যাটবট কী ভূমিকা পালন করে?
গ্রাহক সহায়তা উন্নত করতে, স্বয়ংক্রিয় প্রতিক্রিয়া জানাতে এবং ব্যবহারকারীদের সাথে সম্পৃক্ততা বাড়াতে আমি আমাদের প্ল্যাটফর্মে এআই-চালিত চ্যাটবট সংহত করি।

আপনি কি তৃতীয় পক্ষের পরিষেবাগুলির সাথে কাজ করেন?
হ্যাঁ, আমি API ডেভেলপমেন্টে সহযোগিতা করি এবং পেমেন্ট গেটওয়ে এবং শিপিং সলিউশনের মতো তৃতীয় পক্ষের পরিষেবাগুলিকে ই-কমার্স প্ল্যাটফর্মে সংহত করি।

তিনি কোন শিল্প বা ডোমেইনগুলিতে কাজ করেছেন?
শামীম প্রাথমিকভাবে ই-কমার্স শিল্পে কাজ করেছেন, যেখানে তার শক্তিশালী অবদান রয়েছে:

এআই-বর্ধিত অনলাইন শপিং অভিজ্ঞতা
চ্যাটবট ইন্টিগ্রেশন
এয়ারলাইন শিল্পে সেন্টিমেন্ট বিশ্লেষণ
বাংলা ভাষার সামগ্রীতে বিদ্বেষপূর্ণ বক্তব্য সনাক্তকরণ
তিনি বাস্তব-বিশ্বে কী কী এআই অ্যাপ্লিকেশন তৈরি করেছেন?

স্মার্ট FAQ চ্যাটবট: ব্যবহারকারীর প্রশ্নের বুদ্ধিদীপ্ত উত্তর দিতে ল্যাংচেইন এবং এলএলএম ব্যবহার করে।
ই-কমার্স সহকারী: গ্রাহকদের দ্রুত পণ্য খুঁজে পেতে এবং UX উন্নত করতে সাহায্য করার জন্য এআই সিস্টেম।
সেন্টিমেন্ট ক্লাসিফায়ার: এয়ারলাইনস সম্পর্কে গ্রাহকের অনুভূতি বিশ্লেষণ করতে ডিপ লার্নিং প্রয়োগ করা হয়েছে।
বিদ্বেষপূর্ণ বক্তব্য সনাক্তকারী: ML/NLP কৌশল ব্যবহার করে বাংলা ভাষায় আপত্তিকর ভাষা চিহ্নিত করে।
ক্লাউড পরিষেবাগুলির সাথে তার কী অভিজ্ঞতা আছে?
তিনি ক্লাউড প্ল্যাটফর্মে, বিশেষ করে মডেল এবং পরিষেবা স্থাপন এবং পরিচালনার ক্ষেত্রে দক্ষ:

AWS লাইটসেল: উচ্চ-ট্র্যাফিক ই-কমার্সের জন্য সার্ভার ব্যবস্থাপনা।
গুগল ক্লাউড: ML মডেল হোস্টিং এবং পরীক্ষণের জন্য ব্যবহৃত।
তিনি কোন সরঞ্জাম এবং ফ্রেমওয়ার্কের সাথে স্বাচ্ছন্দ্যবোধ করেন?

ল্যাংচেইন, হাগিং ফেস, পাইটর্চ, টেনসরফ্লো
ফ্লাস্ক, ফাস্টএপিআই (API এবং ML মডেল পরিবেশনের জন্য)
লারাভেল ও পিএইচপি (ব্যাকেন্ড সিস্টেমের জন্য)
মঙ্গোডিবি, মাইএসকিউএল, এসকিউলাইট (ডেটা ব্যবস্থাপনার জন্য)
পেশাগত অভিজ্ঞতা

প্রাচীনে বাংলা ই-কমার্স লিমিটেডে তার ভূমিকা কী?
সফটওয়্যার প্রকৌশলী হিসেবে, শামীম:

AWS-ভিত্তিক ই-কমার্স অবকাঠামোর রক্ষণাবেক্ষণ ও স্কেলিং করছেন
চ্যাটবটের মতো এআই-চালিত বৈশিষ্ট্য তৈরি করছেন
পেমেন্ট, শিপিং ইত্যাদির জন্য API সংহত করছেন
উন্নত কর্মক্ষমতা এবং UX-এর জন্য প্রযুক্তিগত উন্নতির নেতৃত্ব দিচ্ছেন
তিনি কী ধরনের সুযোগ খুঁজছেন?
তিনি সক্রিয়ভাবে চ্যালেঞ্জিং প্রকল্প বা দূরবর্তী ভূমিকা খুঁজছেন যা মূলত:

বৃহৎ ভাষা মডেল (LLMs)
উন্নত মেশিন লার্নিং অ্যাপ্লিকেশন
বাস্তব-বিশ্বের পণ্যগুলিতে এআই উদ্ভাবনের উপর দৃষ্টি নিবদ্ধ করে।
যোগ্যতা

কী কারণে শামীম এমএল ভূমিকার জন্য একজন শক্তিশালী প্রার্থী?

শক্তিশালী একাডেমিক ভিত্তি (বিএসসি-তে ৩.৮৮ সিজিপিএ)
বাস্তব-বিশ্বে স্থাপনার অভিজ্ঞতা
ব্যাকেন্ড এবং এআই ডেভেলপমেন্ট উভয় ক্ষেত্রেই প্রমাণিত সাফল্য
ডিপলার্নিং.এআই, এমএল শিক্ষার একটি শীর্ষস্থানীয় প্রতিষ্ঠান থেকে সার্টিফিকেশন
তার এআই পদ্ধতির অনন্যতা কী?
শামীম তাত্ত্বিক বোঝার সাথে ব্যবহারিক স্থাপনার দক্ষতার মিশ্রণ ঘটান। তিনি কেবল মডেল তৈরি করার উপরই মনোযোগ দেন না, বরং সেগুলি যাতে উৎপাদনে কাজ করে এবং প্রকৃত ব্যবসায়িক মূল্য সরবরাহ করে তাও নিশ্চিত করেন।

আমি তার কাজ বা অবদান কোথায় দেখতে পারি?

GitHub: github.com/shamimjony1000
LinkedIn: linkedin.com/in/shamim-jony
অবস্থান

ঠিকানা:
খুলশী-১, চট্টগ্রাম, বাংলাদেশ

যোগাযোগ

পেশাদার সুযোগের জন্য আমি কীভাবে শামীমের সাথে যোগাযোগ করতে পারি?
আপনি তার লিঙ্কডইন প্রোফাইলের মাধ্যমে linkedin.com/in/shamim-jony অথবা ইমেলের মাধ্যমে শামীমের সাথে যোগাযোগ করতে পারেন। তিনি দূরবর্তী কাজের সুযোগ, কনসাল্টিং প্রকল্প এবং মেশিন লার্নিং ও এআই ডেভেলপমেন্টের ক্ষেত্রে সহযোগিতার বিষয়ে আলোচনা করতে আগ্রহী।
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
    
    # Check if the question is in Bengali (contains Bengali Unicode characters)
    is_bengali = any('\u0980' <= c <= '\u09FF' for c in question)
    
    prompt = f"""
    You are a helpful customer service assistant for Shamim Md. Jony, a machine learning engineer and software developer.

    Answer the following questions based on the FAQ information provided below.

    If the question is directly addressed in the FAQ, give a clear and accurate answer.

    If the question is not directly addressed, but related to his skills or services, use the FAQ context to provide the most relevant response.

    If the question is unrelated to Shamim Md. Jony's professional profile (such as topics outside AI, software development, LLMs, etc.), politely inform the user that you can only answer questions related to Shamim Md. Jony's services and experience.
    
    IMPORTANT: If the user's question is in Bengali, you MUST respond in Bengali. Look for the Bengali translations in the FAQ data and use those for your response.
    
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
    current_time = datetime.now().strftime("%b %d, %H:%M")
    title = data.get('title', f'Conversation - {current_time}')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO conversations (user_id, title) VALUES (?, ?)', (user_id, title))
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': conversation_id, 'title': title})

@app.route('/conversation/<int:conversation_id>/title', methods=['PUT'])
def update_conversation_title(conversation_id):
    if not is_logged_in():
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.json
    new_title = data.get('title')
    
    if not new_title:
        return jsonify({'error': 'No title provided'}), 400
    
    conn = get_db_connection()
    
    # Check if conversation exists and belongs to the user
    conversation = conn.execute('SELECT * FROM conversations WHERE id = ? AND user_id = ?', 
                             (conversation_id, user_id)).fetchone()
    
    if not conversation:
        conn.close()
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Update the title
    conn.execute('UPDATE conversations SET title = ? WHERE id = ?', 
               (new_title, conversation_id))
    conn.commit()
    conn.close()
    
    return jsonify({'id': conversation_id, 'title': new_title})

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
