from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
import requests
from dataclasses import dataclass
from typing import Dict, Any

# Function to get the current weather
def get_current_weather() -> dict:
    try:
        location_url = "http://ip-api.com/json"
        location_response = requests.get(location_url)
        location_response.raise_for_status()
        location_data = location_response.json()
        
        latitude = location_data['lat']
        longitude = location_data['lon']
        
        # Then get weather using the coordinates
        api_key = "9cc32b17eb9445a7669256a9fddd9f01"
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid={api_key}"
        
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        
        weather_data = weather_response.json()
        weather = {
            'city': location_data['city'],
            'country': location_data['country'],
            'latitude': latitude,
            'longitude': longitude,
            'temperature': weather_data['main']['temp'],
            'description': weather_data['weather'][0]['description'].capitalize(),
            'main': weather_data['weather'][0]['main']
        }
        return weather
        
    except requests.RequestException as e:
        return {'error': f'Could not fetch weather data: {str(e)}'}
    
def set1():
    loader = PyPDFDirectoryLoader("data")
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
        api_key = "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",
        model="llama3-70b-8192"
    )
    weather_data = get_current_weather()

    weekly_template = """
   Data Collection and Preparation
   1.Location: {city}, {country}
   2.Temperature: {temperature}°C
   3.Weather Description: {description}
	4.Fertilizer: Specify the type of fertilizer used. Give Remarks in about 25 to 50 words on recommendations and fertiliser usage in brief about 50 words.
	5.Anything Other Than Fertilizer: Note any additional treatments or amendments used (e.g., pesticides, compost).
	6.Irrigation: Describe the irrigation method (e.g., drip, flood, sprinkler).Give description in about 30 to 50 words.
    7.Status of Crop: Confirm the health status of the crop (e.g., healthy, diseased).
    If any disease detected then give info:
	8.Disease: Indicate any diseases affecting the crop (e.g., grassy shoot, yellow leaf, rust).

   Sample Output for Each Entry
   Fill the information strictly in the following format:
   Temperature: [temperature]°C, Weather: [weather], Location: [location], Fertilizer: [fertilizer], Anything other than fertilizer: [other], Irrigation: [irrigation], Disease: [disease], Status of crop: [status]

   Example Output: 
   Here are some example entries for your dataset:
   Temperature: 30°C, Weather: sunny, Location: Nashik, Maharashtra, Fertilizer: Urea - Remarks in about 25 to 50 words, Anything other than fertilizer: None, Irrigation: drip - Remarks in about 25 to 50 words,Status of crop: healthy
   Temperature: 25°C, Weather: rainy, Location: Kolhapur, Maharashtra, Fertilizer: DAP - Remarks in about 25 to 50 words, Anything other than fertilizer: compost , Irrigation: flood - Remarks in about 25 to 50 words,Status of crop: diseased, Disease: yellow leaf,
   Temperature: 28°C, Weather: cloudy, Location: Pune, Maharashtra, Fertilizer: NPK - Remarks in about 25 to 50 words, Anything other than fertilizer: bio-fertilizer, Irrigation: sprinkler - Remarks in about 25 to 50 words,Status of crop: healthy
   Temperature: 32°C, Weather: sunny, Location: Solapur, Maharashtra, Fertilizer: potassium sulfate - Remarks in about 25 to 50 words, Anything other than fertilizer: None, Irrigation: drip - Remarks in about 25 to 50 words,Status of crop: diseased, Disease: rust, 

   Instructions for Bot Training
	1.	Data Annotation: Ensure each line of your dataset follows the exact format provided above. Consistency is crucial for the bot to learn effectively.
	2.	Data Volume: Collect a large volume of such entries to cover various conditions and scenarios in Indian agriculture.
	3.	Data Diversity: Include a wide range of crops, regions, and conditions to make the bot robust and versatile.
	4.	Labeling: Clearly label healthy and diseased conditions to help the bot differentiate and provide accurate recommendations.
     Answer from this:
    {context}
    Question: {question}
"""

    weekly_prompt = ChatPromptTemplate.from_template(weekly_template).partial(
        city=weather_data['city'],
        country=weather_data['country'],
        temperature=weather_data['temperature'],
        description=weather_data['description']
    )

    rag_chain_weekly = (
        {"context": retriever, "question": RunnablePassthrough()}
        | weekly_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain_weekly
