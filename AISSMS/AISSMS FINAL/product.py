from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
import requests
import json
import re

def is_agriculture_related(query: str) -> bool:
    GROQ_API_KEY = "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"
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
    )

    prompt = """
    You are an agriculture query validator. Your task is to determine if the user's query is related to agriculture or farming.

    Examples of agriculture-related queries:
    - "wheat seeds"
    - "organic fertilizers"
    - "tractor parts"
    - "crop irrigation systems"

    Examples of non-agriculture-related queries:
    - "smartphones"
    - "laptops"
    - "cars"
    - "movies"

    Return "yes" if the query is related to agriculture, otherwise return "no".

    Query: {query}
    """

    response = llm.invoke(prompt.format(query=query))
    return response.content.lower()

def web_search_product(query: str, num_results=10) -> list:
    """Search for agricultural products in India and return product details in INR."""
    SERPAPI_KEY = "163d0a2c7a171e2b5e1651decea27e14f37f51d274d5e83e3e89c50cccd59825"
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num_results,
        "tbm": "shop",  # Use Google Shopping for product search
        "gl": "in",  # Restrict results to India
        "hl": "en",  # Language: English
        "currency": "INR"  # Currency: Indian Rupees
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        
        # Extract product details
        products = []
        for result in data.get("shopping_results", [])[:num_results]:
            products.append({
                "title": result.get("title", "No title available"),
                "price": result.get("price", "Price not available"),
                "link": result.get("link", "#"),
                "source": result.get("source", "Unknown source"),
                "image": result.get("thumbnail", ""),  # Fetch product image
                "description": result.get("description", "No description available.")
            })
        
        return products if products else [{"title": "No products found", "link": "#", "price": "", "source": "", "image": "", "description": ""}]
    except Exception as e:
        print(f"Error in web_search_product: {e}")
        return [{"title": "Error fetching products", "link": "#", "price": "", "source": "", "image": "", "description": ""}]
    
