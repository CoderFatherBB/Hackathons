from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
import textwrap
import json
import matplotlib.pyplot as plt
import re
import pandas as pd


# Initialize the Groq model
llm = ChatGroq(
    api_key="",
    model="llama3-8b-8192"
)

# Define the soil analysis template
soil_template = """You are an agricultural expert. Analyze the following soil data and provide detailed recommendations in JSON format:
Location: {location}
Return the response in the following JSON format with no extra text before or after, in this exact format:
{{
    "location": "{location}",
    "soil_parameters": {{
        "pH": <value>,
        "organic_matter": <value>,
        "nitrogen": <value>,
        "phosphorus": <value>,
        "potassium": <value>
    }},
    "suitable_crops": ["Crop1", "Crop2", "Crop3"],
    "recommended_fertilizers": {{
        "organic": ["Fertilizer1", "Fertilizer2"],
        "chemical": ["Fertilizer3", "Fertilizer4"]
    }},
    "soil_management_practices": ["Practice1", "Practice2", "Practice3"]
}}"""

# Create the prompt template
soil_prompt = ChatPromptTemplate.from_template(soil_template)

# Create the chain
soil_chain = soil_prompt | llm | StrOutputParser()

# Reference soil requirements for selected crops
soil_reference = {
    "Sugarcane": {"pH": (6.5, 7.5), "organic_matter": (2.0, 4.0), "nitrogen": (25, 50), "phosphorus": (15, 30), "potassium": (120, 200)},
    "Grape": {"pH": (5.5, 7.0), "organic_matter": (2.5, 5.0), "nitrogen": (30, 50), "phosphorus": (20, 40), "potassium": (150, 250)},
    "Apple": {"pH": (5.5, 6.8), "organic_matter": (3.0, 5.0), "nitrogen": (20, 40), "phosphorus": (15, 35), "potassium": (120, 180)},
    "Tomato": {"pH": (6.0, 7.0), "organic_matter": (2.5, 4.5), "nitrogen": (25, 45), "phosphorus": (20, 50), "potassium": (100, 180)},
    "Jowar": {"pH": (5.5, 7.5), "organic_matter": (1.5, 3.5), "nitrogen": (20, 40), "phosphorus": (10, 25), "potassium": (100, 180)},
    "Coconut": {"pH": (5.2, 6.8), "organic_matter": (2.0, 4.0), "nitrogen": (25, 50), "phosphorus": (15, 30), "potassium": (150, 250)},
}

def parse_response(response):
    """
    Parse and clean the response to ensure valid JSON
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return {"error": "No JSON content found in response"}
        except Exception as e:
            return {"error": f"Failed to parse response: {str(e)}"}

def analyze_soil(location: str):
    """
    Analyze soil data and return structured JSON output.
    """
    try:
        input_data = {"location": str(location)}
        response = soil_chain.invoke(input_data)
        soil_data = parse_response(response)
        return soil_data
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def generate_soil_report_table(soil_data):
    """
    Generate a soil report table dynamically based on the soil analysis and reference data.
    """
    if "error" in soil_data:
        return {"error": soil_data["error"]}

    parameters = soil_data["soil_parameters"]
    location = soil_data["location"]

    table_data = []

    for crop, req_values in soil_reference.items():
        row = {"Crop": crop, "Location": location}

        for param, (min_val, max_val) in req_values.items():
            actual_value = parameters.get(param, "N/A")
            
            # If actual_value is a number, check if it's within the required range
            if isinstance(actual_value, (int, float)):
                if min_val <= actual_value <= max_val:
                    row[param] = actual_value  # Value is within the range
                else:
                    row[param] = "N/A"  # Out of range
            else:
                row[param] = "N/A"  # If data is missing

        table_data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    return df

def plot_soil_parameters(soil_data):
    """
    Plot soil parameters as a horizontal bar chart.
    """
    try:
        if "error" in soil_data:
            print(f"Cannot plot: {soil_data['error']}")
            return

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
        plt.show()
    except Exception as e:
        print(f"Error plotting data: {str(e)}")
        
def generate_detailed_analysis(soil_data):
    """
    Generate a detailed soil analysis text from the JSON data.
    """
    if "error" in soil_data:
        return soil_data["error"]

    location = soil_data["location"]
    soil_params = soil_data["soil_parameters"]
    suitable_crops = soil_data["suitable_crops"]
    fertilizers = soil_data["recommended_fertilizers"]
    practices = soil_data["soil_management_practices"]

    analysis_text = f"""
    **Soil Analysis Report for {location}**

    **Soil Parameters:**
    - pH: {soil_params['pH']}
    - Organic Matter: {soil_params['organic_matter']}%
    - Nitrogen: {soil_params['nitrogen']} ppm
    - Phosphorus: {soil_params['phosphorus']} ppm
    - Potassium: {soil_params['potassium']} ppm

    **Suitable Crops:**
    {', '.join(suitable_crops)}

    **Recommended Fertilizers:**
    - Organic: {', '.join(fertilizers['organic'])}
    - Chemical: {', '.join(fertilizers['chemical'])}

    **Soil Management Practices:**
    {', '.join(practices)}
    """

    return analysis_text.strip()