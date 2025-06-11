from flask import Flask, render_template, request, jsonify, redirect, url_for
from ultralytics import YOLO
import os
from werkzeug.utils import secure_filename
import textwrap
import requests
from bot import sc
import re,io,base64
from News1 import extract_youtube_video_id,parse_response,setscheme
from product import web_search_product,is_agriculture_related
import cv2
from soil import analyze_soil, generate_soil_report_table, plot_soil_parameters,generate_detailed_analysis
import matplotlib
matplotlib.use('Agg')  # Set the backend to 'Agg'
import matplotlib.pyplot as plt




scheme = setscheme()
sgbot = sc()

app = Flask(__name__)
app.secret_key = 'xgdtrshdhy5dckjnhv'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


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
    response = sgbot.invoke(p)
    formatted_response = format_response(response)
    return textwrap.fill(formatted_response, width=80)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')

    
@app.route('/irrigation_mapper')
def irrigation_mapper():
    return render_template('irrigation_mapper.html')

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sugarcane')
def sugarcane():
    return render_template('sugarcane.html')

@app.route('/apple')
def apple():
    return render_template('apple.html')

@app.route('/coconut')
def coconut():
    return render_template('coconut.html')

@app.route('/jowar')
def jowar():
    return render_template('jowar.html')

@app.route('/tomato')
def tomato():
    return render_template('tomato.html')

@app.route('/grape')
def grape():
    return render_template('grape.html')


@app.route('/finance')
def finance():
    return render_template('finance.html')

@app.route('/marketplace', methods=['GET', 'POST'])
def marketplace():
    products = []  # Initialize products as an empty list
    error_message = None  # Initialize error message

    if request.method == 'POST':
        user_input = request.form['user_input']
        
        # Validate if the query is related to agriculture
        if is_agriculture_related(user_input) == "no":
            error_message = "Please enter a product related to agriculture only."
        else:
            # Fetch products only if the query is valid
            products = web_search_product(user_input)
    
    return render_template(
        'marketplace.html',
        products=products,  # Pass products to the template
        is_search=request.method == 'POST',  # Indicate if a search was performed
        error_message=error_message  # Pass error message to the template
    )
    

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')
    
@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        user_input = request.form['user_input']
        response = scheme.invoke({"context": user_input})
        youtube_links, schemes_links = parse_response(response)
        
        # Ensure youtube_links is a list of dictionaries with a "link" key
        youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
        
        # Extract YouTube video IDs for embedding
        youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
        
        # Zip YouTube links and video IDs for the template
        youtube_data = zip(youtube_links, youtube_video_ids)
        
        return render_template(
            'news.html',
            youtube_data=youtube_data,  # Pass both link data and video IDs
            schemes_links=schemes_links  # Pass metadata for schemes
        )
    return render_template('news.html')

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




from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

def extract_agricultural_products(text: str) -> list:
    """
    Extract agricultural product names from the given text using an LLM.
    """
    GROQ_API_KEY = "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"
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
    )

    prompt = """
    You are an agricultural product extractor. Your task is to identify and extract all agricultural-related products mentioned in the text.

    Examples of agricultural products:
    - Fertilizers
    - Pesticides
    - Seeds
    - Irrigation tools
    - Farming equipment
    - Organic compost
    - Crop protection products

    Return the extracted products as a comma-separated list. If no products are found, return an empty string.

    Text: {text}
    """

    response = llm.invoke(prompt.format(text=text))
    extracted_products = response.content.strip()

    # Split the comma-separated list into a list of products
    if extracted_products:
        return [product.strip() for product in extracted_products.split(",")]
    return []









@app.route('/detects', methods=['POST'])
def detects():
    model = YOLO(r"model/Step-1-yolov8.pt")
    model2 = YOLO(r"model/Step-2-yolov8.pt")
    
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
            bot_response = chat(f"Give solutions for sugarcane with disease: {disease_name} disease detected in week 1. Recommend some good fertilizers if needed.")
            
            # Send bot response to scheme.invoke
            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
        
        elif P == "Dried":
            confidence = float(max(r[0].probs.data * 100))
            return jsonify({
                'result': f"Dried with confidence: {confidence:.2f}%",
                'bot_response': "Consider proper irrigation to avoid dryness issues.",
            }), 200
        
        elif P == "Healthy":
            confidence = float(max(r[0].probs.data * 100))
            bot_response = chat(f"Recommend good tips for healthy sugarcane for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
                'result': f"All Good with confidence: {confidence:.2f}%",
                'bot_response': bot_response,
            }), 200

    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.route('/detecta', methods=['POST'])
def detecta():
    model = YOLO("model/Apple.pt")
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
        Result = ['Apple_Black_rot', 'Healthy','Apple_rust','Apple_scab']
        disease_name = Result[r[0].probs.top1]
        confidence = float(max(r[0].probs.data * 100))
        if disease_name == "Healthy":
            bot_response = chat(f"Recommend good tips for healthy apple plant for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
            'result': f"All Good with confidence: {confidence:.2f}%",
            'bot_response': bot_response,
        }), 200
            
        else:
            bot_response = chat(f"Give solutions for jowar plant with {disease_name} disease detected. Recommend some good fertilizers if needed.")

            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
        
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    
    
    
    
    
    
    
    
    
    
@app.route('/detectj', methods=['POST'])
def detectj():
    model = YOLO("model/jowar.pt")
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
        Result = ['Anthracnose and Red Rot', 'Cereal Grain molds','Covered Kernel smut','Head Smut','Rust','loose smut']
        disease_name = Result[r[0].probs.top1]
        confidence = float(max(r[0].probs.data * 100))
        
        if disease_name == "Healthy":
            bot_response = chat(f"Recommend good tips for healthy jowar plant for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
            'result': f"All Good with confidence: {confidence:.2f}%",
            'bot_response': bot_response,
        }), 200
            
        else:
            bot_response = chat(f"Give solutions for jowar plant with {disease_name} disease detected. Recommend some good fertilizers if needed.")
        
            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    
    
    
    
    
@app.route('/detectc', methods=['POST'])
def detectc():
    model = YOLO("model/coconut.pt")
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
        Result = ['Bud Root Dropping', 'Bud Rot','Gray Leaf Spot','Leaf Rot','Stem Bleeding']
        disease_name = Result[r[0].probs.top1]
        confidence = float(max(r[0].probs.data * 100))
        if disease_name == "Healthy":
            bot_response = chat(f"Recommend good tips for healthy coconut plant for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
            'result': f"All Good with confidence: {confidence:.2f}%",
            'bot_response': bot_response,
        }), 200
            
        else:
            bot_response = chat(f"Give solutions for coconut plant with {disease_name} disease detected. Recommend some good fertilizers if needed.")
        
            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
        
        

    else:
        return jsonify({'error': 'Invalid file type'}), 400








@app.route('/detectg', methods=['POST'])
def detectg():
    model = YOLO("model/Grape.pt")
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
        Result = ['Grape_Black_rot', 'Grape_Esca', 'Healthy', 'Grape_spot']
        disease_name = Result[r[0].probs.top1]
        confidence = float(max(r[0].probs.data * 100))
        if disease_name == "Healthy":
            bot_response = chat(f"Recommend good tips for healthy grape plant for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
            'result': f"All Good with confidence: {confidence:.2f}%",
            'bot_response': bot_response,
        }), 200
            
        else:
            bot_response = chat(f"Give solutions for grape plant with {disease_name} disease detected. Recommend some good fertilizers if needed.")
        
            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    
    
    
    
    
    
    
    
    
    
@app.route('/detectt', methods=['POST'])
def detectt():
    model = YOLO("model/Tomato.pt")
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
        Result = ['Bacterial spot', 'Early Blight', 'Late Blight', 'Leaf Mold', 'Septoria Leaf Spot', 'Spider Mites Two Spotted Spider Mite', 'Target Spot', 'Yellow Leaf Curl Virus', 'Mosaic Virus', 'Healthy']
        disease_name = Result[r[0].probs.top1]
        confidence = float(max(r[0].probs.data * 100))
        if disease_name == "Healthy":
            bot_response = chat(f"Recommend good tips for healthy tomato plant for its maintenance and keeping it healthy. Recommend some good fertilizers if needed.")
            return jsonify({
            'result': f"All Good with confidence: {confidence:.2f}%",
            'bot_response': bot_response,
        }), 200
            
        else:
            bot_response = chat(f"Give solutions for tomato plant with {disease_name} disease detected. Recommend some good fertilizers if needed.")
        
            scheme_response = scheme.invoke({"context": bot_response})
            youtube_links, schemes_links = parse_response(scheme_response)
            
            # Ensure youtube_links is a list of dictionaries with a "link" key
            youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
            
            # Extract YouTube video IDs for embedding
            youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
            
            # Zip YouTube links and video IDs for the template
            youtube_data = zip(youtube_links, youtube_video_ids)
            
            # Extract agricultural products from bot response
            product_names = extract_agricultural_products(bot_response)
            products = []
            for product_name in product_names:
                if is_agriculture_related(product_name) == "yes":
                    products.extend(web_search_product(product_name, num_results=1))  # Fetch top 3 products for each keyword
            
            return jsonify({
                'result': f"Disease detected: {disease_name} with confidence {confidence:.2f}%",
                'bot_response': bot_response,
                'youtube_data': [{'link': link['link'], 'video_id': video_id, 'title': link.get('title', 'YouTube Tutorial')} for link, video_id in youtube_data],
                'products': products  # Include product details in the response
            }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400








@app.route('/analyze_soil', methods=['POST'])
def analyze_soil_route():
    # Get latitude and longitude from the request
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    try:
        # Fetch location name using reverse geocoding
        location_response = requests.get(
            f"https://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&limit=1&appid=9cc32b17eb9445a7669256a9fddd9f01"
        )
        location_response.raise_for_status()
        location_data = location_response.json()
        location_name = location_data[0].get('name', 'Unknown Location')

        # Fetch weather data
        weather_response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid=9cc32b17eb9445a7669256a9fddd9f01"
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # Call the soil analysis function
        soil_data = analyze_soil(location_name)

        # Generate detailed analysis text
        detailed_analysis = generate_detailed_analysis(soil_data)

        # Generate soil report table
        soil_report_df = generate_soil_report_table(soil_data)

        # Generate soil parameters graph
        graph_data = generate_soil_graph(soil_data)

        # Return the results
        return jsonify({
            'location': location_name,
            'weather': weather_data,
            'detailed_analysis': format_response(detailed_analysis),
            'soil_report_table': soil_report_df.to_dict(orient='records'),
            'graph_data': graph_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error during soil analysis: {str(e)}'}), 500

def generate_soil_graph(soil_data):
    """
    Generate a base64-encoded image of the soil parameters graph.
    """
    import matplotlib.pyplot as plt
    import io
    import base64

    if "error" in soil_data:
        return None

    parameters = soil_data["soil_parameters"]
    labels = list(parameters.keys())
    values = list(parameters.values())

    plt.figure(figsize=(10, 6))
    bars = plt.barh(labels, values, color=['blue', 'green', 'red', 'purple', 'orange'])

    # Add value labels on each bar
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                 f'{width:.2f}',
                 ha='left', va='center')

    plt.ylabel("Soil Parameters")
    plt.xlabel("Values")
    plt.title(f"Soil Analysis for {soil_data['location']}")
    plt.gca().invert_yaxis()  # Optional: Invert y-axis for better readability
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Encode the image as base64
    graph_data = base64.b64encode(buf.read()).decode('utf-8')
    return graph_data





from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community import embeddings
from langchain.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_groq import ChatGroq
import textwrap




# Your loader and vectorstore setup code remains the same
loader = PyPDFDirectoryLoader("new_data")
the_text = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = text_splitter.split_documents(the_text)

vectorstore = Chroma.from_documents(
    documents=docs,
    collection_name="ollama_embeds",
    embedding=OllamaEmbeddings(model='nomic-embed-text'),
)
retriever = vectorstore.as_retriever()

llm = ChatGroq(
    api_key="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",
    model="llama3-8b-8192"
)

# Define agricultural analysis template
agri_template = """You are an agricultural and financial expert. Analyze the following data and provide detailed recommendations:

Location: {location}
Land Size: {land_size} acres
Land Type: {land_type}
Budget: Rs. {budget}
Crop Type: {crop_type}

Please provide a comprehensive analysis including:

1. Initial Assessment:
   - Complete soil analysis for {location} and land type {land_type}
   - Climate suitability assessment
   - Water availability analysis

2. Financial Planning:
   2.1. Expected Expenditures (Detailed Breakdown):
       - Fertilizer and Agrochemicals: List with quantities and costs
       - Planting Material: Variety recommendations with costs
       - Labor Requirements: Schedule and costs
       - Equipment Needs: Purchase/rental recommendations
       - Irrigation System: Setup and maintenance costs

   2.2. Expected Income:
       - Projected Yield: Based on local averages
       - Market Price Analysis: Current and projected
       - Revenue Calculations
       - ROI Analysis

3. Technical Implementation Plan:
   - Land Preparation Schedule
   - Planting Guidelines
   - Spacing and Population Density
   - Nutrient Management Calendar
   - Irrigation Schedule
   - Pest Management Strategy
   - Harvest Planning

4. Risk Assessment:
   - Climate Risks for {location} and land type {land_type}
   - Market Risks
   - Mitigation Strategies

Provide all financial figures in Indian Rupees (Rs.) and ensure recommendations are practical and location-specific.
"""

# Create the prompt template
agri_prompt = ChatPromptTemplate.from_template(agri_template)

# Create the chain
agri_chain = (
    {
        "location": lambda x: x["location"],
        "land_size": lambda x: x["land_size"],
        "budget": lambda x: x["budget"],
        "crop_type": lambda x: x["crop_type"],
        "land_type": lambda x: x["land_type"]
    }
    | agri_prompt
    | llm
    | StrOutputParser()
)

def analyze_agricultural_project(
    location: str,
    land_size: float,
    budget: float,
    crop_type: str,
    land_type: str  # Added land_type parameter
) -> str:
    """
    Analyze agricultural project and generate comprehensive recommendations
    
    Args:
        location (str): Geographic location of the farm
        land_size (float): Size of land in acres
        budget (float): Available budget in Rs.
        crop_type (str): Type of crop to be cultivated
        land_type (str): Type of soil/land
    
    Returns:
        str: Formatted analysis report
    """
    try:
        input_data = {
            "location": location,
            "land_size": land_size,
            "budget": budget,
            "crop_type": crop_type,
            "land_type": land_type
        }
        
        # Get the analysis
        response = agri_chain.invoke(input_data)
        
        # Format the output
        formatted_response = textwrap.fill(response, width=100)
        return formatted_response
    
    except Exception as e:
        return f"Error during analysis: {str(e)}"


def analyze_agricultural_project(
    location: str,
    land_size: float,
    budget: float,
    crop_type: str,
    land_type: str
) -> str:
    """
    Analyze agricultural project and generate comprehensive recommendations.
    """
    try:
        input_data = {
            "location": location,
            "land_size": land_size,
            "budget": budget,
            "crop_type": crop_type,
            "land_type": land_type
        }
        
        # Get the analysis
        response = agri_chain.invoke(input_data)
        
        # Format the output
        formatted_response = textwrap.fill(response, width=100)
        return formatted_response
    
    except Exception as e:
        return f"Error during analysis: {str(e)}"
    
    
    
    
    
    
    
    
    
    
@app.route('/analyze_finance', methods=['POST'])
def analyze_finance():
    data = request.get_json()
    location = data.get('location')
    crop_type = data.get('crop_type')
    land_size = data.get('land_size')
    budget = data.get('budget')
    land_type = data.get('land_type')

    if not location or not crop_type or not land_size or not budget or not land_type:
        return jsonify({'error': 'All fields are required'}), 400

    try:
        # Call the LLM for financial analysis
        analysis = analyze_agricultural_project(
            location=location,
            land_size=land_size,
            budget=budget,
            crop_type=crop_type,
            land_type=land_type
        )

        return jsonify({
            'location': location,
            'crop_type': crop_type,
            'analysis': analysis
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error during analysis: {str(e)}'}), 500







if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8000,debug=True)