import os
import warnings

try:
    root_dir = config['root_dir']
except NameError:
    root_dir = os.pardir

## functions
    
def normalizeVec(x,y):
    """
    Normalize a 2D vector to unit length.
    
    Args:
        x, y: Components of the vector
        
    Returns:
        Normalized vector components (x/distance, y/distance).
        If distance is 0, returns the original components.
    """
    distance = np.sqrt(x*x+y*y)
    if distance != 0:
        return x/distance, y/distance
    else:
        return x, y

def get_new_coordinates(x, y, offset=-0.00012):
    """
    Generate coordinates for a polygon offset (buffered inward/outward).
    
    This implements a geometric offset that creates a parallel polygon
    at a specified distance from the original.
    
    Args:
        x, y: Lists of coordinate points for the polygon vertices
        offset: Distance to offset (negative for inward, positive for outward)
        
    Returns:
        Lists of new x and y coordinates for the offset polygon
    """
    newX = []
    newY = []
    
    def makeOffsetPoly(oldX, oldY, offset, outer_ccw = 1):
        """
        Inner function that performs the actual offset calculation.
        
        For each vertex, calculates the bisector of adjacent edges and
        moves the vertex along this bisector by the offset distance.
        
        Args:
            oldX, oldY: Original coordinates
            offset: Distance to offset
            outer_ccw: Direction modifier (1 for CCW polygons, -1 for CW)
        """
        num_points = len(oldX)

        for curr in range(num_points):
            prev = (curr + num_points - 1) % num_points
            next = (curr + 1) % num_points
            
            # Normalize edge vectors from current to next vertex, and their perpendicular
            vnX =  oldX[next] - oldX[curr]
            vnY =  oldY[next] - oldY[curr]
            vnnX, vnnY = normalizeVec(vnX,vnY)
            nnnX = vnnY
            nnnY = -vnnX
            
            # Normalize edge vectors from current to next vertex, and their perpendicular
            vpX =  oldX[curr] - oldX[prev]
            vpY =  oldY[curr] - oldY[prev]
            vpnX, vpnY = normalizeVec(vpX,vpY)
            npnX = vpnY * outer_ccw
            npnY = -vpnX * outer_ccw
            
            # Calculate and normalize the bisector.
            bisX = (nnnX + npnX) * outer_ccw
            bisY = (nnnY + npnY) * outer_ccw

            bisnX, bisnY = normalizeVec(bisX,  bisY)
            bislen = offset /  np.sqrt(1 + nnnX*npnX + nnnY*npnY)
            
            # Move along the bisector
            newX.append(oldX[curr] + bislen * bisnX)
            newY.append(oldY[curr] + bislen * bisnY)
    makeOffsetPoly(x, y, offset)
    return newX, newY
  
def generate_new_polygon(HA_geometry):
    """
    Create a new polygon by offsetting (shrinking) the input polygon.
    
    Args:
        HA_geometry: Original polygon geometry
        
    Returns:
        New polygon geometry offset inward by 0.0001 degrees,
        or original geometry if processing fails
    """
    try:
        if HA_geometry.geom_type == 'Polygon':
            # Extract x and y coordinates from polygon exterior
            x = list(HA_geometry.exterior.coords.xy[0])
            y = list(HA_geometry.exterior.coords.xy[1])
            x.pop(-1)
            y.pop(-1)
        
            # Apply
            X, Y = get_new_coordinates(x, y, -0.0001)
          
            X.append(X[0])
            Y.append(Y[0])
        
            return geometry.Polygon([[x, y] for x, y in zip(X, Y)])
        elif HA_geometry.geom_type == 'MultiPolygon':
            # Process each polygon in the MultiPolygon
            new_polygons = []
            for polygon in HA_geometry.geoms:
                # Recursively apply the same function to each polygon
                new_polygon = generate_new_polygon(polygon)
                new_polygons.append(new_polygon)
            
            # Create a new MultiPolygon from all offset polygons
            return geometry.MultiPolygon(new_polygons)
    except Exception as e:
        # Log warning if offsetting fails
        warning_msg = f"Offsetting failed for polygon. Using original geometry. Error: {str(e)}"
        warnings.warn(warning_msg)
        return HA_geometry
      
### MAIN SCRIPT BODY

data_path = os.path.join(root_dir, 'input_data')


# 1. LOAD POLYGON DATA
# Read shapefile containing homogeneous area polygons
gdf_HA = gpd.read_file(os.path.join(data_path, 'geodatasets', 'homogeneous_areas', 'gran_stgoPolygon.shp'))

# 2. REPROJECT DATA
# Convert to WGS84 (EPSG:4326) for geographic coordinates in degrees
gdf_HA = gdf_HA.to_crs("EPSG:4326")

# 3. PRESERVE ORIGINAL GEOMETRY
# Store original geometry in a new column before modification
gdf_HA['orginal_geometry'] = gdf_HA['geometry']
#gdf_HA_ori = gdf_HA.copy()
#gdf_HA_ori['geometry'].to_file(os.path.join(data_path, 'geodatasets', 'homogeneous_areas', 'gran_stgoPolygonori.shp'))

# 4. CREATE OFFSET POLYGONS
# Apply inward buffering to all polygons to prevent overlaps
gdf_HA['geometry'] = gdf_HA['geometry'].apply(generate_new_polygon)
#gdf_HA['geometry'].to_file(os.path.join(data_path, 'geodatasets', 'homogeneous_areas', 'gran_stgoPolygonnew.shp'))


# 5. FIND INTERSECTING/ADJOINING POLYGONS
# Perform spatial self-join to find which polygons intersect each other
gdf_intersect = gpd.sjoin(gdf_HA, gdf_HA, how='left', predicate='intersects')

# 6. REMOVE SELF-INTERSECTIONS
# Filter out rows where a polygon is joined with itself
gdf_intersect = gdf_intersect[~(gdf_intersect['CMN_AH_left']==gdf_intersect['CMN_AH_right'])]

# 7. PREPARE ADJACENCY DATA
# Extract only the polygon ID columns and rename them for clarity
df_intersect = gdf_intersect[['CMN_AH_left', 'CMN_AH_right']].rename(
      columns={'CMN_AH_left': 'CMN_AH', 'CMN_AH_right': 'CMN_AH_neighbour'}
  )


df_intersect = df_intersect.dropna()

# 8. DEBUG/VERIFICATION (optional line)
# Check adjacency for a specific polygon ID (16110-CMB017)
df_intersect[df_intersect['CMN_AH']=='16110-CMB017']

# 9. SAVE RESULTS
# Export adjacency list to CSV file
df_intersect.to_csv(os.path.join(data_path, 'datasets', 'adjoining_HA.csv'), index=False)


