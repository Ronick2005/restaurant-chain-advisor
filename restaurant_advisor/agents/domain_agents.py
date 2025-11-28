"""
Domain-specialized agents for different aspects of restaurant advisory system.
These agents provide domain expertise for specific use cases and queries.
"""

from typing import Dict, List, Any, Optional, Tuple, Literal
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from agents.agent_definitions import BaseAgent

class DomainSpecialist:
    """Base class for domain specialists."""
    
    def __init__(self):
        self.domain = "general"
        self.description = "General domain specialist"
        self.capabilities = []
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        return False
    
    def get_context_requirements(self) -> List[str]:
        """Get the context requirements for this specialist."""
        return ["kb_context", "kg_insights"]


class CuisineSpecialist(DomainSpecialist):
    """Specialist for cuisine-related queries and recommendations."""
    
    def __init__(self):
        super().__init__()
        self.domain = "cuisine"
        self.description = "Cuisine specialist with expertise in food trends, menu design, and cuisine adaptation"
        self.capabilities = [
            "Food trend analysis",
            "Menu recommendations",
            "Cuisine localization strategies",
            "Menu pricing optimization",
            "Dietary restriction accommodation"
        ]
        
        self.prompt_template = """You are a cuisine specialist advising restaurant entrepreneurs in India.
        
        User query: {query}
        City: {city}
        Cuisine: {cuisine}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert advice on cuisine strategy. Include:
        1. Current trends for this cuisine in {city}
        2. Menu recommendations and adaptation suggestions for local tastes
        3. Pricing strategy recommendations
        4. Key ingredients and supply chain considerations
        5. Potential fusion opportunities with local flavors
        
        Your response should be detailed, practical, and specific to the Indian market context.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        cuisine_related_terms = [
            "cuisine", "food", "menu", "dish", "taste", "flavor", "recipe", 
            "ingredient", "culinary", "chef", "cooking", "food trend"
        ]
        
        # Check if query has cuisine-related terms
        has_cuisine_terms = any(term in query_lower for term in cuisine_related_terms)
        
        # Check if parameters include cuisine
        has_cuisine_param = "cuisine" in parameters and parameters["cuisine"]
        
        return has_cuisine_terms or has_cuisine_param


class FinancialAdvisorSpecialist(DomainSpecialist):
    """Specialist for restaurant financial planning and analysis."""
    
    def __init__(self):
        super().__init__()
        self.domain = "financial"
        self.description = "Financial advisor with expertise in restaurant economics, investment planning, and ROI analysis"
        self.capabilities = [
            "Initial investment planning",
            "Operating cost estimation",
            "Break-even analysis",
            "Revenue projection",
            "Financial risk assessment",
            "Funding options"
        ]
        
        self.prompt_template = """You are a financial advisor specializing in restaurant economics in India.
        
        User query: {query}
        City: {city}
        Restaurant type: {restaurant_type}
        Scale: {scale}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert financial advice for this restaurant venture. Include:
        1. Initial investment estimate breakdown for {city}
        2. Monthly operating cost projections
        3. Break-even analysis and timeline
        4. Revenue projections for first 12 months
        5. Key financial risks and mitigation strategies
        6. Potential funding sources relevant to Indian market
        
        Your response should be data-driven, practical, and specific to the restaurant industry in India.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        finance_related_terms = [
            "finance", "cost", "budget", "investment", "revenue", "profit", 
            "break-even", "funding", "loan", "capital", "roi", "return", 
            "expense", "financial", "money", "cash flow", "pricing"
        ]
        
        # Check if query has finance-related terms
        return any(term in query_lower for term in finance_related_terms)


class StaffingHRSpecialist(DomainSpecialist):
    """Specialist for restaurant staffing, HR policies, and team management."""
    
    def __init__(self):
        super().__init__()
        self.domain = "staffing"
        self.description = "Staffing and HR specialist with expertise in restaurant personnel management"
        self.capabilities = [
            "Staff structure planning",
            "Hiring best practices",
            "Training program development",
            "Compensation benchmarks",
            "Labor law compliance",
            "Team management strategies"
        ]
        
        self.prompt_template = """You are a staffing and HR specialist for restaurants in India.
        
        User query: {query}
        City: {city}
        Restaurant type: {restaurant_type}
        Scale: {scale}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert staffing and HR advice for this restaurant. Include:
        1. Recommended staff structure and roles for this restaurant type
        2. Hiring strategy and sources for talent acquisition in {city}
        3. Compensation benchmarks specific to {city} restaurant industry
        4. Key labor regulations to be aware of in this context
        5. Training and retention best practices for Indian restaurant staff
        6. Performance management recommendations
        
        Your response should be practical, compliant with Indian labor laws, and specific to the restaurant industry.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        staffing_related_terms = [
            "staff", "employee", "hiring", "training", "workforce", "team", 
            "chef", "waiter", "manager", "hr", "human resources", "personnel",
            "labor", "recruitment", "interview", "salary", "wage", "compensation"
        ]
        
        # Check if query has staffing-related terms
        return any(term in query_lower for term in staffing_related_terms)


class MarketingBrandingSpecialist(DomainSpecialist):
    """Specialist for restaurant marketing, branding, and customer acquisition."""
    
    def __init__(self):
        super().__init__()
        self.domain = "marketing"
        self.description = "Marketing specialist with expertise in restaurant branding, promotion, and customer acquisition"
        self.capabilities = [
            "Brand strategy development",
            "Digital marketing planning",
            "Customer acquisition tactics",
            "Social media strategy",
            "Local marketing approaches",
            "Customer loyalty programs"
        ]
        
        self.prompt_template = """You are a marketing and branding specialist for restaurants in India.
        
        User query: {query}
        City: {city}
        Restaurant type: {restaurant_type}
        Target demographic: {demographic}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert marketing and branding advice for this restaurant. Include:
        1. Brand positioning recommendations for this restaurant concept in {city}
        2. Digital marketing strategies most effective for restaurants in India
        3. Customer acquisition costs and tactics for the target demographic
        4. Social media platform recommendations and content strategy
        5. Local marketing approaches specific to {city}
        6. Customer loyalty and retention programs that work well in Indian markets
        
        Your response should be practical, data-driven, and specifically tailored to restaurant marketing in India.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        marketing_related_terms = [
            "marketing", "promotion", "advertis", "brand", "customer", "acquisition", 
            "social media", "publicity", "influencer", "campaign", "digital marketing",
            "seo", "website", "online presence", "customer acquisition", "promotion"
        ]
        
        # Check if query has marketing-related terms
        return any(term in query_lower for term in marketing_related_terms)


class TechnologySystemsSpecialist(DomainSpecialist):
    """Specialist for restaurant technology, systems integration, and digital operations."""
    
    def __init__(self):
        super().__init__()
        self.domain = "technology"
        self.description = "Technology specialist with expertise in restaurant systems, POS, and digital operations"
        self.capabilities = [
            "POS system selection",
            "Inventory management systems",
            "Online ordering integration",
            "Kitchen display systems",
            "Table management software",
            "Customer data platforms",
            "Cybersecurity for restaurants"
        ]
        
        self.prompt_template = """You are a technology and systems specialist for restaurants in India.
        
        User query: {query}
        Restaurant type: {restaurant_type}
        Scale: {scale}
        Budget: {budget}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert technology and systems advice for this restaurant. Include:
        1. Recommended POS systems available in India with pricing estimates
        2. Digital operations stack tailored to this restaurant type
        3. Online ordering and delivery integration options
        4. Inventory management system recommendations
        5. Customer data management solutions
        6. Technology implementation timeline and strategy
        7. Technology budget allocation recommendations
        
        Your response should be practical, cost-effective, and specific to the Indian restaurant technology landscape.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        tech_related_terms = [
            "technology", "system", "software", "hardware", "pos", "point of sale", 
            "inventory", "digital", "online", "app", "mobile", "payment", "website",
            "reservation", "cybersecurity", "data", "cloud", "integration"
        ]
        
        # Check if query has tech-related terms
        return any(term in query_lower for term in tech_related_terms)


class DesignInteriorSpecialist(DomainSpecialist):
    """Specialist for restaurant design, interior, and ambiance planning."""
    
    def __init__(self):
        super().__init__()
        self.domain = "design"
        self.description = "Design specialist with expertise in restaurant interiors, space planning, and ambiance"
        self.capabilities = [
            "Interior design concept development",
            "Space planning and layout optimization",
            "Ambiance and atmosphere creation",
            "Lighting and acoustics planning",
            "Furniture and fixture selection",
            "Brand-aligned design elements"
        ]
        
        self.prompt_template = """You are a design and interior specialist for restaurants in India.
        
        User query: {query}
        Restaurant type: {restaurant_type}
        Cuisine: {cuisine}
        Target demographic: {demographic}
        
        Knowledge base insights:
        {kb_context}
        
        Knowledge graph data:
        {kg_insights}
        
        Based on the above information, provide expert design and interior advice for this restaurant. Include:
        1. Design concept recommendations aligned with the restaurant's cuisine and brand
        2. Space planning and layout optimization strategies
        3. Ambiance elements that will appeal to the target demographic
        4. Lighting and acoustics recommendations
        5. Furniture, fixture, and equipment suggestions with estimated costs
        6. Design trends relevant to this restaurant concept in India
        7. Implementation timeline and phasing suggestions
        
        Your response should be practical, visually descriptive, and aligned with Indian design sensibilities and preferences.
        """
    
    def can_handle_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """Check if this specialist can handle the query."""
        query_lower = query.lower()
        design_related_terms = [
            "design", "interior", "decor", "ambiance", "atmosphere", "space", "layout", 
            "lighting", "furniture", "fixture", "seating", "aesthetic", "look",
            "feel", "ambience", "style", "theme", "decoration"
        ]
        
        # Check if query has design-related terms
        return any(term in query_lower for term in design_related_terms)


class DomainSpecialistAgent(BaseAgent):
    """Agent that specializes in domain-specific restaurant advisory."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        
        # Initialize all domain specialists
        self.specialists = [
            CuisineSpecialist(),
            FinancialAdvisorSpecialist(),
            StaffingHRSpecialist(),
            MarketingBrandingSpecialist(),
            TechnologySystemsSpecialist(),
            DesignInteriorSpecialist()
        ]
        
        # Fallback prompt for when no specialist matches
        self.fallback_prompt = PromptTemplate(
            template="""You are a restaurant advisory specialist helping entrepreneurs in India.
            
            User query: {query}
            
            Knowledge base insights:
            {kb_context}
            
            Knowledge graph data:
            {kg_insights}
            
            Please provide a helpful response to this query about the restaurant business in India.
            Focus on being practical, specific, and data-driven in your advice.
            """,
            input_variables=["query", "kb_context", "kg_insights"]
        )
    
    def get_specialist_for_query(self, query: str, parameters: Dict[str, Any]) -> Optional[DomainSpecialist]:
        """Get the appropriate specialist for a given query."""
        for specialist in self.specialists:
            if specialist.can_handle_query(query, parameters):
                return specialist
        return None
    
    def run(self, query: str, parameters: Dict[str, Any], kb_context: str, kg_insights: str) -> str:
        """Run the domain specialist agent with the most appropriate specialist."""
        specialist = self.get_specialist_for_query(query, parameters)
        
        if specialist:
            # Use the specialist's prompt template
            prompt = PromptTemplate(
                template=specialist.prompt_template,
                input_variables=["query", "city", "restaurant_type", "cuisine", "scale", "demographic", "budget", "kb_context", "kg_insights"]
            )
            
            # Fill in the specialist's prompt with available parameters
            prompt_params = {
                "query": query,
                "city": parameters.get("city", ""),
                "restaurant_type": parameters.get("restaurant_type", ""),
                "cuisine": parameters.get("cuisine", ""),
                "scale": parameters.get("scale", ""),
                "demographic": parameters.get("demographic", ""),
                "budget": parameters.get("budget", ""),
                "kb_context": kb_context,
                "kg_insights": kg_insights
            }
            
            prompt_value = prompt.format(**prompt_params)
            
            # Add specialist information to the response
            response_prefix = f"[{specialist.domain.upper()} SPECIALIST RESPONSE]\n\n"
            
            # Get the response from the model
            model_response = self.model.invoke(prompt_value)
            parsed_response = self.parser.invoke(model_response)
            
            return response_prefix + parsed_response
        else:
            # Use fallback prompt
            prompt_value = self.fallback_prompt.format(
                query=query,
                kb_context=kb_context,
                kg_insights=kg_insights
            )
            
            # Get the response from the model
            model_response = self.model.invoke(prompt_value)
            return self.parser.invoke(model_response)
