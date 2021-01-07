
# coding: utf-8

# In[1]:


import pandas as pd
import geopandas as gpd
import os
import requests
import zipfile
from shapely.geometry import Point, LineString, Polygon, shape
import shapefile
import folium


# In[45]:


trips = pd.read_csv('google_transit_urbano_tte/trips.txt')
shapes = pd.read_csv('google_transit_urbano_tte/shapes.txt')
routes = pd.read_csv('google_transit_urbano_tte/routes.txt')
stops = pd.read_csv('google_transit_urbano_tte/stops.txt')
stop_times = pd.read_csv("google_transit_urbano_tte/stop_times.txt")
calendar = pd.read_csv("google_transit_urbano_tte/calendar.txt")


# In[3]:


gtfs_TN = 'gtfs_TN.zip'


# In[4]:


gtfszip = zipfile.ZipFile(gtfs_TN, mode='w')
try:
    gtfszip.write('google_transit_urbano_tte/routes.txt')
    gtfszip.write('google_transit_urbano_tte/trips.txt')
    gtfszip.write('google_transit_urbano_tte/shapes.txt')
    gtfszip.write('google_transit_urbano_tte/agency.txt')
    gtfszip.write('google_transit_urbano_tte/calendar.txt')
    gtfszip.write('google_transit_urbano_tte/calendar_dates.txt')
    gtfszip.write('google_transit_urbano_tte/stops.txt')
    gtfszip.write('google_transit_urbano_tte/stop_times.txt')
finally:
    gtfszip.close()


# # Select only buses in Trento

# In[5]:


geometry = [Point(xy) for xy in zip(stops.stop_lon, stops.stop_lat)]
crs = {'init': 'epsg:4326'}
stops = gpd.GeoDataFrame(stops, crs=crs, geometry=geometry)


# In[6]:


fname = "poli_sociali/poli_sociali.shp"
poli = gpd.read_file(fname)


# In[7]:


poli = poli.to_crs({'init': 'epsg:4326'})


# In[8]:


area_stops = poli.iloc[:, [2,10]]


# In[9]:


routes


# ## stops' selection

# In[10]:


idx_stops_povo = []
for index, row in stops.iterrows():
    for idx, area in area_stops.iterrows():
        if row.geometry.within(area.geometry):
            idx_stops_povo.append(index)
            break


# In[11]:


stops_TN = stops[stops.index.isin(idx_stops_povo)]
stops_TN.head()


# ## stopstimes' selection

# In[12]:


stoptime_TN = stop_times[stop_times.stop_id.isin(stops_TN.stop_id.values)]


# ## trips' selection

# In[13]:


trips_num = list(stoptime_TN.trip_id.unique())


# In[14]:


trip_TN = trips[trips.trip_id.isin(trips_num)]


# ## routes' selection
# 
# 

# In[15]:


routes_num = list(trip_TN.route_id.unique())


# In[16]:


route_TN = routes[routes.route_id.isin(routes_num)]
route_TN.index= range(len(route_TN))


# In[17]:


povo = ['Povo' in route_TN['route_long_name'][i] for i in range(len(route_TN))]


# In[18]:


route_Povo = route_TN[povo]


# In[19]:


route_Povo


# In[23]:


# seleziono prima le trip del 5 e 5 barra e poi quella del 13
route5 = [400, 535]
route13 = [466]


# In[38]:


trip_Povo.head()


# In[46]:


calendar


# In[58]:


trip_povo = trip_TN[trip_TN.service_id.isin([92019091220200610])]


# In[59]:


trip_povo = trip_povo[trip_TN.route_id.isin(route5)]
shape_id_Povo = trip_povo.shape_id.unique()


# In[60]:


shape_id_Povo


# In[61]:


shape_povo = shapes[shapes.shape_id.isin(['D302_F0501a_Andata_sub2'])]


# In[62]:


shape_povo.to_csv('shape_povo.txt')


# In[25]:


# selezionare le trip e le shape in base a route
# plottare su cartodb in base a numero di diverso colore

#https://stanmart.github.io/geodata/datashader/python/plotting/budapest/2018/10/17/bkk-datashader/


# In[26]:


# count number of routes for each shape


# In[27]:


num_trips_by_shape = trip_Povo.groupby('shape_id').aggregate({'route_id': 'count'}).reset_index()
num_trips_by_shape.rename({'route_id': 'trip_count'}, axis='columns', inplace=True)

shapes_with_nums = shapes.merge(num_trips_by_shape, on='shape_id')
shapes_with_nums.head()


# In[28]:


from datashader.utils import lnglat_to_meters
import numpy as np

shapes_with_nums['coord_x'], shapes_with_nums['coord_y'] =     lnglat_to_meters(shapes_with_nums['shape_pt_lon'], shapes_with_nums['shape_pt_lat'])

def split_df_by(df, byvar):
    df_parts = []
    for level, df_part in df.groupby(byvar):
        empty = pd.DataFrame([[level if colname == byvar else np.NaN for colname in df.columns]],
                             columns=df.columns)
        df_parts.append(df_part.append(empty))
    return pd.concat(df_parts) 

sep_shapes = split_df_by(shapes_with_nums, 'shape_id')


# In[29]:


import bokeh.plotting as bp
from bokeh.models.tiles import WMTSTileSource
import datashader as ds
import datashader.transfer_functions as tf
from datashader.bokeh_ext import InteractiveImage
from datashader.utils import export_image
import colorcet as cc

bp.output_notebook()


# In[30]:


x_range=(sep_shapes.coord_x.min(), sep_shapes.coord_x.max())
y_range=(sep_shapes.coord_y.min(), sep_shapes.coord_y.max())


# In[31]:


p = bp.figure(tools='pan,wheel_zoom,box_zoom,save,reset',
              plot_width=int(600),
              plot_height=int(600),
              x_range=x_range,
              y_range=y_range)


# In[35]:


from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html

p.add_tile(CARTODBPOSITRON)

def image_callback(x_range, y_range, w, h, color_fn=tf.shade):
    cvs = ds.Canvas(plot_width=w, plot_height=h, x_range=x_range, y_range=y_range)
    agg = cvs.line(sep_shapes, 'coord_x', 'coord_y')
    image = tf.shade(agg, cmap=cc.fire, how='eq_hist')
    return image

export_image(image_callback(x_range=x_range, y_range=y_range, w=2000, h=2000),
             filename="TRENTOschedule_fire")
plot = InteractiveImage(p, image_callback)

# https://github.com/holoviz/datashader/issues/193 non si può salvare in html datashader

# https://towardsdatascience.com/exploring-and-visualizing-chicago-transit-data-using-pandas-and-bokeh-part-ii-intro-to-bokeh-5dca6c5ced10


# In[36]:


plot

