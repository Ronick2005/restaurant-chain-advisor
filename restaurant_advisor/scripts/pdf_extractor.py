"""
PDF extractor for restaurant advisor system.
Extracts relevant information from PDF files to enhance the knowledge graph.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import json

# Using pypdf instead of PyPDF2 to avoid deprecation warnings
from pypdf import PdfReader

class PDFExtractor:
    """Extracts information from PDF files for the restaurant knowledge graph."""
    
    def __init__(self, pdf_directory: str):
        """Initialize the PDF extractor.
        
        Args:
            pdf_directory: Path to directory containing PDF files
        """
        self.pdf_directory = Path(pdf_directory)
        if not self.pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory not found: {pdf_directory}")
    
    def list_pdf_files(self) -> List[Path]:
        """List all PDF files in the directory.
        
        Returns:
            List of Path objects for PDF files
        """
        return list(self.pdf_directory.glob("*.pdf"))
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def extract_food_regulations(self, text: str) -> Dict[str, Any]:
        """Extract food regulatory information from text.
        
        Args:
            text: Text extracted from PDF
            
        Returns:
            Dictionary with regulatory information
        """
        regulations = {
            "licensing_requirements": [],
            "health_safety": [],
            "food_standards": []
        }
        
        # Look for licensing requirements
        license_patterns = [
            r"(?:license|licensing|permit).*?requirements",
            r"FSSAI.*?registration",
            r"food.*?business.*?operator",
            r"health.*?department.*?approval"
        ]
        
        for pattern in license_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the sentence containing the match
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in regulations["licensing_requirements"]:
                    regulations["licensing_requirements"].append(sentence)
        
        # Look for health and safety regulations
        safety_patterns = [
            r"health.*?safety",
            r"hygiene.*?standards",
            r"sanitation.*?requirements",
            r"food.*?handler.*?training"
        ]
        
        for pattern in safety_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in regulations["health_safety"]:
                    regulations["health_safety"].append(sentence)
        
        # Look for food standards
        standards_patterns = [
            r"food.*?standards",
            r"quality.*?control",
            r"storage.*?requirements",
            r"labeling.*?requirements"
        ]
        
        for pattern in standards_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in regulations["food_standards"]:
                    regulations["food_standards"].append(sentence)
        
        return regulations
    
    def extract_consumer_preferences(self, text: str) -> Dict[str, Any]:
        """Extract consumer preference information from text.
        
        Args:
            text: Text extracted from PDF
            
        Returns:
            Dictionary with consumer preference information
        """
        preferences = {
            "food_trends": [],
            "popular_cuisines": [],
            "dietary_preferences": []
        }
        
        # Look for food trends
        trend_patterns = [
            r"trend.*?in food",
            r"consumer.*?preference",
            r"eating.*?habits",
            r"popular.*?food"
        ]
        
        for pattern in trend_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in preferences["food_trends"]:
                    preferences["food_trends"].append(sentence)
        
        # Look for popular cuisines
        cuisine_patterns = [
            r"(?:popular|favorite).*?cuisine",
            r"(?:Italian|Chinese|Indian|Mexican|Thai|Japanese).*?food",
            r"ethnic.*?food"
        ]
        
        for pattern in cuisine_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in preferences["popular_cuisines"]:
                    preferences["popular_cuisines"].append(sentence)
        
        # Look for dietary preferences
        dietary_patterns = [
            r"(?:vegetarian|vegan|gluten-free|dairy-free|organic).*?food",
            r"dietary.*?(?:preference|restriction)",
            r"healthy.*?eating",
            r"nutritional.*?value"
        ]
        
        for pattern in dietary_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in preferences["dietary_preferences"]:
                    preferences["dietary_preferences"].append(sentence)
        
        return preferences
    
    def extract_real_estate_info(self, text: str) -> Dict[str, Any]:
        """Extract real estate information relevant for restaurant businesses.
        
        Args:
            text: Text extracted from PDF
            
        Returns:
            Dictionary with real estate information
        """
        real_estate = {
            "location_trends": [],
            "rental_insights": [],
            "property_regulations": []
        }
        
        # Look for location trends
        location_patterns = [
            r"prime.*?location",
            r"commercial.*?(?:area|district|zone)",
            r"high.*?foot.*?traffic",
            r"restaurant.*?location"
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in real_estate["location_trends"]:
                    real_estate["location_trends"].append(sentence)
        
        # Look for rental insights
        rental_patterns = [
            r"rental.*?(?:rate|price|cost)",
            r"lease.*?(?:term|agreement|condition)",
            r"property.*?value",
            r"commercial.*?rent"
        ]
        
        for pattern in rental_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in real_estate["rental_insights"]:
                    real_estate["rental_insights"].append(sentence)
        
        # Look for property regulations
        regulation_patterns = [
            r"zoning.*?(?:law|regulation|requirement)",
            r"building.*?code",
            r"property.*?(?:tax|regulation|law)",
            r"commercial.*?property.*?(?:rule|regulation)"
        ]
        
        for pattern in regulation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in real_estate["property_regulations"]:
                    real_estate["property_regulations"].append(sentence)
        
        return real_estate
    
    def extract_city_specific_info(self, text: str) -> Dict[str, str]:
        """Extract city-specific mentions from text.
        
        Args:
            text: Text extracted from PDF
            
        Returns:
            Dictionary mapping cities to relevant information
        """
        cities = {
            "Mumbai": [],
            "Delhi": [],
            "Bangalore": [],
            "Hyderabad": [],
            "Chennai": [],
            "Kolkata": [],
            "Pune": [],
            "Ahmedabad": [],
            "Jaipur": [],
            "Lucknow": []
        }
        
        # For each city, look for mentions and extract sentences
        for city in cities.keys():
            city_pattern = rf"{city}\b"
            matches = re.finditer(city_pattern, text, re.IGNORECASE)
            
            for match in matches:
                start = max(0, text.rfind(".", 0, match.start()) + 1)
                end = text.find(".", match.end())
                if end == -1:
                    end = len(text)
                sentence = text[start:end].strip()
                if sentence and len(sentence) > 10 and sentence not in cities[city]:
                    cities[city].append(sentence)
        
        # Filter out cities with no mentions
        return {city: info for city, info in cities.items() if info}
    
    def process_pdf_file(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF file and extract all relevant information.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with all extracted information
        """
        print(f"Processing PDF: {pdf_path.name}")
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {"filename": pdf_path.name, "error": "No text could be extracted"}
        
        result = {
            "filename": pdf_path.name,
            "regulations": self.extract_food_regulations(text),
            "consumer_preferences": self.extract_consumer_preferences(text),
            "real_estate": self.extract_real_estate_info(text),
            "city_specific": self.extract_city_specific_info(text)
        }
        
        return result
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDF files in the directory.
        
        Returns:
            Dictionary with all extracted information from all PDFs
        """
        pdfs = self.list_pdf_files()
        results = {}
        
        for pdf in pdfs:
            try:
                pdf_data = self.process_pdf_file(pdf)
                results[pdf.name] = pdf_data
            except Exception as e:
                print(f"Error processing {pdf}: {str(e)}")
                results[pdf.name] = {"error": str(e)}
        
        return results
    
    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save extracted results to a JSON file.
        
        Args:
            results: Dictionary with extracted information
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    # Example usage
    data_dir = Path(__file__).parent.parent.parent / "data"
    extractor = PDFExtractor(str(data_dir))
    results = extractor.process_all_pdfs()
    
    output_dir = Path(__file__).parent.parent / "extracted_data"
    output_dir.mkdir(exist_ok=True)
    
    extractor.save_results(results, str(output_dir / "pdf_extracted_data.json"))
