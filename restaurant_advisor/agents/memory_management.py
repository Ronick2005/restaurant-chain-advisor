"""
Advanced memory management for agents with short-term, long-term, and session-specific memory.
"""

from typing import Dict, List, Any, Optional
import json
import time
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

class Memory:
    """Base class for memory systems."""
    
    def __init__(self):
        self.data = {}
    
    def add(self, key: str, value: Any) -> None:
        """Add data to memory."""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get data from memory."""
        return self.data.get(key, default)
    
    def clear(self) -> None:
        """Clear memory."""
        self.data = {}


class ShortTermMemory(Memory):
    """Short-term memory for recent interactions."""
    
    def __init__(self, max_size: int = 10):
        super().__init__()
        self.max_size = max_size
        self.messages = []
        self.timestamp = time.time()
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to short-term memory."""
        self.messages.append(message)
        
        # Trim if exceeding max size
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]
            
        # Update timestamp
        self.timestamp = time.time()
    
    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in short-term memory."""
        return self.messages.copy()
    
    def clear(self) -> None:
        """Clear short-term memory."""
        self.messages = []


class LongTermMemory(Memory):
    """Long-term memory for persistent knowledge."""
    
    def __init__(self):
        super().__init__()
        self.facts = []
        self.preferences = {}
        self.last_queries = []
        self.insights = {}
    
    def add_fact(self, fact: str) -> None:
        """Add a fact to long-term memory."""
        if fact not in self.facts:
            self.facts.append(fact)
    
    def add_preference(self, key: str, value: str) -> None:
        """Add a user preference to long-term memory."""
        self.preferences[key] = value
    
    def add_query(self, query: str) -> None:
        """Add a user query to long-term memory."""
        self.last_queries.append(query)
        
        # Keep only last 20 queries
        if len(self.last_queries) > 20:
            self.last_queries = self.last_queries[-20:]
    
    def add_insight(self, key: str, insight: Any) -> None:
        """Add an insight to long-term memory."""
        self.insights[key] = insight
    
    def get_facts(self) -> List[str]:
        """Get all facts from long-term memory."""
        return self.facts.copy()
    
    def get_preferences(self) -> Dict[str, str]:
        """Get all user preferences from long-term memory."""
        return self.preferences.copy()
    
    def get_last_queries(self, n: int = 5) -> List[str]:
        """Get the last n queries from long-term memory."""
        return self.last_queries[-n:] if self.last_queries else []
    
    def get_insights(self) -> Dict[str, Any]:
        """Get all insights from long-term memory."""
        return self.insights.copy()
    
    def get_relevant_memories(self, query: str, max_items: int = 5) -> Dict[str, Any]:
        """Get relevant memories based on the query."""
        # This is a simple implementation that could be improved with embeddings
        query_lower = query.lower()
        relevant = {
            "facts": [],
            "preferences": {},
            "insights": {}
        }
        
        # Get relevant facts
        for fact in self.facts:
            if any(word in fact.lower() for word in query_lower.split()):
                relevant["facts"].append(fact)
                if len(relevant["facts"]) >= max_items:
                    break
        
        # Get relevant preferences
        for key, value in self.preferences.items():
            if key.lower() in query_lower:
                relevant["preferences"][key] = value
                if len(relevant["preferences"]) >= max_items:
                    break
        
        # Get relevant insights
        for key, insight in self.insights.items():
            if key.lower() in query_lower:
                relevant["insights"][key] = insight
                if len(relevant["insights"]) >= max_items:
                    break
        
        return relevant


class UserMemory:
    """Memory manager for individual users."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.session_data = {}
        self.last_activity = time.time()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to short-term memory."""
        self.short_term.add_message(message)
        self.update_activity()
        
        # If it's a human message, also add to long-term queries
        if isinstance(message, HumanMessage):
            self.long_term.add_query(message.content)
    
    def get_conversation_context(self, max_messages: int = 10) -> List[BaseMessage]:
        """Get conversation context from short-term memory."""
        return self.short_term.get_messages()[-max_messages:]
    
    def extract_preferences(self, message: HumanMessage) -> None:
        """Extract user preferences from a message and store in long-term memory."""
        content = message.content.lower()
        
        # Extract cuisine preferences
        cuisine_keywords = {
            "italian": "Italian",
            "chinese": "Chinese",
            "indian": "Indian",
            "mexican": "Mexican",
            "thai": "Thai",
            "japanese": "Japanese",
            "french": "French",
            "mediterranean": "Mediterranean",
            "american": "American",
            "middle eastern": "Middle Eastern",
            "south indian": "South Indian",
            "north indian": "North Indian",
            "punjabi": "Punjabi",
            "bengali": "Bengali",
            "gujarati": "Gujarati"
        }
        
        for keyword, cuisine in cuisine_keywords.items():
            if keyword in content:
                self.long_term.add_preference("cuisine", cuisine)
        
        # Extract city preferences
        city_keywords = {
            "mumbai": "Mumbai",
            "delhi": "Delhi",
            "bangalore": "Bangalore",
            "chennai": "Chennai",
            "hyderabad": "Hyderabad",
            "kolkata": "Kolkata",
            "pune": "Pune",
            "ahmedabad": "Ahmedabad",
            "jaipur": "Jaipur",
            "lucknow": "Lucknow"
        }
        
        for keyword, city in city_keywords.items():
            if keyword in content:
                self.long_term.add_preference("city", city)
        
        # Extract budget preferences
        budget_phrases = {
            "low budget": "Low",
            "budget friendly": "Low",
            "affordable": "Low",
            "mid budget": "Medium",
            "medium budget": "Medium",
            "moderate": "Medium",
            "high budget": "High",
            "luxury": "High",
            "premium": "High",
            "expensive": "High"
        }
        
        for phrase, budget in budget_phrases.items():
            if phrase in content:
                self.long_term.add_preference("budget", budget)
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session-specific data."""
        return self.session_data.get(key, default)
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Set session-specific data."""
        self.session_data[key] = value
        self.update_activity()
    
    def clear_session_data(self) -> None:
        """Clear session-specific data."""
        self.session_data = {}
        self.update_activity()
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get comprehensive user context from all memory types."""
        # Get relevant long-term memories
        if self.short_term.messages:
            latest_query = self.short_term.messages[-1].content if isinstance(self.short_term.messages[-1], HumanMessage) else ""
        else:
            latest_query = ""
        
        relevant_memories = self.long_term.get_relevant_memories(latest_query) if latest_query else {}
        
        # Compile context
        context = {
            "preferences": self.long_term.get_preferences(),
            "recent_queries": self.long_term.get_last_queries(3),
            "facts": relevant_memories.get("facts", []),
            "insights": relevant_memories.get("insights", {}),
            "session": self.session_data
        }
        
        return context


class MemoryManager:
    """Manages memory for all users in the system."""
    
    def __init__(self, session_timeout: int = 3600):
        """Initialize memory manager.
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.users = {}  # User ID -> UserMemory
        self.session_timeout = session_timeout
    
    def get_user_memory(self, user_id: str) -> UserMemory:
        """Get memory for a specific user."""
        if user_id not in self.users:
            self.users[user_id] = UserMemory(user_id)
        
        # Update activity timestamp
        self.users[user_id].update_activity()
        return self.users[user_id]
    
    def process_message(self, user_id: str, message: BaseMessage) -> None:
        """Process a message for a user, extracting preferences and updating memory."""
        user_memory = self.get_user_memory(user_id)
        
        # Add message to short-term memory
        user_memory.add_message(message)
        
        # Extract preferences if it's a human message
        if isinstance(message, HumanMessage):
            user_memory.extract_preferences(message)
    
    def cleanup_inactive_sessions(self) -> None:
        """Clean up inactive user sessions based on timeout."""
        current_time = time.time()
        inactive_users = []
        
        for user_id, user_memory in self.users.items():
            if current_time - user_memory.last_activity > self.session_timeout:
                inactive_users.append(user_id)
        
        # Remove inactive users
        for user_id in inactive_users:
            del self.users[user_id]
    
    def save_to_disk(self, file_path: str) -> None:
        """Save memory to disk."""
        data = {}
        
        for user_id, user_memory in self.users.items():
            # Convert message objects to serializable format
            messages = []
            for msg in user_memory.short_term.get_messages():
                msg_type = type(msg).__name__
                messages.append({
                    "type": msg_type,
                    "content": msg.content
                })
            
            # Prepare user data
            user_data = {
                "short_term": {
                    "messages": messages,
                    "timestamp": user_memory.short_term.timestamp
                },
                "long_term": {
                    "facts": user_memory.long_term.facts,
                    "preferences": user_memory.long_term.preferences,
                    "last_queries": user_memory.long_term.last_queries,
                    "insights": user_memory.long_term.insights
                },
                "session_data": user_memory.session_data,
                "last_activity": user_memory.last_activity
            }
            
            data[user_id] = user_data
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_from_disk(self, file_path: str) -> None:
        """Load memory from disk."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            for user_id, user_data in data.items():
                # Create user memory
                user_memory = UserMemory(user_id)
                
                # Restore short-term memory
                short_term_data = user_data.get("short_term", {})
                messages_data = short_term_data.get("messages", [])
                
                for msg_data in messages_data:
                    msg_type = msg_data.get("type", "")
                    content = msg_data.get("content", "")
                    
                    # Create message object based on type
                    if msg_type == "HumanMessage":
                        msg = HumanMessage(content=content)
                    elif msg_type == "AIMessage":
                        msg = AIMessage(content=content)
                    elif msg_type == "SystemMessage":
                        msg = SystemMessage(content=content)
                    else:
                        continue
                    
                    user_memory.short_term.add_message(msg)
                
                user_memory.short_term.timestamp = short_term_data.get("timestamp", time.time())
                
                # Restore long-term memory
                long_term_data = user_data.get("long_term", {})
                user_memory.long_term.facts = long_term_data.get("facts", [])
                user_memory.long_term.preferences = long_term_data.get("preferences", {})
                user_memory.long_term.last_queries = long_term_data.get("last_queries", [])
                user_memory.long_term.insights = long_term_data.get("insights", {})
                
                # Restore session data and activity timestamp
                user_memory.session_data = user_data.get("session_data", {})
                user_memory.last_activity = user_data.get("last_activity", time.time())
                
                # Add to users
                self.users[user_id] = user_memory
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading memory from disk: {str(e)}")
