"""
Location Processing for Apollo API
Handles parsing raw location input using LLM and converting to clean location strings for Apollo API
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Any
import requests
from openai import OpenAI

from config_model import LocationConfig
from utils.firebase_utils import get_api_keys

# Configure logging for Firebase Functions
from utils.logging_config import get_logger
logger = get_logger(__file__)


class LocationProcessor:
    """Processes location data for Apollo API searches using LLM to extract clean location strings"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.openai_client = openai_client
    
    def parse_location_with_llm(self, raw_location: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse raw location string using LLM to extract clean location strings for Apollo API
        
        Args:
            raw_location: Raw location string (e.g., "123 Main St, San Francisco Bay Area, California, Apt 4B")
            
        Returns:
            Tuple of (clean_location_strings, parsed_info)
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key is required for location processing. Please configure the OpenAI API key in your settings.")
        
        try:
            prompt = f"""
You are a location extraction expert specializing in NARROW, SPECIFIC location targeting for Apollo.io lead searches.

User input: "{raw_location}"

CRITICAL: Apollo uses OR logic between locations. If you include both "Linz" and "Austria", it will search ALL of Austria, making "Linz" meaningless. Focus on the MOST SPECIFIC locations only.

Return a JSON object with:
1. "clean_locations": Array of NARROW, specific location strings for precise targeting
2. "confidence": Number from 0-1 indicating your confidence in the extraction
3. "method": Brief description of how you processed the input
4. "ignored_details": Array of parts you ignored (like broad countries/states)

RULES FOR NARROW TARGETING:
- Use ONLY the most specific locations (cities, districts, neighborhoods)
- NEVER include broad areas (countries, large states) when specific cities are available
- Include VARIATIONS of the same specific location for better coverage
- Remove all street addresses, apartment numbers, zip codes, building names
- Maximum 4-5 location strings, all at similar specificity levels

LOCATION VARIATION EXAMPLES:
- "Linz" → ["Linz", "Linz, Austria", "Linz, Upper Austria", "Linz an der Donau"]
- "San Francisco" → ["San Francisco", "San Francisco, CA", "SF", "San Francisco Bay Area"]
- "Manhattan" → ["Manhattan", "Manhattan, NY", "New York Manhattan", "Manhattan, New York City"]

WRONG (too broad): ["Linz", "Upper Austria", "Austria"] ❌
RIGHT (narrow + variations): ["Linz", "Linz, Austria", "Linz an der Donau"] ✅

WRONG (mixed specificity): ["Brooklyn", "New York", "USA"] ❌  
RIGHT (consistent specificity): ["Brooklyn", "Brooklyn, NY", "Brooklyn, New York"] ✅

Return only valid JSON.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            clean_locations = parsed_data.get('clean_locations', [])
            
            # Validate and clean the location strings
            validated_locations = self._validate_location_strings(clean_locations)
            
            return validated_locations, parsed_data
            
        except Exception as e:
            logger.error(f"LLM location parsing failed: {e}")
            raise ValueError(f"Failed to process location '{raw_location}' with LLM: {str(e)}")
    
    # Note: _simple_location_parse method removed - LLM processing is now mandatory
    
    def _extract_location_patterns(self, text: str) -> List[str]:
        """
        Extract location-like patterns from text using regex
        """
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # City, State
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+\b',  # City, Country
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two-word locations
            r'\b[A-Z]{2}\b',  # State abbreviations
        ]
        
        extracted = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            extracted.extend(matches)
        
        return list(set(extracted))
    
    def _validate_location_strings(self, location_strings: List[str]) -> List[str]:
        """
        Validate and clean location strings for Apollo API
        
        Args:
            location_strings: List of location strings from LLM
            
        Returns:
            List of validated location strings
        """
        validated = []
        
        for location in location_strings:
            if isinstance(location, str):
                # Clean and validate the location string
                cleaned = location.strip()
                
                # Basic validation - must be at least 2 characters and contain letters
                if len(cleaned) >= 2 and any(c.isalpha() for c in cleaned):
                    # Remove any remaining unwanted characters but keep spaces, commas, hyphens
                    import re
                    cleaned = re.sub(r'[^\w\s,\-.]', '', cleaned)
                    if cleaned:
                        validated.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for location in validated:
            location_lower = location.lower()
            if location_lower not in seen:
                seen.add(location_lower)
                result.append(location)
        
        return result
    
    def get_apollo_location_params(self, location_config: LocationConfig) -> Dict[str, Any]:
        """
        Get Apollo API location parameters from LocationConfig using LLM processing
        
        Args:
            location_config: LocationConfig object
            
        Returns:
            Dict with Apollo API location parameters (using location strings)
        """
        params = {}
        
        # Initialize OpenAI client - this is now required
        api_keys = get_api_keys()
        if not api_keys.get('openai'):
            raise ValueError("OpenAI API key is required for location processing. Please configure the OpenAI API key in your settings.")
        
        self.openai_client = OpenAI(api_key=api_keys['openai'])
        
        # Use raw_location if available, otherwise try configured location data
        location_input = location_config.raw_location
        if not location_input and hasattr(location_config, 'location_strings'):
            location_input = ', '.join(location_config.location_strings)
        
        if not location_input:
            raise ValueError("No location data found in configuration. Please set a location description.")
        
        try:
            # Use LLM to parse location into clean strings
            clean_locations, parsed_info = self.parse_location_with_llm(location_input)
            
            if clean_locations:
                # Use clean location strings for Apollo API
                params['person_locations'] = clean_locations
                params['organization_locations'] = clean_locations
                
                logger.info(f"Using LLM-parsed clean locations: {clean_locations} for input '{location_input}'")
                logger.info(f"Parsing method: {parsed_info.get('method', 'unknown')}")
                logger.info(f"Confidence: {parsed_info.get('confidence', 'unknown')}")
                
                if parsed_info.get('ignored_details'):
                    logger.info(f"Ignored details: {parsed_info['ignored_details']}")
            else:
                raise ValueError(f"Could not extract valid locations from: '{location_input}'")
                
        except Exception as e:
            logger.error(f"Failed to process location: {e}")
            raise ValueError(f"Location processing failed for input '{location_input}': {str(e)}")
        
        return params
    
    # Note: validate_apollo_location_ids method removed - now using location strings instead of IDs
    
    # Note: get_location_suggestions and _get_location_type methods removed
    # These methods relied on apollo_location_cache which is no longer used
    # Location suggestions can now be implemented using LLM if needed


# Global instance
location_processor = LocationProcessor() 