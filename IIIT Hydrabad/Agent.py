import os
import re
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque
import numpy as np

from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough

# Configuration constants
MAX_HISTORY = 10  # Maximum number of history items to store
DEFAULT_ITERATIONS = 2  # Number of research iterations per query
HISTORY_FILE = "research_history.json"  # File for persistent storage of research history

# Initialize the LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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") # "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"
llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.7)

@dataclass
class ResearchMemory:
    """
    Data class for storing detailed research memory
    
    Attributes:
        query: The original research query
        hypothesis: Current hypothesis
        score: Rating of the hypothesis quality
        timestamp: When this memory was created
        web_data: Data extracted from web
        sources: Relevant sources used
        key_concepts: Important concepts identified
    """
    query: str
    hypothesis: str
    score: float
    timestamp: datetime
    web_data: Dict[str, Any]
    sources: List[Dict[str, Any]] = None
    key_concepts: List[str] = None

@dataclass
class HistoryItem:
    """
    Data class for storing research history items
    
    Attributes:
        query: The original research query
        timestamp: When the research was conducted
        top_solutions: Best solutions found during research
        key_concepts: Important concepts identified in the research
        related_queries: Other queries related to this research
    """
    query: str
    timestamp: str
    top_solutions: List[Dict]
    key_concepts: List[str]
    related_queries: List[str]

class Agent:
    """Base agent class with common functionality"""
    def __init__(self, name: str, llm):
        self.name = name
        self.llm = llm
        self.memory = ConversationBufferMemory(return_messages=True)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        raise NotImplementedError

class WebExtractor:
    """
    Web data extraction module to gather real-time information
    
    Capabilities:
    - Extract data from search results
    - Categorize sources by type
    - Retrieve content snippets
    """
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract information from the web based on the query
        
        Args:
            query: Search query 
            
        Returns:
            Dictionary with extracted web data
        """
        search_url = f"https://news.google.com/search?q={query}&hl=en-US"
        try:
            response = self.session.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract articles
            articles = soup.find_all('article')
            extracted_articles = []
            
            for article in articles[:5]:  # Limit to first 5 articles
                title_elem = article.find('h3')
                snippet_elem = article.find('p')
                
                article_data = {
                    "title": title_elem.text if title_elem else "Untitled",
                    "snippet": snippet_elem.text if snippet_elem else "",
                    "source": self._extract_source(article),
                    "date": self._extract_date(article)
                }
                
                extracted_articles.append(article_data)
            
            # Extract trending topics
            trend_section = soup.find('div', {'jsname': 'JD8Qqd'})
            trending = []
            
            if trend_section:
                trend_items = trend_section.find_all('div', {'jsname': 'kfWnTd'})
                for item in trend_items[:3]:
                    trending.append(item.text if item else "")
            
            return {
                "articles": extracted_articles,
                "trending": trending,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "articles": [],
                "trending": [],
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_source(self, article):
        """Extract source from article"""
        source_elem = article.find('div', {'class': 'SVJrMe'})
        return source_elem.text if source_elem else "Unknown Source"
    
    def _extract_date(self, article):
        """Extract date from article"""
        date_elem = article.find('time')
        return date_elem.get('datetime') if date_elem else ""

class GenerationAgent(Agent):
    """
    Generation Agent creates initial hypotheses based on queries
    
    This agent generates creative, informed hypotheses by combining:
    - The user's research query
    - Real-time web data
    - Past related experiences
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate initial hypothesis for the research query
        
        Args:
            input_data: Contains query and web data
            
        Returns:
            Dictionary with generated hypothesis
        """
        query = input_data.get("query", "")
        web_data = input_data.get("web_data", {})
        past_memories = input_data.get("past_memories", [])
        
        # Extract articles from web data for context
        articles = web_data.get("articles", [])
        article_info = "\n".join([
            f"- {a.get('title', '')}: {a.get('snippet', '')[:150]}..." 
            for a in articles[:3]
        ])
        
        # Extract related past hypotheses
        past_hypotheses = "\n".join([
            f"- Query: {m.get('query', '')}\n  Hypothesis: {m.get('hypothesis', '')[:150]}..." 
            for m in past_memories[:2]
        ])
        
        # Create prompt for hypothesis generation
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Generation Agent, responsible for creating an initial hypothesis for a research query.
                
                Generate an insightful, well-structured hypothesis that:
                1. Directly addresses the research query
                2. Incorporates relevant insights from the web data provided
                3. Connects to past relevant research when appropriate
                4. Is specific and falsifiable
                5. Includes supporting reasoning
                
                Format your response as a clear hypothesis statement followed by 2-3 supporting points.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Research Query: {query}
                
                Web Data:
                {article_info}
                
                Past Related Research:
                {past_hypotheses}
                
                Generate a comprehensive initial hypothesis:"""
            )
        ])
        
        # Generate hypothesis using LLM
        chain = prompt | self.llm | StrOutputParser()
        hypothesis = await chain.ainvoke({
            "query": query,
            "article_info": article_info,
            "past_hypotheses": past_hypotheses
        })
        
        # Update agent memory
        self.memory.save_context(
            {"input": f"Query: {query}"}, 
            {"output": f"Hypothesis: {hypothesis[:100]}..."}
        )
        
        return {"hypothesis": hypothesis}


class ReflectionAgent(Agent):
    """
    Reflection Agent checks hypothesis coherence and validity
    
    This agent critically analyzes hypotheses by:
    - Evaluating logical consistency
    - Cross-checking against web data
    - Identifying potential flaws or gaps
    - Suggesting targeted improvements
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the coherence and validity of a hypothesis
        
        Args:
            input_data: Contains hypothesis and supporting data
            
        Returns:
            Dictionary with reflection analysis
        """
        hypothesis = input_data.get("hypothesis", "")
        web_data = input_data.get("web_data", {})
        query = input_data.get("query", "")
        
        # Extract articles for cross-checking
        articles = web_data.get("articles", [])
        article_info = "\n".join([
            f"- {a.get('title', '')}: {a.get('snippet', '')[:150]}..." 
            for a in articles[:3]
        ])
        
        # Create prompt for reflection
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Reflection Agent, responsible for critically evaluating hypotheses.
                
                Analyze the given hypothesis for:
                1. Logical coherence and consistency
                2. Alignment with available web data
                3. Potential contradictions or flaws
                4. Missing perspectives or considerations
                5. Relevance to the original query
                
                Your goal is to identify both strengths and weaknesses in the hypothesis.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Original Query: {query}
                
                Hypothesis to Evaluate: 
                {hypothesis}
                
                Web Data for Cross-checking:
                {article_info}
                
                Provide a structured evaluation with clear strengths and weaknesses:"""
            )
        ])
        
        # Generate reflection using LLM
        chain = prompt | self.llm | StrOutputParser()
        reflection = await chain.ainvoke({
            "query": query,
            "hypothesis": hypothesis,
            "article_info": article_info
        })
        
        # Update agent memory
        self.memory.save_context(
            {"input": f"Hypothesis: {hypothesis[:100]}..."}, 
            {"output": f"Reflection: {reflection[:100]}..."}
        )
        
        return {"reflection": reflection}


class RankingAgent(Agent):
    """
    Ranking Agent scores hypotheses based on multiple factors
    
    This agent evaluates hypotheses through:
    - Relevance to the original query
    - Support from web evidence
    - Logical consistency
    - Novelty and practical value
    - Alignment with past successful hypotheses
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a hypothesis on a scale of 0-10
        
        Args:
            input_data: Contains hypothesis and supporting data
            
        Returns:
            Dictionary with ranking score and explanation
        """
        hypothesis = input_data.get("hypothesis", "")
        web_data = input_data.get("web_data", {})
        query = input_data.get("query", "")
        reflection = input_data.get("reflection", "")
        
        # Extract articles for evidence
        articles = web_data.get("articles", [])
        article_info = "\n".join([
            f"- {a.get('title', '')}: {a.get('snippet', '')[:100]}..." 
            for a in articles[:3]
        ])
        
        # Create prompt for ranking
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Ranking Agent, responsible for scoring hypotheses.
                
                Score the given hypothesis from 0-10 based on:
                1. Relevance to the original query (0-2 points)
                2. Support from web evidence (0-2 points)
                3. Logical coherence and consistency (0-2 points)
                4. Novelty and insight (0-2 points)
                5. Practical value and applicability (0-2 points)
                
                First provide a single numerical score out of 10, then explain your reasoning
                with reference to the criteria above.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Original Query: {query}
                
                Hypothesis to Score: 
                {hypothesis}
                
                Web Evidence:
                {article_info}
                
                Reflection Analysis:
                {reflection}
                
                Provide a score (0-10) and detailed explanation:"""
            )
        ])
        
        # Generate ranking using LLM
        chain = prompt | self.llm | StrOutputParser()
        ranking_result = await chain.ainvoke({
            "query": query,
            "hypothesis": hypothesis,
            "article_info": article_info,
            "reflection": reflection
        })
        
        # Extract score from the result (first number in the response)
        score_match = re.search(r'\d+(?:\.\d+)?', ranking_result)
        score = float(score_match.group(0)) if score_match else 5.0  # default to 5.0 if no score found
        
        # Normalize score to 0-10 range if needed
        score = min(max(score, 0), 10)
        
        # Update agent memory
        self.memory.save_context(
            {"input": f"Hypothesis: {hypothesis[:100]}..."}, 
            {"output": f"Score: {score}/10"}
        )
        
        return {"ranking": ranking_result, "score": score}


class EvolutionAgent(Agent):
    """
    Evolution Agent refines hypotheses based on feedback
    
    This agent enhances hypotheses by:
    - Incorporating reflection feedback
    - Adding insights from web data
    - Addressing identified weaknesses
    - Maintaining strengths from the original
    - Learning from past refinements
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine a hypothesis based on feedback and web data
        
        Args:
            input_data: Contains hypothesis, reflection, ranking, and web data
            
        Returns:
            Dictionary with evolved hypothesis
        """
        hypothesis = input_data.get("hypothesis", "")
        web_data = input_data.get("web_data", {})
        query = input_data.get("query", "")
        reflection = input_data.get("reflection", "")
        ranking = input_data.get("ranking", "")
        score = input_data.get("score", 0)
        
        # Extract articles and trending topics
        articles = web_data.get("articles", [])
        trending = web_data.get("trending", [])
        
        web_insights = "\n".join([
            f"- {a.get('title', '')}: {a.get('snippet', '')[:100]}..." 
            for a in articles[:2]
        ])
        
        if trending:
            web_insights += "\n\nTrending Topics:\n" + "\n".join([f"- {t}" for t in trending])
        
        # Create prompt for evolution
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Evolution Agent, responsible for refining hypotheses.
                
                Enhance the given hypothesis by:
                1. Addressing weaknesses identified in the reflection
                2. Incorporating insights from web data and trends
                3. Maintaining the strengths of the original hypothesis
                4. Adding specificity and clarity
                5. Ensuring alignment with the original query
                
                The current hypothesis score is {score}/10. Your goal is to evolve it to achieve a higher score.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Original Query: {query}
                
                Current Hypothesis: 
                {hypothesis}
                
                Reflection Feedback:
                {reflection}
                
                Ranking Assessment:
                {ranking}
                
                Web Insights for Enhancement:
                {web_insights}
                
                Provide a refined, evolved hypothesis:"""
            )
        ])
        
        # Generate evolved hypothesis using LLM
        chain = prompt | self.llm | StrOutputParser()
        evolved_hypothesis = await chain.ainvoke({
            "query": query,
            "hypothesis": hypothesis,
            "reflection": reflection,
            "ranking": ranking,
            "score": score,
            "web_insights": web_insights
        })
        
        # Update agent memory
        self.memory.save_context(
            {"input": f"Original Hypothesis: {hypothesis[:100]}..."}, 
            {"output": f"Evolved: {evolved_hypothesis[:100]}..."}
        )
        
        return {"evolved_hypothesis": evolved_hypothesis}


class ProximityAgent(Agent):
    """
    Proximity Agent connects current research to past knowledge
    
    This agent enhances learning by:
    - Finding relevant past research
    - Identifying conceptual connections
    - Highlighting recurring patterns
    - Suggesting integrations of past insights
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find relevant past interactions and connections
        
        Args:
            input_data: Contains query, hypothesis, and memory store
            
        Returns:
            Dictionary with related memories and insights
        """
        query = input_data.get("query", "")
        hypothesis = input_data.get("hypothesis", "")
        memory_store = input_data.get("memory_store", [])
        
        if not memory_store:
            return {"related_memories": [], "connections": "No past research available for comparison."}
        
        # Format memory store for prompt
        formatted_memories = "\n\n".join([
            f"Memory {i+1}:\nQuery: {m.query}\nHypothesis: {m.hypothesis[:200]}...\nScore: {m.score}/10"
            for i, m in enumerate(memory_store[:5])  # Limit to recent 5 memories
        ])
        
        # Create prompt for proximity analysis
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Proximity Agent, responsible for connecting current research to past knowledge.
                
                Analyze the current query and hypothesis in relation to past research:
                1. Identify the most relevant past research items
                2. Highlight conceptual connections and patterns
                3. Extract useful insights from past research
                4. Suggest how past knowledge could enhance the current hypothesis
                
                Your goal is to provide learning continuity across research sessions.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Current Query: {query}
                
                Current Hypothesis: 
                {hypothesis}
                
                Past Research Memories:
                {formatted_memories}
                
                Provide connections to past research and insights:"""
            )
        ])
        
        # Generate proximity analysis using LLM
        chain = prompt | self.llm | StrOutputParser()
        connections = await chain.ainvoke({
            "query": query,
            "hypothesis": hypothesis,
            "formatted_memories": formatted_memories
        })
        
        # Find most similar past memories
        related_memories = []
        for memory in memory_store:
            # Simple word overlap similarity
            query_similarity = self._calculate_text_similarity(query, memory.query)
            hypothesis_similarity = self._calculate_text_similarity(hypothesis, memory.hypothesis)
            
            # Combine similarities with higher weight on query
            overall_similarity = (0.7 * query_similarity) + (0.3 * hypothesis_similarity)
            
            if overall_similarity > 0.2:  # Threshold for relevance
                related_memories.append({
                    "query": memory.query,
                    "hypothesis_snippet": memory.hypothesis[:200],
                    "score": memory.score,
                    "similarity": overall_similarity
                })
        
        # Sort by similarity and limit
        related_memories.sort(key=lambda x: x["similarity"], reverse=True)
        related_memories = related_memories[:3]  # Return top 3
        
        return {"related_memories": related_memories, "connections": connections}
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts based on word overlap
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
            
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
            
        # Jaccard similarity: intersection / union
        intersection = words1.intersection(words2)
        return len(intersection) / (len(words1) + len(words2) - len(intersection))


class MetaReviewAgent(Agent):
    """
    Meta-review Agent evaluates the research process itself
    
    This agent improves the system by:
    - Comparing initial and final hypotheses
    - Assessing the effectiveness of iterations
    - Identifying bottlenecks in the process
    - Suggesting process improvements
    - Learning from successful patterns
    """
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the research process and suggest improvements
        
        Args:
            input_data: Contains initial and final hypotheses, cycle data
            
        Returns:
            Dictionary with meta-review and recommendations
        """
        initial_hypothesis = input_data.get("initial_hypothesis", "")
        final_hypothesis = input_data.get("final_hypothesis", "")
        iterations = input_data.get("iterations", [])
        query = input_data.get("query", "")
        
        # Format iterations data
        iteration_summaries = []
        for i, iteration in enumerate(iterations):
            hypothesis = iteration.get("hypothesis", "") if i == 0 else iteration.get("evolved_hypothesis", "")
            score = iteration.get("score", 0)
            
            iteration_summaries.append(
                f"Iteration {i+1}:\n"
                f"Hypothesis: {hypothesis[:150]}...\n"
                f"Score: {score}/10"
            )
        
        formatted_iterations = "\n\n".join(iteration_summaries)
        
        # Create prompt for meta-review
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are the Meta-review Agent, responsible for evaluating the research process.
                
                Analyze the evolution of the research process:
                1. Compare initial and final hypotheses
                2. Evaluate the effectiveness of each iteration
                3. Identify strengths in the research approach
                4. Pinpoint areas for improvement
                5. Suggest specific enhancements for future research
                
                Your goal is to improve the system's research methodology.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """Original Query: {query}
                
                Initial Hypothesis: 
                {initial_hypothesis}
                
                Final Hypothesis:
                {final_hypothesis}
                
                Iteration History:
                {formatted_iterations}
                
                Provide a comprehensive meta-review and recommendations:"""
            )
        ])
        
        # Generate meta-review using LLM
        chain = prompt | self.llm | StrOutputParser()
        meta_review = await chain.ainvoke({
            "query": query,
            "initial_hypothesis": initial_hypothesis,
            "final_hypothesis": final_hypothesis,
            "formatted_iterations": formatted_iterations
        })
        
        # Extract specific recommendations using a focused prompt
        recommendation_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """Based on the meta-review, extract 3-5 specific, actionable recommendations 
                to improve the research process. Format as a bulleted list."""
            ),
            HumanMessagePromptTemplate.from_template(
                """Meta-review: {meta_review}
                
                List specific recommendations:"""
            )
        ])
        
        # Generate recommendations using LLM
        chain = recommendation_prompt | self.llm | StrOutputParser()
        recommendations = await chain.ainvoke({"meta_review": meta_review})
        
        return {
            "meta_review": meta_review,
            "recommendations": recommendations,
            "improvement_score": self._calculate_improvement(initial_hypothesis, final_hypothesis, iterations)
        }
    
    def _calculate_improvement(self, initial_hypothesis, final_hypothesis, iterations):
        """Calculate an improvement score based on iteration progress"""
        if not iterations:
            return 0
            
        # Get first and last scores
        initial_score = iterations[0].get("score", 0)
        final_score = iterations[-1].get("score", 0)
        
        # Calculate improvement percentage
        score_improvement = max(0, final_score - initial_score)
        
        # Scale to 0-10
        return min(score_improvement, 10)

class SupervisorAgent:
    """
    Supervisor Agent orchestrates the research process
    
    This agent manages the entire research workflow by:
    - Coordinating the specialized agents
    - Maintaining memory and research state
    - Allocating resources to agents
    - Creating feedback loops for iterative improvement
    - Storing and retrieving research history
    """
    def __init__(self):
        """Initialize the supervisor with specialized agents and memory"""
        # Initialize LLM
        self.llm = llm
        
        # Initialize specialized agents
        self.agents = {
            "generation": GenerationAgent("generation", self.llm),
            "reflection": ReflectionAgent("reflection", self.llm),
            "ranking": RankingAgent("ranking", self.llm),
            "evolution": EvolutionAgent("evolution", self.llm),
            "proximity": ProximityAgent("proximity", self.llm),
            "meta_review": MetaReviewAgent("meta_review", self.llm)
        }
        
        # Initialize web extractor
        self.web_extractor = WebExtractor()
        
        # Initialize memory stores
        self.memory_store = []  # Short-term memory for current session
        self.global_history = self._load_history()  # Long-term memory across sessions
        
        # Initialize session state
        self.reset_session()
    
    def reset_session(self):
        """Reset the current research session"""
        # Short-term conversation memory
        self.conversation_history = deque(maxlen=MAX_HISTORY)
        
        # Storage for ranked solutions in the current session
        self.ranked_solutions = []
        
        # Current topic and state information
        self.current_state = {}
        
        # Research iterations for the current query
        self.iterations = []
        
        # Final synthesis report
        self.final_report = None
        
        # Key concepts identified in this session
        self.session_key_concepts = set()
    
    def _load_history(self) -> List[HistoryItem]:
        """Load persistent research history from file"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    history_data = json.load(f)
                return [HistoryItem(**item) for item in history_data]
            except Exception as e:
                print(f"Error loading history: {str(e)}")
                return []
        return []
    
    def _save_history(self):
        """Save research history to persistent storage"""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump([asdict(item) for item in self.global_history], f, indent=2)
        except Exception as e:
            print(f"Error saving history: {str(e)}")
    
    def _add_to_history(self, query: str):
        """Add current research to history"""
        if not self.iterations:
            return
            
        # Extract top solutions (hypotheses with highest scores)
        top_solutions = []
        for iteration in self.iterations:
            if iteration.get('score', 0) > 0:
                hypothesis = iteration.get('hypothesis', '') if len(top_solutions) == 0 else iteration.get('evolved_hypothesis', '')
                top_solutions.append({
                    "hypothesis": hypothesis,
                    "score": iteration.get('score', 0)
                })
        
        # Sort solutions by score (highest first)
        top_solutions.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Extract key concepts from the top solutions
        key_concepts = self._extract_key_concepts()
        
        # Find related past queries based on concept overlap
        related_queries = self._find_related_queries(key_concepts)
        
        # Create and add history item
        history_item = HistoryItem(
            query=query,
            timestamp=datetime.now().isoformat(),
            top_solutions=top_solutions[:3],  # Store only top results
            key_concepts=list(key_concepts),
            related_queries=related_queries
        )
        
        self.global_history.append(history_item)
        if len(self.global_history) > MAX_HISTORY:
            self.global_history = self.global_history[-MAX_HISTORY:]
        self._save_history()
    
    def _extract_key_concepts(self) -> set:
        """Extract key concepts from the current research"""
        key_concepts = set()
        
        try:
            # Combine hypotheses for concept extraction
            all_text = ""
            for iteration in self.iterations:
                hypothesis = iteration.get('hypothesis', '')
                if hypothesis:
                    all_text += " " + hypothesis
                evolved = iteration.get('evolved_hypothesis', '')
                if evolved:
                    all_text += " " + evolved
            
            # Use LLM to extract key concepts
            extract_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    """Extract 5-10 key technical concepts from this text as a JSON list:
                        {text}

                        Format: ["concept1", "concept2", ...]"""
                )
            ])
            
            chain = extract_prompt | self.llm
            result = chain.invoke({"text": all_text}).content
            
            # Extract JSON list of concepts using regex
            matches = re.search(r'\[.*?\]', result, re.DOTALL)
            if matches:
                concepts = json.loads(matches.group(0))
                key_concepts.update(concepts)
        except Exception as e:
            print(f"Error extracting concepts: {str(e)}")
        
        return key_concepts
    
    def _find_related_queries(self, key_concepts: set) -> List[str]:
        """Find related past queries based on key concepts"""
        related = []
        
        for item in self.global_history:
            # Calculate concept overlap between current and past research
            overlap = len(set(item.key_concepts).intersection(key_concepts))
            if overlap > 0:
                related.append(item.query)
                
        return related[:3]  # Return top 3 related queries
    
    async def _find_relevant_past_memories(self, query: str) -> List[Dict]:
        """Find relevant memories from history for the current query"""
        relevant_memories = []
        
        for item in self.global_history:
            # Calculate text similarity between current query and past query
            similarity = self._calculate_text_similarity(query, item.query)
            if similarity > 0.3:  # Threshold for relevance
                for solution in item.top_solutions:
                    relevant_memories.append({
                        "query": item.query,
                        "hypothesis": solution.get("hypothesis", ""),
                        "score": solution.get("score", 0)
                    })
                
        # Sort by score and limit
        relevant_memories.sort(key=lambda x: x.get("score", 0), reverse=True)
        return relevant_memories[:3]  # Return top 3
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0
            
        # Jaccard similarity: intersection / union
        intersection = words1.intersection(words2)
        return len(intersection) / (len(words1) + len(words2) - len(intersection))
    
    async def process_query(self, query: str, cycles: int = DEFAULT_ITERATIONS) -> Dict[str, Any]:
        """
        Process a research query through multiple iteration cycles
        
        This is the main method that orchestrates the entire research flow
        
        Args:
            query: The research query to process
            cycles: Number of iteration cycles to run
            
        Returns:
            Dictionary with complete research results
        """
        # Reset session and set current query
        self.reset_session()
        self.current_state = {"query": query, "topic": query}
        
        try:
            # Iterate through multiple research cycles
            for cycle in range(cycles):
                print(f"\nCycle {cycle + 1}:")
                cycle_results = {"cycle": cycle + 1}
                
                # 1. Extract web data
                print("Extracting web data...")
                web_data = await self.web_extractor.extract(query)
                
                # 2. Find relevant past memories
                print("Finding relevant past experiences...")
                past_memories = await self._find_relevant_past_memories(query)
                
                # 3. Generation or Evolution
                if cycle == 0:
                    # First cycle: Generate initial hypothesis
                    print("Generating initial hypothesis...")
                    generation_result = await self.agents["generation"].process({
                        "query": query,
                        "web_data": web_data,
                        "past_memories": past_memories
                    })
                    hypothesis = generation_result["hypothesis"]
                    cycle_results["hypothesis"] = hypothesis
                else:
                    # Subsequent cycles: Evolve hypothesis
                    print("Evolving hypothesis...")
                    evolution_result = await self.agents["evolution"].process({
                        "query": query,
                        "hypothesis": self._get_last_hypothesis(),
                        "web_data": web_data,
                        "reflection": self.iterations[-1]["reflection"],
                        "ranking": self.iterations[-1]["ranking"],
                        "score": self.iterations[-1]["score"]
                    })
                    hypothesis = evolution_result["evolved_hypothesis"]
                    cycle_results["evolved_hypothesis"] = hypothesis
                
                # 4. Proximity analysis
                print("Analyzing connections to past research...")
                proximity_result = await self.agents["proximity"].process({
                    "query": query,
                    "hypothesis": hypothesis,
                    "memory_store": self.memory_store
                })
                cycle_results["related_memories"] = proximity_result["related_memories"]
                cycle_results["connections"] = proximity_result["connections"]
                
                # 5. Reflection
                print("Reflecting on hypothesis...")
                reflection_result = await self.agents["reflection"].process({
                    "query": query,
                    "hypothesis": hypothesis,
                    "web_data": web_data
                })
                cycle_results["reflection"] = reflection_result["reflection"]
                
                # 6. Ranking
                print("Ranking hypothesis...")
                ranking_result = await self.agents["ranking"].process({
                    "query": query,
                    "hypothesis": hypothesis,
                    "web_data": web_data,
                    "reflection": reflection_result["reflection"]
                })
                cycle_results["ranking"] = ranking_result["ranking"]
                cycle_results["score"] = ranking_result["score"]
                
                # Store cycle results
                self.iterations.append(cycle_results)
                
                # Store in memory for this session
                self.memory_store.append(ResearchMemory(
                    query=query,
                    hypothesis=hypothesis,
                    score=ranking_result["score"],
                    timestamp=datetime.now(),
                    web_data=web_data
                ))
                
                print(f"Cycle {cycle + 1} completed - Score: {ranking_result['score']}/10")
            
            # Final meta-review after all cycles
            print("\nPerforming meta-review...")
            meta_result = await self.agents["meta_review"].process({
                "query": query,
                "initial_hypothesis": self._get_hypothesis_from_iteration(0),
                "final_hypothesis": self._get_hypothesis_from_iteration(-1),
                "iterations": self.iterations
            })
            
            # Add to history
            self._add_to_history(query)
            
            # Return complete results
            return {
                "query": query,
                "cycles": self.iterations,
                "meta_review": meta_result["meta_review"],
                "recommendations": meta_result["recommendations"],
                "improvement_score": meta_result["improvement_score"]
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in process_query: {error_details}")
            return {"error": f"Processing failed: {str(e)}"}
    
    def _get_last_hypothesis(self) -> str:
        """Get the most recent hypothesis from iterations"""
        if not self.iterations:
            return ""
        
        last_iteration = self.iterations[-1]
        if "evolved_hypothesis" in last_iteration:
            return last_iteration["evolved_hypothesis"]
        elif "hypothesis" in last_iteration:
            return last_iteration["hypothesis"]
        return ""
    
    def _get_hypothesis_from_iteration(self, index: int) -> str:
        """Get hypothesis from a specific iteration index"""
        if not self.iterations or index >= len(self.iterations) or index < -len(self.iterations):
            return ""
        
        iteration = self.iterations[index]
        if index > 0 and "evolved_hypothesis" in iteration:
            return iteration["evolved_hypothesis"]
        elif "hypothesis" in iteration:
            return iteration["hypothesis"]
        return ""


# Display functions and main application
async def display_results(result: Dict[str, Any]):
    """Display research results in a readable format"""
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\n{'='*50}")
    print(f"RESEARCH QUERY: {result['query']}")
    print(f"{'='*50}")
    
    # Display each iteration cycle
    for i, cycle in enumerate(result["cycles"]):
        print(f"\n{'-'*50}")
        print(f"CYCLE {cycle['cycle']}:")
        print(f"{'-'*50}")
        
        # Display hypothesis
        if i == 0:
            print("\nINITIAL HYPOTHESIS:")
            print(f"{cycle.get('hypothesis', 'N/A')}")
        else:
            print("\nEVOLVED HYPOTHESIS:")
            print(f"{cycle.get('evolved_hypothesis', 'N/A')}")
        
        # Display reflection
        print("\nREFLECTION:")
        print(f"{cycle.get('reflection', 'N/A')[:300]}...")
        
        # Display ranking and score
        print(f"\nRANKING (Score: {cycle.get('score', 0)}/10):")
        print(f"{cycle.get('ranking', 'N/A')[:300]}...")
        
        # Display connections to past research
        if cycle.get('related_memories'):
            print("\nCONNECTIONS TO PAST RESEARCH:")
            for memory in cycle.get('related_memories', []):
                print(f"- Query: {memory.get('query', 'N/A')}")
                print(f"  Similarity: {memory.get('similarity', 0):.2f}")
                print(f"  Score: {memory.get('score', 0)}/10")
    
    # Display meta-review
    print(f"\n{'='*50}")
    print("META-REVIEW:")
    print(f"{'='*50}")
    print(result.get("meta_review", "N/A"))
    
    # Display recommendations
    print(f"\n{'-'*50}")
    print("RECOMMENDATIONS FOR IMPROVEMENT:")
    print(f"{'-'*50}")
    print(result.get("recommendations", "N/A"))
    
    # Display improvement score
    print(f"\nImprovement Score: {result.get('improvement_score', 0)}/10")
    print(f"{'='*50}")


async def main():
    """Main function to run the system"""
    # Initialize the supervisor agent
    supervisor = SupervisorAgent()
    
    print("Welcome to The Second Mind - Research Assistant")
    print("Type 'exit' to quit the program")
    
    while True:
        try:
            # Get query from user
            query = input("\nEnter your research query: ")
            if query.lower() in ["exit", "quit"]:
                break
                
            if not query:
                continue
            
            # Process the query
            result = await supervisor.process_query(query)
            
            # Display results
            await display_results(result)
            
            # Ask for next action
            next_action = input("\nEnter 'next' for a new query or 'exit' to quit: ")
            if next_action.lower() == "exit":
                break
                
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
