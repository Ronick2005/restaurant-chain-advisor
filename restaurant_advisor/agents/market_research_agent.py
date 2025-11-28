"""
Market Research Agent
Scrapes and analyzes Indian F&B industry reports, trends, and market data.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymongo import MongoClient
from utils.config import GEMINI_API_KEY, MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

class MarketResearchAgent:
    """
    Agent for gathering and analyzing market research data on Indian F&B industry.
    Scrapes news, reports, and market trends from various sources.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        
        # MongoDB connection for storing scraped data
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client[MONGODB_DB_NAME]
        self.collection = self.db["market_research"]
        
        # Embeddings for semantic search
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GEMINI_API_KEY
        )
        
        # Data sources for Indian F&B industry
        self.sources = {
            "news": [
                "https://economictimes.indiatimes.com/industry/services/hotels-/-restaurants",
                "https://www.business-standard.com/industry/news/food-beverages",
                "https://www.livemint.com/industry/retail"
            ],
            "reports": [
                "https://www.ibef.org/industry/indian-food-industry",
                "https://www.investindia.gov.in/sector/food-processing"
            ]
        }
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    def scrape_industry_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape latest F&B industry news from Indian sources.
        
        Args:
            limit: Maximum number of articles to scrape
            
        Returns:
            List of news articles with title, content, url, date
        """
        logger.info(f"Scraping F&B industry news (limit: {limit})")
        articles = []
        
        try:
            # Example scraping logic (can be extended based on actual website structure)
            for url in self.sources["news"][:2]:  # Limit sources to avoid rate limiting
                try:
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Store page metadata
                        article = {
                            "title": soup.title.string if soup.title else "Industry News",
                            "url": url,
                            "content_preview": soup.get_text()[:500],  # First 500 chars
                            "scraped_at": datetime.now().isoformat(),
                            "source": url.split('/')[2],
                            "category": "industry_news"
                        }
                        articles.append(article)
                        
                        if len(articles) >= limit:
                            break
                            
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
            # Store in MongoDB
            if articles:
                self.collection.insert_many(articles)
                logger.info(f"Stored {len(articles)} articles in MongoDB")
                
        except Exception as e:
            logger.error(f"Error in scrape_industry_news: {e}")
        
        return articles
    
    def scrape_market_reports(self) -> List[Dict[str, Any]]:
        """
        Scrape market research reports on Indian F&B industry.
        
        Returns:
            List of report summaries with key insights
        """
        logger.info("Scraping market research reports")
        reports = []
        
        try:
            for url in self.sources["reports"]:
                try:
                    loader = WebBaseLoader(url)
                    documents = loader.load()
                    
                    # Split into chunks for embedding
                    chunks = self.text_splitter.split_documents(documents)
                    
                    # Create embeddings for semantic search
                    for chunk in chunks[:5]:  # Limit chunks per report
                        embedding = self.embeddings.embed_query(chunk.page_content)
                        
                        report = {
                            "title": f"Market Report - {url.split('/')[-1]}",
                            "url": url,
                            "content": chunk.page_content,
                            "embedding": embedding,
                            "scraped_at": datetime.now().isoformat(),
                            "category": "market_report",
                            "metadata": chunk.metadata
                        }
                        reports.append(report)
                    
                except Exception as e:
                    logger.error(f"Error scraping report {url}: {e}")
                    continue
            
            # Store in MongoDB
            if reports:
                self.collection.insert_many(reports)
                logger.info(f"Stored {len(reports)} report chunks in MongoDB")
                
        except Exception as e:
            logger.error(f"Error in scrape_market_reports: {e}")
        
        return reports
    
    def analyze_market_trends(self, location: str, query: str) -> Dict[str, Any]:
        """
        Analyze market trends for a specific location using LLM.
        
        Args:
            location: City or region to analyze
            query: Specific market research query
            
        Returns:
            Analysis results with trends, opportunities, threats
        """
        logger.info(f"Analyzing market trends for {location}: {query}")
        
        # Retrieve relevant documents from MongoDB
        relevant_docs = self.collection.find({
            "$or": [
                {"category": "industry_news"},
                {"category": "market_report"}
            ]
        }).sort("scraped_at", -1).limit(10)
        
        # Prepare context from documents
        context = "\n\n".join([
            f"Source: {doc['url']}\n{doc.get('content_preview', doc.get('content', ''))[:300]}"
            for doc in relevant_docs
        ])
        
        # Use LLM to analyze
        system_prompt = f"""You are a market research analyst specializing in the Indian food and beverage industry.
Analyze the following market data and provide insights for {location}.

Focus on:
1. Current market trends and growth opportunities
2. Consumer preferences and dining habits
3. Competition landscape
4. Emerging food concepts and cuisines
5. Market challenges and risks

Be specific to Indian market dynamics and regional preferences."""

        user_prompt = f"""Query: {query}

Available Market Data:
{context}

Provide a comprehensive market research analysis with:
- Key Findings (3-5 points)
- Market Opportunities
- Potential Challenges
- Recommendations for restaurant chain expansion"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "location": location,
                "query": query,
                "analysis": response.content,
                "sources_used": [doc["url"] for doc in relevant_docs],
                "analyzed_at": datetime.now().isoformat(),
                "agent": "market_research"
            }
            
            # Store analysis
            self.db["market_analysis"].insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_market_trends: {e}")
            return {
                "location": location,
                "query": query,
                "analysis": f"Error analyzing market trends: {str(e)}",
                "error": True
            }
    
    def get_industry_statistics(self) -> Dict[str, Any]:
        """
        Get key statistics about Indian F&B industry.
        
        Returns:
            Dictionary with market size, growth rate, segments, etc.
        """
        # This would ideally scrape from government/industry sources
        # For now, returning structured data that can be updated periodically
        stats = {
            "market_size_usd_billion": 60,
            "projected_growth_rate_percent": 11.5,
            "key_segments": [
                "Quick Service Restaurants (QSR)",
                "Fine Dining",
                "Cloud Kitchens",
                "Casual Dining",
                "Cafes and Bakeries"
            ],
            "top_cuisines": [
                "North Indian",
                "South Indian", 
                "Chinese",
                "Continental",
                "Italian",
                "Fast Food"
            ],
            "market_leaders": [
                "Jubilant FoodWorks (Dominos, Dunkin)",
                "Westlife Development (McDonald's)",
                "Devyani International (KFC, Pizza Hut)",
                "Barbeque Nation",
                "Zomato/Swiggy (delivery platforms)"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.db["industry_stats"].replace_one(
            {"type": "indian_fnb_industry"},
            {**stats, "type": "indian_fnb_industry"},
            upsert=True
        )
        
        return stats
    
    def refresh_data(self) -> Dict[str, Any]:
        """
        Refresh all market research data (news, reports, statistics).
        
        Returns:
            Summary of data refresh operation
        """
        logger.info("Refreshing market research data")
        
        results = {
            "news_articles": 0,
            "market_reports": 0,
            "statistics_updated": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Scrape news
            articles = self.scrape_industry_news(limit=15)
            results["news_articles"] = len(articles)
            
            # Scrape reports
            reports = self.scrape_market_reports()
            results["market_reports"] = len(reports)
            
            # Update statistics
            self.get_industry_statistics()
            results["statistics_updated"] = True
            
            logger.info(f"Data refresh completed: {results}")
            
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            results["error"] = str(e)
        
        return results
    
    def search_insights(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search market research insights using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant insights
        """
        try:
            # Create query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in MongoDB (if using vector search)
            # For now, doing text search
            results = self.collection.find({
                "$text": {"$search": query}
            }).limit(limit)
            
            insights = []
            for doc in results:
                doc.pop("_id", None)
                doc.pop("embedding", None)  # Remove embedding from response
                insights.append(doc)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error searching insights: {e}")
            return []
