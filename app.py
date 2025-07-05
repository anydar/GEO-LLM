from flask import Flask, render_template, request, jsonify
import logging
import os
from dotenv import load_dotenv
from llm import GeoLLM
from tools import GISTools
import json
from shapely.geometry import Polygon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize LLM and GIS tools
try:
    geo_llm = GeoLLM()
    gis_tools = GISTools()
    logger.info("GeoLLM and GISTools initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {str(e)}", exc_info=True)
    raise

app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    logger.info("Chat endpoint called")
    data = request.get_json(silent=True) or {}
    user_query = data.get('query', '')
    
    if not user_query:
        logger.warning("Empty query received")
        return jsonify({'error': 'No query provided'}), 400
    
    logger.info(f"Processing query: {user_query}")
    
    try:
        logger.info("Generating response")
        response = geo_llm.generate_response(user_query)
        logger.info("Response generated")
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/geocode', methods=['POST'])
def geocode():
    """API endpoint to geocode a location name to coordinates"""
    data = request.get_json(silent=True) or {}
    location_name = data.get('location', '')
    
    if not location_name:
        return jsonify({'error': 'No location provided'}), 400
    
    # Prioritize Indian locations if not already specified
    if not any(country in location_name.lower() for country in ['india', 'pakistan', 'bangladesh', 'nepal', 'bhutan', 'sri lanka', 'myanmar']):
        location_name = f"{location_name}, India"
    
    try:
        coordinates = gis_tools.geocode_location(location_name)
        if coordinates:
            # Validate that coordinates are within or near India's bounding box
            lat, lon = coordinates
            india_bbox = {
                'min_lat': 6.5, 'max_lat': 37.5,  # North-South boundaries
                'min_lon': 68.0, 'max_lon': 97.5  # East-West boundaries
            }
            
            # Check if coordinates are within or reasonably close to India
            is_near_india = (
                india_bbox['min_lat'] - 5 <= lat <= india_bbox['max_lat'] + 5 and
                india_bbox['min_lon'] - 5 <= lon <= india_bbox['max_lon'] + 5
            )
            
            if not is_near_india:
                return jsonify({'error': f"Coordinates ({lat}, {lon}) are outside India's geographic region"}), 400
                
            return jsonify({
                'location': location_name,
                'coordinates': {
                    'lat': coordinates[0],
                    'lon': coordinates[1]
                }
            })
        else:
            error_message = f"Could not geocode location: {location_name}"
            logger.warning(error_message)
            return jsonify({'error': error_message}), 404
    except Exception as e:
        logger.error(f"Error geocoding location: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/buffer', methods=['POST'])
def create_buffer():
    """API endpoint to create a buffer around a point"""
    data = request.get_json(silent=True) or {}
    lat = data.get('lat')
    lon = data.get('lon')
    distance_km = data.get('distance_km', 5)  # Default 5km buffer
    
    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        buffer_geom = gis_tools.create_buffer(lat, lon, distance_km)
        if buffer_geom is not None and isinstance(buffer_geom, Polygon):
            # Convert to GeoJSON for frontend use
            buffer_coords = list(buffer_geom.exterior.coords)
            geojson = {
                'type': 'Feature',
                'properties': {
                    'distance_km': distance_km
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[coord[0], coord[1]] for coord in buffer_coords]]
                }
            }
            return jsonify(geojson)
        else:
            return jsonify({'error': 'Could not create buffer'}), 500
    except Exception as e:
        logger.error(f"Error creating buffer: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools', methods=['POST'])
def use_tool():
    """API endpoint to use GIS tools directly"""
    data = request.get_json(silent=True) or {}
    tool_name = data.get('tool', '')
    params = data.get('params', {})
    
    if not tool_name:
        return jsonify({'error': 'No tool specified'}), 400
    
    try:
        # Map tool names to methods
        tool_mapping = {
            'geocode': gis_tools.geocode_location,
            'buffer': gis_tools.create_buffer,
            'calculate_area': gis_tools.calculate_area
        }
        
        if tool_name not in tool_mapping:
            return jsonify({'error': f'Unknown tool: {tool_name}'}), 400
            
        # Call the appropriate tool with parameters
        tool_func = tool_mapping[tool_name]
        result = tool_func(**params)
        
        # Process special result types
        if tool_name == 'buffer' and result is not None and isinstance(result, Polygon):
            # Convert Shapely geometry to GeoJSON
            buffer_coords = list(result.exterior.coords)
            result = {
                'type': 'Feature',
                'properties': {
                    'distance_km': params.get('distance_km', 5)
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[coord[0], coord[1]] for coord in buffer_coords]]
                }
            }
        
        return jsonify({
            'tool': tool_name,
            'result': result
        })
    except Exception as e:
        logger.error(f"Error using tool {tool_name}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True)