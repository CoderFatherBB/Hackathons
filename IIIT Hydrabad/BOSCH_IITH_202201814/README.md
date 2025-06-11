# The Second Mind - AI-Powered Research Assistant

The Second Mind is an advanced AI-based research assistant that helps users explore complex topics by automatically collecting, analyzing, and synthesizing information from various sources. The system iteratively refines research through multiple cycles and provides detailed insights with source credibility evaluation.

## Features

- 🔍 **Intelligent Web Search**: Automatically searches relevant academic and general sources
- 📊 **Source Credibility Analysis**: Evaluates and ranks sources based on relevance, credibility, and technical depth
- 🧠 **Multi-Iteration Research**: Performs multiple research cycles to refine understanding
- 📝 **Comprehensive Reporting**: Generates analysis, key concepts, trends, and knowledge gaps
- 🔄 **Feedback Integration**: Incorporates user feedback to improve research quality
- 🔬 **Deep Research**: Allows focused exploration of specific subtopics
- 📱 **User-Friendly Interface**: Intuitive Streamlit web interface with progress tracking

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- API keys for Groq and Tavily (for LLM access and web search)

### Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root and add your API keys:
   ```
   GROQ_API_KEY="your_groq_api_key"
   TAVILY_API_KEY="your_tavily_api_key"
   ```

### Running the Application

Launch the Streamlit app:
```
streamlit run app.py
```

The application will be available at http://localhost:8501 in your web browser.

## Using the Research Assistant

1. **Start Research**: Enter your research query in the text input field and click "Start Research"
2. **Review Results**: Explore the research results in the different tabs:
   - **Final Results**: Overall findings and recommendations
   - **Iteration Details**: Information from each research cycle
   - **Sources**: Ranked list of sources with detailed information
   - **Raw Data**: Complete JSON data for inspection

3. **Refine Research**:
   - Provide feedback to improve the research quality
   - Request deep research on specific topics
   - Start a new research topic when needed

## Project Structure

- `app.py`: Streamlit web application and user interface
- `stools.py`: Core research engine and supervisor agent implementation
- `.env`: Configuration and API keys
- `research_history.json`: Persistent storage of research history
- `feedback_history.json`: Storage for user feedback

## How It Works

The research assistant operates through a supervisor agent architecture:

1. **Query Processing**: The system takes a user's research query and plans the research approach
2. **Web Search**: Multiple targeted searches are performed to gather information
3. **Source Analysis**: Information sources are categorized and evaluated for credibility
4. **Content Analysis**: Key concepts, trends, and gaps are identified from sources
5. **Multiple Iterations**: The system performs several research cycles, refining its approach
6. **Meta-Analysis**: Final synthesis connects findings across iterations
7. **Presentation**: Results are presented in an organized, user-friendly interface

## Acknowledgments

- Built with Streamlit, Langchain, and Groq LLM
- Uses Tavily for intelligent web search capabilities 