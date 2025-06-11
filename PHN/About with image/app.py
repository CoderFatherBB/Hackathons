from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
import cv2
import os
from werkzeug.utils import secure_filename
from bot import setup
import textwrap
from News1 import get_news
import requests
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



model = YOLO(r"model/Step-1-yolov8.pt")
model2 = YOLO(r"model/Step-2-yolov8.pt")



rag = setup()

def format_response(response):
    """
    Format a chatbot response with proper HTML handling and valid escape sequences.
    """
    def process_section(section_text):
        
        bullet_pattern = re.compile(r'^\s*\*\s*(.*?)(?=\n\s*\*|\n\s*$|$)', re.MULTILINE)
        if bullet_pattern.search(section_text):
            items = bullet_pattern.findall(section_text)
            list_items = ''.join([f"<li>{item.strip()}</li>" for item in items])
            section_text = bullet_pattern.sub('', section_text)
            if section_text.strip():
                return f"{section_text.strip()}<br><ul>{list_items}</ul>"
            return f"<ul>{list_items}</ul>"
        return section_text.strip()

    
    response = response.replace('\r', '')
    
    
    response = re.sub(r'\*(Step \d+:.*?)\*\*', r'**\1**', response)
    
    
    response = re.sub(r'\*\*(.*?)\*\*', r'<br><br><strong>\1</strong><br>', response)
    
    
    paragraphs = response.split('\n\n')
    
    formatted_paragraphs = []
    for para in paragraphs:
        if para.strip():
            
            if re.match(r'\s*\d+\.', para):
                items = re.split(r'\s*\d+\.\s*', para)[1:]
                list_items = ''.join([f"<li>{item.strip()}</li>" for item in items])
                formatted_para = f"<ol>{list_items}</ol>"
            else:
                formatted_para = process_section(para)
            
            formatted_paragraphs.append(formatted_para)
    
    
    result = ' '.join(formatted_paragraphs)
    
    
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'<br>\s*<br>', '<br><br>', result)
    result = re.sub(r'<br>\s*<(ol|ul)', r'<br><br><\1', result)
    result = re.sub(r'(</ol>|</ul>)\s*<br>', r'\1<br><br>', result)
    result = re.sub(r'^(<br>)+', '', result)
    
    return result.strip()

def chat(p):
    response = rag.invoke(p)
    formatted_response = format_response(response)
    return textwrap.fill(formatted_response, width=80)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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

@app.route('/')
def login():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sugarcane')
def sugarcane():
    return render_template('sugarcane.html')

@app.route('/profile')
def profile():
    return render_template('profile_settings.html')

@app.route('/settings')
def settings():
    return render_template('profile_settings.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/news')
def news():
    news_items = get_news()
    return render_template('news.html', news=news_items)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
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
    week = 4
    
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
            
            
            bot_response = chat(f"I have a sugarcane with {disease_name} disease detected in week {week} and give some solutions for this.")
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response
            }), 200
        
        elif P == "Dried":
            confidence = float(max(r[0].probs.data * 100))
            return jsonify({
                'result': f"Dried with confidence: {confidence:.2f}%",
                'bot_response': "Consider proper irrigation to avoid dryness issues."
            }), 200
        
        elif P == "Healthy":
            confidence = float(max(r[0].probs.data * 100))
            
            
            bot_response = chat(f"I have a healthy sugarcane in week {week}. Recommend good tips for its maintenance and keeping it healthy.")
            return jsonify({
                'result': f"All Good with confidence: {confidence:.2f}%",
                'bot_response': bot_response
            }), 200

    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)