"""
Location Processing for Apollo API
Handles parsing raw location input and converting to Apollo-compatible location IDs
"""

import logging
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
    """Processes location data for Apollo API searches"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.openai_client = openai_client
        
        # Common location mappings for quick lookup
        self.apollo_location_cache = {
            # Major US Cities
            "new york": ["5128581"],  # New York City
            "nyc": ["5128581"],
            "new york city": ["5128581"],
            "los angeles": ["5368361"],
            "la": ["5368361"],
            "chicago": ["4887398"],
            "houston": ["4699066"],
            "phoenix": ["5308655"],
            "philadelphia": ["4560349"],
            "san antonio": ["4726206"],
            "san diego": ["5391811"],
            "dallas": ["4684888"],
            "san jose": ["5392171"],
            "austin": ["4671654"],
            "jacksonville": ["4160023"],
            "fort worth": ["4691930"],
            "columbus": ["4509177"],
            "charlotte": ["4460243"],
            "san francisco": ["5391959"],
            "sf": ["5391959"],
            "indianapolis": ["4259418"],
            "seattle": ["5809844"],
            "denver": ["5419384"],
            "washington": ["4140963"],
            "washington dc": ["4140963"],
            "dc": ["4140963"],
            "boston": ["4930956"],
            "nashville": ["4644585"],
            "detroit": ["4990729"],
            "portland": ["5746545"],
            "las vegas": ["5506956"],
            "memphis": ["4641239"],
            "louisville": ["4299276"],
            "baltimore": ["4347778"],
            "milwaukee": ["5263045"],
            "albuquerque": ["5454711"],
            "tucson": ["5318313"],
            "fresno": ["5350937"],
            "sacramento": ["5389489"],
            "kansas city": ["4273837"],
            "atlanta": ["4180439"],
            "colorado springs": ["5417598"],
            "raleigh": ["4487042"],
            "omaha": ["5074472"],
            "miami": ["4164138"],
            "cleveland": ["5150529"],
            "tulsa": ["4553433"],
            "arlington": ["4671171"],
            "tampa": ["4174757"],
            "new orleans": ["4335045"],
            "wichita": ["4281730"],
            "honolulu": ["5856195"],
            "anaheim": ["5322400"],
            "santa ana": ["5393052"],
            "corpus christi": ["4672227"],
            "riverside": ["5386082"],
            "lexington": ["4297983"],
            "stockton": ["5400075"],
            "st. paul": ["5037649"],
            "cincinnati": ["4508722"],
            "anchorage": ["5879400"],
            "henderson": ["5506956"],  # Part of Las Vegas metro
            "greensboro": ["4460162"],
            "plano": ["4715311"],
            "newark": ["5101798"],
            "lincoln": ["5073708"],
            "orlando": ["4167147"],
            "irvine": ["5359777"],
            "toledo": ["4006508"],
            "jersey city": ["5099133"],
            "chula vista": ["5344994"],
            "durham": ["4464368"],
            "fort wayne": ["4920423"],
            "st. petersburg": ["4171563"],
            "laredo": ["4705349"],
            "buffalo": ["5110629"],
            "madison": ["5261457"],
            
            # US States
            "california": ["5332921"],
            "ca": ["5332921"],
            "texas": ["4736286"],
            "tx": ["4736286"],
            "florida": ["4155751"],
            "fl": ["4155751"],
            "new york state": ["5128638"],
            "ny": ["5128638"],
            "pennsylvania": ["6254927"],
            "pa": ["6254927"],
            "illinois": ["4896861"],
            "il": ["4896861"],
            "ohio": ["4851859"],
            "oh": ["4851859"],
            "georgia": ["4197000"],
            "ga": ["4197000"],
            "north carolina": ["4482348"],
            "nc": ["4482348"],
            "michigan": ["5001836"],
            "mi": ["5001836"],
            "new jersey": ["5101760"],
            "nj": ["5101760"],
            "virginia": ["6254928"],
            "va": ["6254928"],
            "washington state": ["5815135"],
            "wa": ["5815135"],
            "arizona": ["5551752"],
            "az": ["5551752"],
            "massachusetts": ["6254926"],
            "ma": ["6254926"],
            "tennessee": ["4662168"],
            "tn": ["4662168"],
            "indiana": ["4921868"],
            "in": ["4921868"],
            "missouri": ["4398678"],
            "mo": ["4398678"],
            "maryland": ["4361885"],
            "md": ["4361885"],
            "wisconsin": ["5279468"],
            "wi": ["5279468"],
            "colorado": ["5417618"],
            "co": ["5417618"],
            "minnesota": ["5037779"],
            "mn": ["5037779"],
            "south carolina": ["4597040"],
            "sc": ["4597040"],
            "alabama": ["4829764"],
            "al": ["4829764"],
            "louisiana": ["4331987"],
            "la": ["4331987"],
            "kentucky": ["6254925"],
            "ky": ["6254925"],
            "oregon": ["5744337"],
            "or": ["5744337"],
            "oklahoma": ["4544379"],
            "ok": ["4544379"],
            "connecticut": ["4831725"],
            "ct": ["4831725"],
            "utah": ["5549030"],
            "ut": ["5549030"],
            "iowa": ["4862182"],
            "ia": ["4862182"],
            "nevada": ["5509151"],
            "nv": ["5509151"],
            "arkansas": ["4099753"],
            "ar": ["4099753"],
            "mississippi": ["4436296"],
            "ms": ["4436296"],
            "kansas": ["4273857"],
            "ks": ["4273857"],
            "new mexico": ["5481136"],
            "nm": ["5481136"],
            "nebraska": ["5073708"],
            "ne": ["5073708"],
            "west virginia": ["4826850"],
            "wv": ["4826850"],
            "idaho": ["5596512"],
            "id": ["5596512"],
            "hawaii": ["5855797"],
            "hi": ["5855797"],
            "new hampshire": ["5090174"],
            "nh": ["5090174"],
            "maine": ["4971068"],
            "me": ["4971068"],
            "montana": ["5667009"],
            "mt": ["5667009"],
            "rhode island": ["5224323"],
            "ri": ["5224323"],
            "delaware": ["4142224"],
            "de": ["4142224"],
            "south dakota": ["5769223"],
            "sd": ["5769223"],
            "north dakota": ["5690763"],
            "nd": ["5690763"],
            "alaska": ["5879092"],
            "ak": ["5879092"],
            "vermont": ["5242283"],
            "vt": ["5242283"],
            "wyoming": ["5843591"],
            "wy": ["5843591"],
            
            # Major International Cities/Countries
            "london": ["2643743"],
            "united kingdom": ["2635167"],
            "uk": ["2635167"],
            "toronto": ["6167865"],
            "canada": ["6251999"],
            "paris": ["2988507"],
            "france": ["3017382"],
            "berlin": ["2950159"],
            "germany": ["2921044"],
            "tokyo": ["1850147"],
            "japan": ["1861060"],
            "sydney": ["2147714"],
            "australia": ["2077456"],
            "amsterdam": ["2759794"],
            "netherlands": ["2750405"],
            "singapore": ["1880251"],
            "hong kong": ["1819730"],
            "dublin": ["2964574"],
            "ireland": ["2963597"],
            "zurich": ["2657896"],
            "switzerland": ["2658434"],
            "stockholm": ["2673730"],
            "sweden": ["2661886"],
            "copenhagen": ["2618425"],
            "denmark": ["2623032"],
            "oslo": ["3143244"],
            "norway": ["3144096"],
            "helsinki": ["658225"],
            "finland": ["660013"],
            "brussels": ["2800866"],
            "belgium": ["2802361"],
            "vienna": ["2761369"],
            "austria": ["2782113"],
            "barcelona": ["3128760"],
            "madrid": ["3117735"],
            "spain": ["2510769"],
            "rome": ["3169070"],
            "milan": ["3173435"],
            "italy": ["3175395"],
            "mumbai": ["1275339"],
            "bangalore": ["1277333"],
            "india": ["1269750"],
            "seoul": ["1835848"],
            "south korea": ["1835841"],
            "beijing": ["1816670"],
            "shanghai": ["1796236"],
            "china": ["1814991"],
            "mexico city": ["3530597"],
            "mexico": ["3996063"],
            "sao paulo": ["3448439"],
            "brazil": ["3469034"],
            "buenos aires": ["3435910"],
            "argentina": ["3865483"],
            "tel aviv": ["293397"],
            "israel": ["294640"],
        }
    
    def parse_location_with_llm(self, raw_location: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse raw location string using LLM to extract Apollo-compatible location IDs
        
        Args:
            raw_location: Raw location string (e.g., "San Francisco Bay Area, California")
            
        Returns:
            Tuple of (apollo_location_ids, parsed_info)
        """
        if not self.openai_client:
            # Fallback to simple parsing
            return self._simple_location_parse(raw_location)
        
        try:
            prompt = f"""
Parse the following location string and extract specific location information for business lead targeting:

Location: "{raw_location}"

Extract and return a JSON object with:
1. "cities": Array of specific cities mentioned
2. "states_provinces": Array of states/provinces mentioned  
3. "countries": Array of countries mentioned
4. "regions": Array of broader regions (e.g., "Bay Area", "New England")
5. "confidence": Number from 0-1 indicating parsing confidence
6. "suggested_apollo_terms": Array of location terms optimized for Apollo.io search

Focus on:
- Exact city/state/country names
- Common business location terminology
- Alternative names and abbreviations
- Metropolitan areas

Return only valid JSON.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            apollo_ids = self._convert_to_apollo_ids(parsed_data)
            
            return apollo_ids, parsed_data
            
        except Exception as e:
            logger.warning(f"LLM location parsing failed: {e}, falling back to simple parsing")
            return self._simple_location_parse(raw_location)
    
    def _simple_location_parse(self, raw_location: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Simple location parsing without LLM
        """
        location_lower = raw_location.lower().strip()
        
        # Direct cache lookup
        if location_lower in self.apollo_location_cache:
            return self.apollo_location_cache[location_lower], {
                "method": "cache_lookup",
                "confidence": 0.9,
                "original": raw_location
            }
        
        # Try to find partial matches
        apollo_ids = []
        matched_terms = []
        
        for cache_term, ids in self.apollo_location_cache.items():
            if cache_term in location_lower or location_lower in cache_term:
                apollo_ids.extend(ids)
                matched_terms.append(cache_term)
        
        # Remove duplicates
        apollo_ids = list(set(apollo_ids))
        
        if apollo_ids:
            return apollo_ids, {
                "method": "partial_match",
                "matched_terms": matched_terms,
                "confidence": 0.7,
                "original": raw_location
            }
        
        # Last resort: extract common patterns
        extracted = self._extract_location_patterns(raw_location)
        
        return [], {
            "method": "pattern_extraction",
            "extracted_terms": extracted,
            "confidence": 0.3,
            "original": raw_location,
            "requires_manual_mapping": True
        }
    
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
    
    def _convert_to_apollo_ids(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Convert parsed location data to Apollo location IDs
        """
        apollo_ids = []
        
        # Check all location terms from LLM parsing
        all_terms = []
        all_terms.extend(parsed_data.get('cities', []))
        all_terms.extend(parsed_data.get('states_provinces', []))
        all_terms.extend(parsed_data.get('countries', []))
        all_terms.extend(parsed_data.get('regions', []))
        all_terms.extend(parsed_data.get('suggested_apollo_terms', []))
        
        for term in all_terms:
            term_lower = term.lower().strip()
            if term_lower in self.apollo_location_cache:
                apollo_ids.extend(self.apollo_location_cache[term_lower])
        
        return list(set(apollo_ids))  # Remove duplicates
    
    def get_apollo_location_params(self, location_config: LocationConfig) -> Dict[str, Any]:
        """
        Get Apollo API location parameters from LocationConfig
        
        Args:
            location_config: LocationConfig object
            
        Returns:
            Dict with Apollo API location parameters
        """
        params = {}
        
        if location_config.use_llm_parsing and location_config.raw_location:
            # Use LLM to parse location
            api_keys = get_api_keys()
            if api_keys.get('openai'):
                self.openai_client = OpenAI(api_key=api_keys['openai'])
            
            apollo_ids, parsed_info = self.parse_location_with_llm(location_config.raw_location)
            
            if apollo_ids:
                params['organization_locations'] = apollo_ids
                logger.info(f"Using LLM-parsed location IDs: {apollo_ids} for '{location_config.raw_location}'")
            else:
                logger.warning(f"Could not parse location: {location_config.raw_location}")
                logger.info(f"Parsing info: {parsed_info}")
        
        elif location_config.apollo_location_ids:
            # Use pre-configured Apollo location IDs
            params['organization_locations'] = location_config.apollo_location_ids
            logger.info(f"Using configured location IDs: {location_config.apollo_location_ids}")
        
        return params
    
    def validate_apollo_location_ids(self, location_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate Apollo location IDs (basic format validation)
        
        Args:
            location_ids: List of location ID strings
            
        Returns:
            Tuple of (valid_ids, invalid_ids)
        """
        valid_ids = []
        invalid_ids = []
        
        for location_id in location_ids:
            # Basic validation - Apollo location IDs are typically numeric strings
            if isinstance(location_id, str) and location_id.isdigit() and len(location_id) >= 6:
                valid_ids.append(location_id)
            else:
                invalid_ids.append(location_id)
        
        return valid_ids, invalid_ids
    
    def get_location_suggestions(self, partial_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get location suggestions for autocomplete
        
        Args:
            partial_text: Partial location text
            limit: Maximum number of suggestions
            
        Returns:
            List of location suggestions with display names and Apollo IDs
        """
        suggestions = []
        partial_lower = partial_text.lower()
        
        for location_name, apollo_ids in self.apollo_location_cache.items():
            if partial_lower in location_name and len(suggestions) < limit:
                suggestions.append({
                    'display_name': location_name.title(),
                    'apollo_ids': apollo_ids,
                    'type': self._get_location_type(location_name)
                })
        
        return suggestions
    
    def _get_location_type(self, location_name: str) -> str:
        """
        Determine if location is city, state, or country
        """
        # Simple heuristics based on our cache structure
        if len(location_name) == 2 and location_name.isupper():
            return 'state_abbrev'
        elif any(country in location_name.lower() for country in ['kingdom', 'states', 'republic']):
            return 'country'
        elif 'state' in location_name.lower():
            return 'state'
        else:
            return 'city'


# Global instance
location_processor = LocationProcessor() 