# ISRO GeoLLM Assistant

A geospatial analysis chatbot powered by Gemini AI, focused on Indian geography and ISRO resources.

## Overview

The ISRO GeoLLM Assistant is a web application that uses Google's Gemini AI to provide geospatial analysis solutions for queries related to Indian geography. The application leverages Chain-of-Thought (CoT) reasoning to generate geospatial analysis provides concise solutions.

## Features

- Natural language query processing for geospatial questions
- Chain-of-Thought reasoning using Gemini AI
- Focus on Indian geography and ISRO resources
- Integration with GIS libraries for spatial analysis
- Automatic geocoding of location names
- Clean, responsive web interface

## Tech Stack

| Layer       | Technology                         |
|-------------|-----------------------------------|
| LLM Backend | Gemini (via `google.generativeai`) |
| GIS Tools   | GeoPandas, Folium, Rasterio, etc.  |
| Backend     | Python (Flask API)                 |
| Frontend    | HTML, CSS, JavaScript              |

## Project Structure

```
geo-llm-assistant/
│
├── app.py               # Flask application entry point
├── llm.py               # LLM integration and system prompts
├── tools.py             # GIS utility functions
├── requirements.txt     # Python dependencies
├── templates/
│   └── index.html       # Chat frontend UI
└── static/
    ├── styles.css       # CSS styles
    └── main.js          # JavaScript for frontend logic
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd geo-llm-assistant
   ```

2. Create a virtual environment:
   ```
   python -m venv geo
   ```

3. Activate the virtual environment:
   - Windows: `geo\Scripts\activate`
   - Linux/Mac: `source geo/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000`

3. Enter a geospatial query related to Indian geography in the chat interface

## Example Queries

- "How can I identify flood-prone areas in the Brahmaputra basin?"
- "What is the best approach to analyze urban growth patterns in Hyderabad over the last decade?"
- "How would I use remote sensing to monitor crop health in Punjab?"
- "What steps would I take to identify suitable locations for solar power plants in Rajasthan?"

## GIS Tools and Libraries

The application integrates the following GIS libraries:

- **GeoPandas**: Vector data analysis
- **Folium**: Interactive mapping
- **Rasterio**: Raster data processing
- **Shapely**: Geometric operations
- **PyProj**: Coordinate transformations
- **RTree**: Spatial indexing
- **GeoPy**: Geocoding
- **Contextily**: Base maps
- **EarthPy**: Earth data visualization

## ISRO Data Sources

The system is designed to work with:

- IRS (Indian Remote Sensing) satellite imagery
- Cartosat series data
- ResourceSat series (LISS-IV, AWiFS)
- RISAT (Radar Imaging Satellite) data
- Bhuvan geoportal resources
- NRSC (National Remote Sensing Centre) datasets

## License

[MIT License](LICENSE)

## Acknowledgments

- Indian Space Research Organisation (ISRO)
- Google Gemini AI
- Open-source GIS community 