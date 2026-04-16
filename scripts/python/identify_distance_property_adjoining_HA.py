import os
import warnings

try:
    root_dir = config['root_dir']
except (NameError, KeyError):
    # Fallback: assume script is in project_root/python/
    # and navigate up one level to the project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    warnings.warn(f"root_dir not provided by R. Using fallback: {root_dir}")

    
desired_comunes = [14166, 14156, 14201, 14127, 16165, 14157, 14158, 13167, 16110, 15128, 16131, 16154, 15132, 15108, 15161, 16164, 14155, 15151, 14109, 15105, 16162, 15152, 15103, 14111, 16301, 14114, 14107, 13159, 14113, 16401, 16163, 16106, 16153, 13101, 13134, 13135, 15160]

# Open coordenates
data_path = os.path.join(root_dir, 'raw')
df_coordenates = pd.read_csv(os.path.join(data_path, 'sii_roles_coordinates.csv'))

# coordenates to geographic file
df_coordenates = df_coordenates[df_coordenates['cod_com'].isin(desired_comunes)]
gdf_coordenates = gpd.GeoDataFrame(df_coordenates, geometry=gpd.points_from_xy(df_coordenates.longitud, df_coordenates.latitud))
gdf_coordenates.crs = "EPSG:4326"

# Homogeneous Areas
gdf_HA = gpd.read_file(os.path.join(data_path, 'homogeneous_areas', 'gran_stgoPolygon.shp'))
gdf_HA = gdf_HA[gdf_HA['COMUNA'].isin(desired_comunes)]
gdf_HA = gdf_HA.to_crs("EPSG:4326")


# Homogeneous Areas for Roles
path = os.path.join(data_path, 'homogeneaous_area_roles')
data = {}
for file_name in tqdm(os.listdir(path)):
    with open(os.path.join(path, file_name), 'r') as fp:
        data.update(json.load(fp))
    break

data_HA = {}
for key, value in data.items():
    try:
        HA = value['data']['ah']
        data_HA.update({key: {'AH': HA}})
    except:
        pass

df_HA_roles = pd.DataFrame.from_dict(data_HA, orient='index')

# graph
g_points = gdf_coordenates[(gdf_coordenates['latitud']>-40) & (gdf_coordenates['longitud']<80)]
g_area = gdf_HA 

g_area.to_file(os.path.join(root_dir, 'data_channel', "g_area.shp"))
g_points.to_file(os.path.join(root_dir, 'data_channel', "g_points.shp"))




