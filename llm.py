import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from tools import GISTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class GeoLLM:
    """
    LLM utility class for geospatial analysis using Gemini
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the GeoLLM with API key
        
        Args:
            api_key (str, optional): Google API key. If None, uses environment variable
        """
        self.api_key = api_key or GOOGLE_API_KEY
        if not self.api_key:
            logger.error("No Google API key found")
            raise ValueError("No Google API key found. Please set the GOOGLE_API_KEY environment variable.")
            
        genai.configure(api_key=self.api_key)
        # Reverted to the user-specified model name.
        # Note: 'gemini-2.0-flash-exp' is not a standard public model. 
        # This will only work if the user has access to this specific experimental model.
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("GeoLLM initialized with Gemini API (gemini-2.0-flash-exp)")
        self.gis_tools = GISTools()
        logger.info("GISTools initialized")
        
    def get_system_prompt(self):
        """
        Get the system prompt for geospatial analysis
        
        Returns:
            str: System prompt
        """
        return """
        You are an advanced geospatial analysis assistant for ISRO (Indian Space Research Organisation).
        Your primary role is to answer geospatial questions about India. Your response style depends on the user's query type:

        1.  **For specific Point-of-Interest (POI) or direct location queries** (e.g., "Where is the nearest hospital?", "Find schools in Koramangala", "What is in this area?"): Provide a direct, helpful answer using your general knowledge. You can and should name specific places or landmarks. Frame the answer naturally.

        2.  **For complex analytical or "how-to" queries** (e.g., "How would I identify flood zones?", "Analyze urban growth in Hyderabad"): Provide a concise, direct answer that explains the outcome or methodology of a hypothetical GIS analysis.

        ---
        IMPORTANT RULES FOR ALL RESPONSES:
        - Your entire focus is on INDIA. All locations, data, and context must be Indian.
        - If a location is ambiguous, assume it's in India.
        - DO NOT use phrases like "Based on my analysis," "As an AI," or "I lack the capability." Directly provide the answer.
        - DO NOT show your step-by-step reasoning or use numbered lists in the final answer.
        - NEVER use coordinates or examples from outside of India.
        ---
        
        REFERENCE DATA AND TOOLS FOR YOUR KNOWLEDGE BASE (for analytical queries):
        - Remote Sensing Data: IRS, Cartosat, ResourceSat, RISAT, Oceansat, INSAT/GSAT.
        - GIS Platforms: QGIS, Bhuvan, VEDAS, NRSC Open Data Archive, MOSDAC.
        - Indian Data Sources: Census of India, Survey of India, India WRIS, NBSS&LUP soil maps, Forest Survey of India, IMD climate data.
        - Analysis Libraries: GeoPandas, Rasterio, Folium.
        ---
        Question: {query}
        
        Answer:
        """
        
    def generate_response(self, query):
        """
        Generate a response for a geospatial query
        
        Args:
            query (str): User's geospatial query
            
        Returns:
            str: Generated response
        """
        try:
            prompt = self.get_system_prompt().format(query=query)
            logger.info("Sending request to Gemini API.")
            
            response = self.model.generate_content(prompt)
            logger.info("Response received from Gemini API.")

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                logger.error(f"Prompt was blocked by the API. Reason: {block_reason}")
                return f"Error: Your query was blocked by the content safety filter. Reason: {block_reason}. Please rephrase your question."

            if response.candidates:
                first_candidate = response.candidates[0]
                if first_candidate.content and first_candidate.content.parts:
                    generated_text = "".join(part.text for part in first_candidate.content.parts)
                    if generated_text:
                        logger.info("Successfully extracted text from response.")
                        return generated_text
                    else:
                        logger.warning("API response received, but the generated text is empty.")
                        return "Error: The model returned an empty response. Please try rephrasing your question."
                else:
                    finish_reason = first_candidate.finish_reason.name if hasattr(first_candidate, 'finish_reason') and first_candidate.finish_reason else "UNKNOWN"
                    logger.error(f"API response has no content parts. Finish reason: {finish_reason}")
                    return f"Error: The model could not generate a response. Reason: {finish_reason}. This may be due to safety filters."
            else:
                logger.error("No candidates found in the API response.")
                return "Error: Received an invalid response from the AI model (no candidates)."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"Error: An unexpected error occurred while communicating with the AI model. Please check the backend logs. Details: {str(e)}"