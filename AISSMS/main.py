from flask import Flask, render_template, request
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
import requests
import json
import re


def extract_youtube_video_id(link_dict):
    """Extract YouTube video ID from the 'link' key in a dictionary."""
    if not isinstance(link_dict, dict) or "link" not in link_dict:
        return None  # Skip invalid inputs
    
    url = link_dict["link"]
    if not isinstance(url, str):
        return None  # Skip non-string URLs
    
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

app = Flask(__name__)

# Set your API keys
SERPAPI_KEY = "32c9a0f6319c0042a0f66eff091b1399f16c28f3daff2224083495deb08905ba"
GROQ_API_KEY = "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"

def web_search(query: str, num_results=5) -> list:
    """Search Google for relevant links using SerpAPI and return metadata."""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num_results
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        
        # Extract metadata (title, link, and snippet/description)
        results = []
        for result in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": result.get("title", "No title available"),
                "link": result.get("link", "#"),
                "description": result.get("snippet", "No description available.")
            })
        
        return results if results else [{"title": "No results found", "link": "#", "description": ""}]
    except Exception as e:
        print(f"Error in web_search: {e}")
        return [{"title": "Error fetching results", "link": "#", "description": ""}]

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
)

rag_template = """
You are a ChatBot which Only have a main task to Understant the user problem and help find realated links and articals:
This is the bellow code for it 

'''python
def web_search(query: str, num_results=5) -> list:
    Search Google for relevant links using SerpAPI.
    api_key = SERPAPI_KEY
    url = "https://serpapi.com/search"
    
    params = {{
        "q": query,
        "api_key": api_key,
        "num": num_results
    }}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract top links
    links = [result["link"] for result in data.get("organic_results", [])[:num_results]]
    
    return links if links else ["No relevant links found."]
'''

What you need to do is 2 things if in the given context there is any problem and it solution
you need to find best query which i can use in the function to get the links from youtube 
and you will give one more query always to find the related government yojna/schemes or new policies related to that context.

And you will always give the message in JSON format no matter what always give in JSON and not think more 

Example: 
{{
    "YouTube" : "query",
    "Government Schemes "query"
}}

Context: {context}
"""
rag_prompt = ChatPromptTemplate.from_template(rag_template)
rag_chain = (
    {"context": RunnablePassthrough(),}
    | rag_prompt
    | llm
    | StrOutputParser()
)

def parse_response(response):
    try:
        # Extract JSON content between {}
        match = re.search(r'\{(.|\n)*\}', response)
        if match:
            response = match.group(0)  # Extracted JSON as string
        else:
            return [], []  # Return empty lists if no JSON is found
        
        if response.startswith("{"):
            response = json.loads(response)
            
            youtube_query = response.get("YouTube", "")
            schemes_query = response.get("Government Schemes", "")
            
            
            youtube_links = web_search(f"{youtube_query} on Youtube") if youtube_query else []
            schemes_links = web_search(schemes_query) if schemes_query else []
            print(f"Response from LLM: {response}")
            print(f"YouTube links: {youtube_links}")
            print(f"Schemes links: {schemes_links}")
            return youtube_links, schemes_links
        else:
            return [], []  # Return empty lists if JSON parsing fails
    except Exception as e:
        print(f"Error in parse_response: {e}")
        return [], []  # Return empty lists on error
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        response = rag_chain.invoke({"context": user_input})
        youtube_links, schemes_links = parse_response(response)
        
        # Ensure youtube_links is a list of dictionaries with a "link" key
        youtube_links = [link for link in youtube_links if isinstance(link, dict) and "link" in link]
        
        # Extract YouTube video IDs for embedding
        youtube_video_ids = [extract_youtube_video_id(link) for link in youtube_links]
        
        # Zip YouTube links and video IDs for the template
        youtube_data = zip(youtube_links, youtube_video_ids)
        
        return render_template(
            'index.html',
            youtube_data=youtube_data,  # Pass both link data and video IDs
            schemes_links=schemes_links  # Pass metadata for schemes
        )
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)