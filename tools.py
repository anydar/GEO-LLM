import geopandas as gpd
import folium
import rasterio
import shapely
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, LineString
import contextily as ctx
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GISTools:
    """
    Collection of GIS utility functions for spatial analysis
    focused on Indian geospatial data and ISRO resources.
    """
    
    def __init__(self):
        # Configure Nominatim with better parameters
        self.geolocator = Nominatim(
            user_agent="isro-geollm-assistant"
        )
        # Add rate limiting to avoid hitting API limits
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
        logger.info("GISTools initialized")
    
    def geocode_location(self, location_name):
        """
        Convert a location name to coordinates (latitude, longitude)
        
        Args:
            location_name (str): Name of location (preferably in India)
            
        Returns:
            tuple: (latitude, longitude) or None if not found
        """
        try:
            # Check if a country is already specified in the location name
            if not any(country in location_name.lower() for country in ['india', 'pakistan', 'bangladesh', 'nepal', 'bhutan', 'sri lanka', 'myanmar']):
                # Prioritize Indian locations by appending India to the query
                search_query = f"{location_name}, India"
            else:
                search_query = location_name
            
            # Try with more flexible geocoding parameters
            location = self.geocode(
                search_query,
                exactly_one=True,
                addressdetails=True,
                namedetails=True,
                language="en",
                extratags=True,
                country_codes="in"  # Limit to India
            )
                
            if location:
                logger.info(f"Geocoded {location_name} to {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            else:
                # Try without country specification if the first attempt fails
                if search_query != location_name:
                    location = self.geocode(
                        location_name,
                        exactly_one=True,
                        addressdetails=True,
                        namedetails=True,
                        language="en"
                    )
                    if location:
                        logger.info(f"Geocoded {location_name} to {location.latitude}, {location.longitude}")
                        return (location.latitude, location.longitude)
                
                # Try with structured query if all else fails
                parts = location_name.split()
                if len(parts) > 1:
                    # Try different combinations of the parts
                    for i in range(len(parts)):
                        city = parts[i]
                        rest = " ".join(parts[:i] + parts[i+1:])
                        structured_query = {
                            "city": city,
                            "country": "India",
                            "state": rest
                        }
                        location = self.geocode(structured_query, exactly_one=True)
                        if location:
                            logger.info(f"Geocoded {location_name} to {location.latitude}, {location.longitude} using structured query")
                            return (location.latitude, location.longitude)
                
                logger.warning(f"Could not geocode location: {location_name}")
                return None
        except Exception as e:
            logger.error(f"Error geocoding {location_name}: {str(e)}")
            return None
    
    def create_buffer(self, lat, lon, distance_km):
        """
        Create a buffer around a point
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            distance_km (float): Buffer distance in kilometers
            
        Returns:
            shapely.geometry.Polygon: Buffer polygon
        """
        try:
            # Create point and convert to UTM for accurate buffering
            point = Point(lon, lat)
            point_gdf = gpd.GeoDataFrame(geometry=[point], crs="EPSG:4326")
            
            # Convert to UTM projection (more accurate for distance calculations)
            utm_zone = int((lon + 180) / 6) + 1
            utm_crs = f"EPSG:326{utm_zone}"  # Northern hemisphere
            if lat < 0:
                utm_crs = f"EPSG:327{utm_zone}"  # Southern hemisphere
                
            point_utm = point_gdf.to_crs(utm_crs)
            
            # Create buffer (distance in meters)
            buffer_utm = point_utm.buffer(distance_km * 1000)
            
            # Convert back to WGS84
            buffer_gdf = gpd.GeoDataFrame(geometry=buffer_utm, crs=utm_crs)
            buffer_wgs84 = buffer_gdf.to_crs("EPSG:4326")
            
            logger.info(f"Created {distance_km}km buffer around {lat}, {lon}")
            return buffer_wgs84.geometry[0]
        except Exception as e:
            logger.error(f"Error creating buffer: {str(e)}")
            return None
    
    def create_map(self, center_lat=20.5937, center_lon=78.9629, zoom=5):
        """
        Create a folium map centered on India
        
        Args:
            center_lat (float): Center latitude (default: India's center)
            center_lon (float): Center longitude (default: India's center)
            zoom (int): Initial zoom level
            
        Returns:
            folium.Map: Map object
        """
        try:
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom,
                          tiles='OpenStreetMap')
            logger.info("Created map centered on India")
            return m
        except Exception as e:
            logger.error(f"Error creating map: {str(e)}")
            return None
    
    def load_geojson(self, file_path):
        """
        Load GeoJSON file into GeoDataFrame
        
        Args:
            file_path (str): Path to GeoJSON file
            
        Returns:
            geopandas.GeoDataFrame: Loaded data
        """
        try:
            gdf = gpd.read_file(file_path)
            logger.info(f"Loaded GeoJSON from {file_path} with {len(gdf)} features")
            return gdf
        except Exception as e:
            logger.error(f"Error loading GeoJSON {file_path}: {str(e)}")
            return None
    
    def spatial_intersection(self, gdf1, gdf2):
        """
        Perform spatial intersection between two GeoDataFrames
        
        Args:
            gdf1 (geopandas.GeoDataFrame): First GeoDataFrame
            gdf2 (geopandas.GeoDataFrame): Second GeoDataFrame
            
        Returns:
            geopandas.GeoDataFrame: Intersection result
        """
        try:
            # Ensure both have same CRS
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
                
            result = gpd.overlay(gdf1, gdf2, how='intersection')
            logger.info(f"Performed spatial intersection, resulting in {len(result)} features")
            return result
        except Exception as e:
            logger.error(f"Error performing spatial intersection: {str(e)}")
            return None
    
    def calculate_area(self, geometry, units='km2'):
        """
        Calculate area of a geometry
        
        Args:
            geometry: Shapely geometry or GeoDataFrame
            units (str): 'km2' or 'm2'
            
        Returns:
            float: Area in specified units
        """
        try:
            if isinstance(geometry, gpd.GeoDataFrame):
                # Convert to equal area projection for accurate area calculation
                geometry_ea = geometry.to_crs('+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=80 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs')
                area_m2 = geometry_ea.geometry.area.sum()
            else:
                # Create a GeoDataFrame from the geometry
                gdf = gpd.GeoDataFrame(geometry=[geometry], crs="EPSG:4326")
                geometry_ea = gdf.to_crs('+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=80 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs')
                area_m2 = geometry_ea.geometry.area[0]
                
            if units == 'km2':
                area = area_m2 / 1_000_000  # Convert to km²
                logger.info(f"Calculated area: {area:.2f} km²")
                return area
            else:
                logger.info(f"Calculated area: {area_m2:.2f} m²")
                return area_m2
        except Exception as e:
            logger.error(f"Error calculating area: {str(e)}")
            return None
            
    def load_raster(self, file_path):
        """
        Load raster data from file
        
        Args:
            file_path (str): Path to raster file
            
        Returns:
            tuple: (data array, transform, metadata)
        """
        try:
            with rasterio.open(file_path) as src:
                data = src.read(1)  # Read first band
                transform = src.transform
                meta = src.meta
                logger.info(f"Loaded raster from {file_path}")
                return data, transform, meta
        except Exception as e:
            logger.error(f"Error loading raster {file_path}: {str(e)}")
            return None, None, None
            
    def find_nearest_features(self, point_gdf, polygon_gdf, k=5):
        """
        Find k nearest polygon features to each point
        
        Args:
            point_gdf (geopandas.GeoDataFrame): Points
            polygon_gdf (geopandas.GeoDataFrame): Polygons
            k (int): Number of nearest features to find
            
        Returns:
            dict: Dictionary mapping point index to list of nearest polygon indices
        """
        try:
            # Ensure same CRS
            if point_gdf.crs != polygon_gdf.crs:
                polygon_gdf = polygon_gdf.to_crs(point_gdf.crs)
                
            # Build spatial index for polygons
            spatial_index = polygon_gdf.sindex
            
            nearest_dict = {}
            
            for idx, point in point_gdf.iterrows():
                # Find potential nearest polygons
                possible_matches_index = list(spatial_index.nearest(point.geometry.bounds, k))
                possible_matches = polygon_gdf.iloc[possible_matches_index]
                
                # Calculate distances
                distances = possible_matches.distance(point.geometry)
                
                # Sort by distance
                nearest_indices = distances.sort_values().index.tolist()[:k]
                nearest_dict[idx] = nearest_indices
                
            logger.info(f"Found nearest features for {len(point_gdf)} points")
            return nearest_dict
        except Exception as e:
            logger.error(f"Error finding nearest features: {str(e)}")
            return None 