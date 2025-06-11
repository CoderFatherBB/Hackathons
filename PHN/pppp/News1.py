import feedparser
import logging
import random
from datetime import datetime

class AgricultureNewsScraper:
    def __init__(self, rss_url):
        self.rss_url = rss_url
        self.setup_logging()
        
    def setup_logging(self):
        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Create console handler and set format
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def format_date(self, date_str):
        try:
            # Parse the date string to datetime object
            # Example input: "Fri, 20 Dec 2024 14:30:00 +0530"
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            # Format the date with 12-hour time format without seconds
            return date_obj.strftime("%a, %d %b %Y %I:%M %p")
        except Exception:
            return date_str  # Return original string if parsing fails
        
    def is_agriculture_related(self, text):
        agriculture_keywords = [
            'farming', 'agriculture', 'crop', 'harvest', 'livestock',
            'farmer', 'agricultural', 'soil', 'irrigation', 'pesticide',
            'organic farming', 'sustainable agriculture', 'farm'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in agriculture_keywords)
        
    def fetch_news(self):
        try:
            feed = feedparser.parse(self.rss_url)
            if feed.bozo:
                self.logger.error(f"Error parsing RSS feed: {feed.bozo_exception}")
                return []
                
            agriculture_news = []
            for entry in feed.entries:
                title = entry.get('title', '')
                description = entry.get('description', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                if self.is_agriculture_related(title) or self.is_agriculture_related(description):
                    news_item = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'published_date': self.format_date(published)  # Format the date
                    }
                    agriculture_news.append(news_item)
            
            # Shuffle the news items to get random news each time
            random.shuffle(agriculture_news)
            
            # Log with formatted date and day
            current_time = datetime.now().strftime('%A, %d %B %Y')
            self.logger.info(f"Top 20 agriculture-related news at {current_time}")
            
            # Return top 20 news items
            return agriculture_news[:20]
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {str(e)}")
            return []

def get_news():
    rss_urls = [
        "https://www.thehindubusinessline.com/economy/agri-business/feeder/default.rss",
        "https://timesofindia.indiatimes.com/rssfeeds/1221656.cms",
        "http://feeds.feedburner.com/NDTV-LatestNews"
    ]
    all_news = []
    for url in rss_urls:
        scraper = AgricultureNewsScraper(url)
        news_items = scraper.fetch_news()
        all_news.extend(news_items)
    return all_news


class AgricultureNewsScraperSearcher():
    def __init__(self, rss_url):
        self.rss_url = rss_url
        self.setup_logging()
        
    def setup_logging(self):
        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Create console handler and set format
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def format_date(self, date_str):
        try:
            # Parse the date string to datetime object
            # Example input: "Fri, 20 Dec 2024 14:30:00 +0530"
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            # Format the date with 12-hour time format without seconds
            return date_obj.strftime("%a, %d %b %Y %I:%M %p")
        except Exception:
            return date_str  # Return original string if parsing fails


    def is_agriculture_related(self, text,  search_query):
        agriculture_keywords = [
            search_query
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in agriculture_keywords)
        
    def fetch_news(self, search_query=None):
        try:
            feed = feedparser.parse(self.rss_url)
            if feed.bozo:
                self.logger.error(f"Error parsing RSS feed: {feed.bozo_exception}")
                return []
                   
            agriculture_news = []
            for entry in feed.entries:
                title = entry.get('title', '')
                description = entry.get('description', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                

                if self.is_agriculture_related(title, search_query) or self.is_agriculture_related(description, search_query):
                    news_item = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'published_date': self.format_date(published)  # Format the date
                    }
                    agriculture_news.append(news_item)
            
            # Shuffle the news items to get random news each time
            random.shuffle(agriculture_news)
            
            # Log with formatted date and day
            current_time = datetime.now().strftime('%A, %d %B %Y')
            self.logger.info(f"Top 20 agriculture-related news at {current_time}")
            
            # Return top 20 news items
            return agriculture_news[:20]
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {str(e)}")
            return []