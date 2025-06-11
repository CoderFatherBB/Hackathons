from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from ultralytics import YOLO
import cv2
import os
from werkzeug.utils import secure_filename
from bot import setup
import textwrap
from News1 import get_news
import requests
import re
import mysql.connector as mysql
from datetime import datetime
from backbot import set1

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

# Database connection
db = mysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="phn",
    port="3306"
)
cursor = db.cursor()
# Your existing configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

model = YOLO(r"model/Step-1-yolov8.pt")
model2 = YOLO(r"model/Step-2-yolov8.pt")
rag = setup()
weekrag = set1()

email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def format_response(response):
    def process_section(section_text):
        
        # Match for bullet points starting with a single '*'
        bullet_pattern = re.compile(r'^\s*\*\s*(.*?)(?=\n\s*\*|\n\s*$|$)', re.MULTILINE)
        
        if bullet_pattern.search(section_text):
            items = bullet_pattern.findall(section_text)
            
            list_items = ''.join([f"<li>{item.strip()}</li>" for item in items])
            
            section_text = bullet_pattern.sub('', section_text)
            
            if section_text.strip():
                return f"{section_text.strip()}<br><ul>{list_items}</ul>"
            return f"<ul>{list_items}</ul>"
        
        return section_text.strip()

    
    # Replace carriage returns
    response = response.replace('\r', '')
    
    # Convert double asterisks to strong (bold) text
    response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)
    
    # Remove colons after headings and labels
    response = re.sub(r':\s*', ' ', response)
    
    # Split the response into paragraphs
    paragraphs = response.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        if para.strip():
            formatted_para = process_section(para)
            formatted_paragraphs.append(formatted_para)
    
    # Add line breaks before the first numbered bullet
    result = '<br><br>'.join(formatted_paragraphs)
    
    # Replace numbered lists to ensure line breaks after each item
    result = re.sub(r'(\d+\.\s*.*?)(?=\n\s*\d+\.|\n\s*$)', r'\1<br>', result)

    # Add two line breaks after sections
    result = re.sub(r'(\d+\.\s*.*?)(?=\n\s*\d+\.|\n\s*$)', r'\1<br><br>', result)

    # Clean up extra spaces and ensure proper line breaks between sections
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'<br>\s*<br>', '<br><br>', result)
    result = re.sub(r'<br>\s*<(ul|ol)', r'<br><br><\1', result)
    result = re.sub(r'(</ul>|</ol>)\s*<br>', r'\1<br><br>', result)
    result = re.sub(r'^(<br>)+', '', result)
    
    return result.strip()

def chat(p):
    response = rag.invoke(p)
    formatted_response = format_response(response)
    return textwrap.fill(formatted_response, width=80)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        })
    
    cursor.execute("SELECT * FROM Data WHERE Username=%s", (username,))
    if cursor.fetchone():
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        })
    
    try:
        cursor.execute("INSERT INTO Data (Username, Password) VALUES (%s, %s)",
                      (username, password))
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'redirect': '/'
        })
    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration'
        })
        
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False, 
            'message': 'Please enter both username and password'
        })
    
    cursor.execute("SELECT * FROM Data WHERE Username=%s AND Password=%s", 
                  (username, password))
    user = cursor.fetchone()
    
    if user:
        session['username'] = username
        return jsonify({
            'success': True,
            'redirect': '/user_dashboard'
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid username or password'
    })
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sugarcane')
def sugarcane():
    return render_template('sugarcane.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

@app.route('/news')
def news():
    news_items = get_news()
    return render_template('news.html', news=news_items)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('chatbot.html')
    
    if request.method == 'POST':
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({'response': 'Please enter a valid message.'}), 400

        bot_response = chat(user_message)
        return jsonify({'response': bot_response}), 200

@app.route('/detect', methods=['POST'])
def detect():
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    # Get the username from session
    username = session['username']
    
    # Calculate current week from start date
    cursor.execute("SELECT start_date FROM Data WHERE Username=%s", (username,))
    start_date_result = cursor.fetchone()
    
    if not start_date_result or not start_date_result[0]:
        return jsonify({'error': 'Please set a start date first'}), 400
        
    start_date = start_date_result[0]
    current_date = datetime.now()
    days_difference = (current_date - start_date).days
    week = (days_difference // 7) + 1
    
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image = cv2.imread(file_path)
        
        r = model.predict(image, verbose=False)
        Result = ["Disease", "Dried", "Healthy"]
        P = Result[r[0].probs.top1]
        if P == "Disease":
            D = [
                'Banded Chlorosis', 'Brown Rust', 'Brown Spot', 'Grassy shoot', 
                'Mosaic', 'Pokkah Boeng', 'RedRot', 'RedRust', 'Sett Rot', 
                'Viral Disease', 'Yellow Leaf', 'Smut'
            ]
            d = model2.predict(image, verbose=False)
            disease_name = D[d[0].probs.top1]
            confidence = float(max(d[0].probs.data * 100))
            bot_response = chat(f"Give solutions for sugarcane with disease: {disease_name} disease detected in week {week}. Recommend some good fertilizers if needed.")
            
            weekly_prompt = f"Give data entry for sugarcane with disease: {disease_name} in week {week} for temperature, weather, location, fertilizer, anything other than fertilizer, irrigation and status of crop"
            weekly_analysis = weekrag.invoke(weekly_prompt)
            irrigation = ""
            fertiliser = ""
            
            irrigation_match = re.search(r'Irrigation:\s*([^,\n]+)', weekly_analysis)
            fertilizer_match = re.search(r'Fertilizer:\s*([^,\n]+)', weekly_analysis)
            
            if irrigation_match:
                irrigation = irrigation_match.group(1).strip()
            if fertilizer_match:
                fertiliser = fertilizer_match.group(1).strip()
            
            try:
                cursor.execute("""
                    INSERT INTO Analysis (Username, Irrigation, Fertiliser, Week)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    Irrigation = VALUES(Irrigation),
                    Fertiliser = VALUES(Fertiliser)
                """, (username, irrigation, fertiliser, week))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Database error: {str(e)}")
                
            try:
                cursor.execute("""
                    INSERT INTO big (Username, Week, analysis)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    analysis = VALUES(analysis)
                """, (username, week, weekly_analysis))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Database error: {str(e)}")
                
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
            }), 200
        
        elif P == "Dried":
            confidence = float(max(r[0].probs.data * 100))
            return jsonify({
                'result': f"Dried with confidence: {confidence:.2f}%",
                'bot_response': "Consider proper irrigation to avoid dryness issues.",
            }), 200
        
        elif P == "Healthy":
            confidence = float(max(r[0].probs.data * 100))
            bot_response = chat(f"Recommend good tips for healthy sugarcane in week {week} for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            weekly_prompt = f"Give data entry for healthy sugarcane in week {week} for temperature, weather, location, fertilizer, anything other than fertilizer, irrigation and status of crop"
            weekly_analysis = weekrag.invoke(weekly_prompt)
            irrigation = ""
            fertiliser = ""
            
            irrigation_match = re.search(r'Irrigation:\s*([^,\n]+)', weekly_analysis)
            fertilizer_match = re.search(r'Fertilizer:\s*([^,\n]+)', weekly_analysis)
            
            if irrigation_match:
                irrigation = irrigation_match.group(1).strip()
            if fertilizer_match:
                fertiliser = fertilizer_match.group(1).strip()
            
            try:
                cursor.execute("""
                    INSERT INTO Analysis (Username, Irrigation, Fertiliser, Week)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    Irrigation = VALUES(Irrigation),
                    Fertiliser = VALUES(Fertiliser)
                """, (username, irrigation, fertiliser, week))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Database error: {str(e)}")
                
            try:
                cursor.execute("""
                    INSERT INTO big (Username, Week, analysis)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    analysis = VALUES(analysis)
                """, (username, week, weekly_analysis))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Database error: {str(e)}")
                
            return jsonify({
                'result': f"All Good with confidence: {confidence:.2f}%",
                'bot_response': bot_response,
            }), 200

    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude and longitude:
        api_key = "9cc32b17eb9445a7669256a9fddd9f01"
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid={api_key}"
        
        try:
            response = requests.get(weather_url)
            response.raise_for_status()  
            
            weather_data = response.json()
            weather = {
                'temperature': weather_data['main']['temp'],
                'description': weather_data['weather'][0]['description'].capitalize(),
                'main': weather_data['weather'][0]['main']  
            }
            return jsonify({'weather': weather}), 200
            
        except requests.RequestException as e:
            return jsonify({'error': f'Could not fetch weather data: {str(e)}'}), 500
    return jsonify({'error': 'Invalid location data'}), 400

@app.route('/check_start_date')
def check_start_date():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    cursor.execute("SELECT start_date FROM Data WHERE Username=%s", (username,))
    result = cursor.fetchone()
    
    if result and result[0]:
        return jsonify({
            'hasDate': True,
            'date': result[0].strftime('%d %B, %Y')
        })
    return jsonify({'hasDate': False})

@app.route('/set_start_date', methods=['POST'])
def set_start_date():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    start_date = data.get('date')
    
    try:
        # Convert string date to datetime object
        date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        
        cursor.execute(
            "UPDATE Data SET start_date=%s WHERE Username=%s",
            (date_obj, session['username'])
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'formattedDate': date_obj.strftime('%d %B, %Y')
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_schedule')
def get_schedule():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    
    # Get all tasks for the user ordered by week
    cursor.execute("""
        SELECT Week, Irrigation, Fertiliser, IC, FC 
        FROM Analysis 
        WHERE Username = %s
        ORDER BY Week DESC
    """, (username,))
    
    results = cursor.fetchall()
    
    if results:
        # Format all tasks
        tasks = []
        for week, irrigation, fertiliser, ic, fc in results:
            tasks.append({
                'week': week,
                'irrigation': irrigation if irrigation else '',
                'fertilizer': fertiliser if fertiliser else '',
                'irrigationComplete': bool(ic),
                'fertilizerComplete': bool(fc)
            })
        return jsonify(tasks)
    
    return jsonify([])

@app.route('/update_task', methods=['POST'])
def update_task():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    task_type = data.get('type')
    week = data.get('week')
    
    try:
        if task_type == 'irrigation':
            cursor.execute("""
                UPDATE Analysis 
                SET IC = 1 
                WHERE Username = %s AND Week = %s
            """, (username, week))
        elif task_type == 'fertilizer':
            cursor.execute("""
                UPDATE Analysis 
                SET FC = 1 
                WHERE Username = %s AND Week = %s
            """, (username, week))
        
        db.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)