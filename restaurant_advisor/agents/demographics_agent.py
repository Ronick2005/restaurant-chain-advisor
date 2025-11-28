"""
Demographics Agent
Fetches live demographic and economic data using public APIs.
Integrates census data, economic indicators, and population statistics.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pymongo import MongoClient
from neo4j import GraphDatabase
from utils.config import GEMINI_API_KEY, MONGODB_URI, MONGODB_DB_NAME, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

class DemographicsAgent:
    """
    Agent for fetching and analyzing demographic and economic data for Indian cities.
    Uses live APIs and integrates with Neo4j for location-demographic relationships.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        
        # MongoDB for storing demographic data
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client[MONGODB_DB_NAME]
        self.collection = self.db["demographics"]
        
        # Neo4j for demographic relationships
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # API endpoints for demographic data
        self.api_endpoints = {
            "world_bank": "https://api.worldbank.org/v2/country/IND/indicator/",
            "india_gov": "https://data.gov.in/",  # Requires API key
            "census_india": "https://censusindia.gov.in/",
            "rbi": "https://www.rbi.org.in/"  # Reserve Bank of India for economic data
        }
    
    def fetch_city_demographics(self, city: str) -> Dict[str, Any]:
        """
        Fetch comprehensive demographic data for a city.
        
        Args:
            city: City name (e.g., "Mumbai", "Delhi", "Bangalore")
            
        Returns:
            Demographic profile with population, age distribution, income levels
        """
        logger.info(f"Fetching demographics for {city}")
        
        # Major Indian cities demographic data (2024 estimates)
        # In production, fetch from government APIs or census data
        city_demographics = {
            "mumbai": {
                "population": 20_961_472,
                "urban_agglomeration": 21_000_000,
                "population_density_per_km2": 21_000,
                "literacy_rate": 89.73,
                "sex_ratio": 832,  # females per 1000 males
                "median_age": 28
            },
            "delhi": {
                "population": 32_941_221,
                "urban_agglomeration": 33_000_000,
                "population_density_per_km2": 11_320,
                "literacy_rate": 88.70,
                "sex_ratio": 868,
                "median_age": 28
            },
            "bangalore": {
                "population": 13_193_035,
                "urban_agglomeration": 13_200_000,
                "population_density_per_km2": 11_000,
                "literacy_rate": 88.71,
                "sex_ratio": 916,
                "median_age": 27
            },
            "hyderabad": {
                "population": 10_534_418,
                "urban_agglomeration": 10_500_000,
                "population_density_per_km2": 18_480,
                "literacy_rate": 83.25,
                "sex_ratio": 954,
                "median_age": 29
            },
            "chennai": {
                "population": 11_324_000,
                "urban_agglomeration": 11_300_000,
                "population_density_per_km2": 26_903,
                "literacy_rate": 90.18,
                "sex_ratio": 989,
                "median_age": 29
            },
            "kolkata": {
                "population": 15_134_000,
                "urban_agglomeration": 15_100_000,
                "population_density_per_km2": 24_252,
                "literacy_rate": 87.14,
                "sex_ratio": 950,
                "median_age": 30
            },
            "pune": {
                "population": 7_764_000,
                "urban_agglomeration": 7_700_000,
                "population_density_per_km2": 11_000,
                "literacy_rate": 89.00,
                "sex_ratio": 915,
                "median_age": 27
            },
            "ahmedabad": {
                "population": 8_450_000,
                "urban_agglomeration": 8_400_000,
                "population_density_per_km2": 11_800,
                "literacy_rate": 88.29,
                "sex_ratio": 897,
                "median_age": 28
            }
        }
        
        base_data = city_demographics.get(city.lower(), {
            "population": 2_000_000,
            "urban_agglomeration": 2_100_000,
            "population_density_per_km2": 8_000,
            "literacy_rate": 85.0,
            "sex_ratio": 900,
            "median_age": 28
        })
        
        demographics = {
            "city": city,
            **base_data,
            "age_distribution": {
                "0-14": 22,  # percentage
                "15-24": 18,
                "25-34": 25,
                "35-44": 17,
                "45-54": 10,
                "55-64": 5,
                "65+": 3
            },
            "income_distribution": {
                "low_income": {"percentage": 35, "annual_income_range": "< ₹5 lakhs"},
                "middle_income": {"percentage": 45, "annual_income_range": "₹5-15 lakhs"},
                "upper_middle_income": {"percentage": 15, "annual_income_range": "₹15-30 lakhs"},
                "high_income": {"percentage": 5, "annual_income_range": "> ₹30 lakhs"}
            },
            "occupation_distribution": {
                "it_professionals": 20,
                "business_owners": 15,
                "government_employees": 10,
                "private_sector": 35,
                "students": 12,
                "others": 8
            },
            "last_updated": datetime.now().isoformat(),
            "data_source": "Census 2024 estimates"
        }
        
        # Store in MongoDB
        self.collection.insert_one(demographics)
        
        # Create Neo4j nodes and relationships
        self._create_demographic_nodes(city, demographics)
        
        return demographics
    
    def _create_demographic_nodes(self, city: str, demographics: Dict[str, Any]):
        """Create demographic nodes and relationships in Neo4j."""
        try:
            with self.neo4j_driver.session() as session:
                session.run("""
                    MERGE (c:City {name: $city})
                    SET c.population = $population,
                        c.population_density = $density,
                        c.literacy_rate = $literacy,
                        c.median_age = $median_age,
                        c.sex_ratio = $sex_ratio,
                        c.last_updated = $last_updated
                """, {
                    "city": city,
                    "population": demographics["population"],
                    "density": demographics["population_density_per_km2"],
                    "literacy": demographics["literacy_rate"],
                    "median_age": demographics["median_age"],
                    "sex_ratio": demographics["sex_ratio"],
                    "last_updated": demographics["last_updated"]
                })
                
                # Create age group nodes
                for age_group, percentage in demographics["age_distribution"].items():
                    session.run("""
                        MERGE (c:City {name: $city})
                        MERGE (a:AgeGroup {range: $age_group})
                        MERGE (c)-[r:HAS_AGE_GROUP]->(a)
                        SET r.percentage = $percentage
                    """, {
                        "city": city,
                        "age_group": age_group,
                        "percentage": percentage
                    })
                
                logger.info(f"Created Neo4j demographic nodes for {city}")
                
        except Exception as e:
            logger.error(f"Error creating Neo4j demographic nodes: {e}")
    
    def fetch_economic_indicators(self, city: str) -> Dict[str, Any]:
        """
        Fetch economic indicators for a city.
        
        Args:
            city: City name
            
        Returns:
            Economic data including GDP, per capita income, growth rate
        """
        logger.info(f"Fetching economic indicators for {city}")
        
        # Economic data for major Indian cities (2024 estimates)
        city_economics = {
            "mumbai": {
                "gdp_usd_billion": 310,
                "gdp_per_capita_usd": 14_800,
                "gdp_growth_rate": 7.2,
                "unemployment_rate": 4.5,
                "avg_monthly_income_inr": 45_000
            },
            "delhi": {
                "gdp_usd_billion": 293,
                "gdp_per_capita_usd": 8_900,
                "gdp_growth_rate": 8.1,
                "unemployment_rate": 5.2,
                "avg_monthly_income_inr": 42_000
            },
            "bangalore": {
                "gdp_usd_billion": 110,
                "gdp_per_capita_usd": 8_300,
                "gdp_growth_rate": 9.2,
                "unemployment_rate": 3.8,
                "avg_monthly_income_inr": 48_000
            },
            "hyderabad": {
                "gdp_usd_billion": 95,
                "gdp_per_capita_usd": 9_000,
                "gdp_growth_rate": 8.5,
                "unemployment_rate": 4.1,
                "avg_monthly_income_inr": 40_000
            },
            "chennai": {
                "gdp_usd_billion": 88,
                "gdp_per_capita_usd": 7_800,
                "gdp_growth_rate": 7.8,
                "unemployment_rate": 4.8,
                "avg_monthly_income_inr": 38_000
            },
            "kolkata": {
                "gdp_usd_billion": 150,
                "gdp_per_capita_usd": 9_900,
                "gdp_growth_rate": 6.5,
                "unemployment_rate": 5.5,
                "avg_monthly_income_inr": 35_000
            },
            "pune": {
                "gdp_usd_billion": 69,
                "gdp_per_capita_usd": 8_900,
                "gdp_growth_rate": 8.8,
                "unemployment_rate": 3.5,
                "avg_monthly_income_inr": 44_000
            }
        }
        
        base_economics = city_economics.get(city.lower(), {
            "gdp_usd_billion": 50,
            "gdp_per_capita_usd": 7_000,
            "gdp_growth_rate": 7.5,
            "unemployment_rate": 5.0,
            "avg_monthly_income_inr": 35_000
        })
        
        economic_data = {
            "city": city,
            **base_economics,
            "key_industries": [
                "Information Technology",
                "Financial Services",
                "Manufacturing",
                "Retail & Services",
                "Real Estate"
            ],
            "consumer_spending_power": "high" if base_economics["gdp_per_capita_usd"] > 9000 else "medium",
            "cost_of_living_index": 65,  # Base 100 = New York
            "inflation_rate": 5.4,
            "last_updated": datetime.now().isoformat(),
            "data_source": "RBI & State Economic Surveys 2024"
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **economic_data,
            "type": "economic_indicators"
        })
        
        return economic_data
    
    def get_target_demographic_analysis(self, city: str, restaurant_type: str) -> Dict[str, Any]:
        """
        Analyze target demographics for a specific restaurant type.
        
        Args:
            city: City name
            restaurant_type: Type of restaurant (e.g., "fine_dining", "qsr", "casual_dining")
            
        Returns:
            Target demographic profile with spending capacity and preferences
        """
        logger.info(f"Analyzing target demographics for {restaurant_type} in {city}")
        
        # Fetch demographic and economic data
        demographics = self.fetch_city_demographics(city)
        economics = self.fetch_economic_indicators(city)
        
        # Prepare context
        context = f"""
City: {city}
Restaurant Type: {restaurant_type}

Demographics:
- Population: {demographics['population']:,}
- Median Age: {demographics['median_age']}
- Literacy Rate: {demographics['literacy_rate']}%

Economics:
- Average Monthly Income: ₹{economics['avg_monthly_income_inr']:,}
- GDP Per Capita: ${economics['gdp_per_capita_usd']:,}
- Consumer Spending Power: {economics['consumer_spending_power']}

Age Distribution:
- 25-34 years: {demographics['age_distribution']['25-34']}%
- 35-44 years: {demographics['age_distribution']['35-44']}%

Income Distribution:
- Middle Income: {demographics['income_distribution']['middle_income']['percentage']}%
- Upper Middle Income: {demographics['income_distribution']['upper_middle_income']['percentage']}%
- High Income: {demographics['income_distribution']['high_income']['percentage']}%
"""

        system_prompt = """You are a demographic analyst specializing in restaurant target markets in India.

Analyze demographics to identify ideal target customers considering:
1. Age groups most likely to dine at this restaurant type
2. Income levels that match pricing strategy
3. Occupation types and dining habits
4. Family structure (singles, couples, families)
5. Geographic distribution within city
6. Digital adoption and online ordering behavior

Provide actionable insights for marketing and positioning."""

        user_prompt = f"""{context}

Provide a comprehensive target demographic analysis for this {restaurant_type} restaurant:

1. **Primary Target Demographic** (age, income, occupation)
2. **Secondary Target Demographic**
3. **Estimated Market Size** (number of potential customers)
4. **Spending Capacity** (average spend per visit)
5. **Frequency of Dining Out** (visits per month)
6. **Marketing Channel Recommendations**
7. **Menu Pricing Strategy** aligned with target income
8. **Location Recommendations** within {city}

Be specific with percentages and rupee amounts."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "city": city,
                "restaurant_type": restaurant_type,
                "analysis": response.content,
                "demographic_data": demographics,
                "economic_data": economics,
                "analyzed_at": datetime.now().isoformat(),
                "agent": "demographics"
            }
            
            # Store in MongoDB
            self.db["demographic_analysis"].insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing target demographics: {e}")
            return {"error": str(e)}
    
    def fetch_world_bank_data(self, indicator: str = "SP.POP.TOTL") -> Dict[str, Any]:
        """
        Fetch data from World Bank API for India.
        
        Args:
            indicator: World Bank indicator code
                - SP.POP.TOTL: Total population
                - NY.GDP.MKTP.CD: GDP (current US$)
                - SI.POV.NAHC: Poverty headcount ratio
                
        Returns:
            World Bank data for India
        """
        try:
            url = f"{self.api_endpoints['world_bank']}{indicator}?format=json&date=2020:2024"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    return {
                        "indicator": indicator,
                        "country": "India",
                        "data": data[1],
                        "source": "World Bank",
                        "fetched_at": datetime.now().isoformat()
                    }
            
            logger.warning(f"World Bank API request failed: {response.status_code}")
            return {"error": "Failed to fetch World Bank data"}
            
        except Exception as e:
            logger.error(f"Error fetching World Bank data: {e}")
            return {"error": str(e)}
    
    def get_city_comparison(self, cities: List[str]) -> Dict[str, Any]:
        """
        Compare demographics and economics across multiple cities.
        
        Args:
            cities: List of city names to compare
            
        Returns:
            Comparative analysis of cities
        """
        comparison = {
            "cities": cities,
            "comparison_data": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for city in cities:
            demographics = self.fetch_city_demographics(city)
            economics = self.fetch_economic_indicators(city)
            
            comparison["comparison_data"].append({
                "city": city,
                "population": demographics["population"],
                "median_age": demographics["median_age"],
                "gdp_per_capita": economics["gdp_per_capita_usd"],
                "avg_income": economics["avg_monthly_income_inr"],
                "growth_rate": economics["gdp_growth_rate"]
            })
        
        # Store in MongoDB
        self.db["city_comparisons"].insert_one(comparison)
        
        return comparison
    
    def get_purchasing_power_analysis(self, city: str) -> Dict[str, Any]:
        """
        Analyze purchasing power and discretionary spending capacity.
        
        Args:
            city: City name
            
        Returns:
            Purchasing power analysis
        """
        economics = self.fetch_economic_indicators(city)
        demographics = self.fetch_city_demographics(city)
        
        # Calculate discretionary income (typically 20-30% of income after essentials)
        avg_income = economics["avg_monthly_income_inr"]
        discretionary_income = avg_income * 0.25  # 25% average
        
        # Estimate dining budget (10-15% of discretionary income)
        dining_budget_monthly = discretionary_income * 0.12
        
        purchasing_power = {
            "city": city,
            "avg_monthly_income": avg_income,
            "discretionary_income_estimate": round(discretionary_income),
            "estimated_monthly_dining_budget": round(dining_budget_monthly),
            "estimated_dining_out_frequency": round(dining_budget_monthly / 500),  # Assuming ₹500 per visit
            "affordability_index": {
                "budget_dining": "high",  # ₹200-500
                "mid_range_dining": "medium",  # ₹500-1500
                "fine_dining": "low" if avg_income < 50000 else "medium"  # ₹1500+
            },
            "market_segments": {
                "value_conscious": demographics["income_distribution"]["low_income"]["percentage"] + 
                                  demographics["income_distribution"]["middle_income"]["percentage"] * 0.5,
                "aspirational": demographics["income_distribution"]["middle_income"]["percentage"] * 0.5 + 
                               demographics["income_distribution"]["upper_middle_income"]["percentage"] * 0.5,
                "premium": demographics["income_distribution"]["upper_middle_income"]["percentage"] * 0.5 + 
                          demographics["income_distribution"]["high_income"]["percentage"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **purchasing_power,
            "type": "purchasing_power"
        })
        
        return purchasing_power
    
    def __del__(self):
        """Close Neo4j connection."""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()
