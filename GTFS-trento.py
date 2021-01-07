
# coding: utf-8

# ## Data upload

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')
import pandas as pd
import geopandas as gpd
import os
import requests
import zipfile
from shapely.geometry import Point, LineString, Polygon
import shapely
import folium


# In[2]:


gtfdir='gtfs'
zipfilegtfs = 'google_transit_urbano_tte.zip'
urlzip = 'https://www.trentinotrasporti.it/opendata/google_transit_urbano_tte.zip'


# In[3]:


if not os.path.exists(gtfdir):
    os.mkdir(gtfdir)


# In[4]:


r = requests.get(urlzip,allow_redirects=True)
open(zipfilegtfs, 'wb').write(r.content)


# In[5]:


with zipfile.ZipFile(zipfilegtfs,"r") as zip_ref:
    zip_ref.extractall(gtfdir)


# ### GTFS: upload

# In[6]:


stops = pd.read_csv(gtfdir + os.sep + 'stops.txt')
stop_times = pd.read_csv(gtfdir + os.sep + "stop_times.txt")
trips = pd.read_csv(gtfdir + os.sep + "trips.txt")
routes = pd.read_csv(gtfdir + os.sep + "routes.txt")
agency = pd.read_csv(gtfdir + os.sep + "agency.txt")
shapes = pd.read_csv(gtfdir + os.sep + "shapes.txt")
calendar = pd.read_csv(gtfdir + os.sep + 'calendar.txt')
calendar_dates = pd.read_csv(gtfdir + os.sep + "calendar_dates.txt")
transfers = pd.read_csv(gtfdir + os.sep + "transfers.txt")


# In[7]:


routes.to_csv('routes.txt',index=False)
trips.to_csv("trips.txt",index=False)
shapes.to_csv('shapes.txt',index=False)
agency.to_csv('agency.txt',index=False)
calendar.to_csv('calendar.txt',index=False)
calendar_dates.to_csv('calendar_dates.txt',index=False)


# ### Zip file

# In[8]:


gtfs_trento = 'gtfs_trento.zip'


# In[9]:


zf = zipfile.ZipFile(gtfs_trento, mode='w')
try:
    zf.write('routes.txt')
    zf.write('trips.txt')
    zf.write('shapes.txt')
    zf.write('agency.txt')
    zf.write('calendar.txt')
    zf.write('calendar_dates.txt')
    zf.write('stops.txt')
    zf.write('stop_times.txt')
finally:
    zf.close()


# ## Analysis: selecting routes that go to the Povo Area

# ### upload shape file of analysed zone

# In[10]:


import geopandas as gpd


# In[11]:


fname = "shape_povo.geojson"
povo = gpd.read_file(fname)


# In[12]:


geometry = [Point(xy) for xy in zip(stops.stop_lon, stops.stop_lat)]
crs = {'init': 'epsg:4326'}
stops = gpd.GeoDataFrame(stops, crs=crs, geometry=geometry)


# In[13]:


povo = povo.to_crs({'init': 'epsg:4326'})


# In[14]:


p = povo.geometry
id = int(povo.index[0])
p = p[id]


# ### intersection stops and POVO

# In[15]:


area_fermate = povo.iloc[:, [2,10]]
area_fermate


# In[16]:


idx_stops_povo = []
for index, row in stops.iterrows():
    for idx, area in area_fermate.iterrows():
        if row.geometry.within(area.geometry):
            idx_stops_povo.append(index)
            break


# In[17]:


stops_area = stops[stops.index.isin(idx_stops_povo)]
stops_area.head()


# In[18]:


x= stops_area.unary_union.envelope.centroid.x
y = stops_area.unary_union.envelope.centroid.y
m = folium.Map([y,x], zoom_start=14, tiles="OpenStreetMap")
folium.GeoJson(stops_area.to_json()).add_to(m)
m


# In[19]:


stops_area.stop_id.values


# In[20]:


stops_times_area = stop_times[stop_times.stop_id.isin(stops_area.stop_id.values)]


# In[21]:


trip_id_area = stops_times_area.trip_id.unique()


# In[22]:


trip_id_area = list(trip_id_area)


# In[23]:


trips_area = trips[trips.trip_id.isin(trip_id_area)]
trips_area.head()


# In[24]:


routeids = list(trips_area.route_id.unique())


# In[25]:


routeids


# In[26]:


routes_area = routes[routes.route_id.isin(routeids)]
routes_area


# Quite a considerable number of buses go to Povo.
# Anyway, the aim is to check the crowded number 5, which is the bus that students use the most.  
# For the preliminary analysis, also the route of bus 13 is analysed, in order to understand why students prefer not to use it.

# In[27]:


routes_area.index=range(0,len(routes_area))


# ### Analysis of the number 13

# In[28]:


routes_area13 = routes_area[routes_area['route_short_name'].isin(['13'])]


# In[29]:


routes_area13


# The bus 13 has only one route id: route_id=466.  
# Anyway, the next steps keep the code general in order to be able to analyse also bus route with different trips.

# In[30]:


route_ids_13 = routes_area13.route_id.unique()


# In[31]:


route_ids_13 = list(route_ids_13)


# In[32]:


trips_area_13 = trips[trips.route_id.isin(route_ids_13)]
trips_area_13.head()


# In[33]:


trip_id_for_stops13 = trips_area_13.trip_id.unique()


# In[34]:


trip_id_for_stops13 = list(trip_id_for_stops13)


# In[35]:


stop_times_linea13 = stop_times[stop_times.trip_id.isin(trip_id_for_stops13)]
stop_times_linea13.head()


# In[36]:


stop_id_linea13 = list(stop_times_linea13.stop_id.unique())


# In[37]:


stops_linea13 = stops[stops.stop_id.isin(stop_id_linea13)]


# In[38]:


x= stops_linea13.unary_union.envelope.centroid.x
y = stops_linea13.unary_union.envelope.centroid.y
trento_bus13 = folium.Map([y,x], zoom_start=14, tiles="OpenStreetMap")
folium.GeoJson(stops_linea13.to_json()).add_to(trento_bus13)
trento_bus13


# In[39]:


andata = trips_area_13['direction_id'] == 0
trips_13_andata = trips_area_13[andata]


# In[40]:


service_id13 = list(trips_13_andata.service_id.unique()) 
service_id13


# In[41]:


trips_13_andata_feriale = trips_13_andata[trips_13_andata.service_id.isin(service_id13)]
# trips_13_andata_feriale


# In[42]:


# select only one trip station-Povo 

trips_ids = [trips_13_andata_feriale['trip_id'][753]]


# In[43]:


trips_ids = list(trips_ids)
trips_ids


# In[44]:


stop_13_andata_fer = stop_times_linea13[stop_times_linea13.trip_id.isin(trips_ids)]


# In[45]:


# stop_13_andata_fer


# As we can see, the bus 13 has two main disadvantages. First of all, as can be see in the map 'trento_bus13', the trips is way longer than the one of bus number 5 and 5/ (trento_bus5). Also, the duration of the trip is around 40 min (as we can see by displaying 'stop_13_andata_fer'). On the other hand, the duration of the buses 5 and 5/ is way shorter (paragraph 5.1).

# In[46]:


#stop_13_andata_fer


# ### Analysis of number 5

# In[47]:


routes_area5 = routes_area[routes_area['route_short_name'].isin(['5'])]


# In[48]:


routes_area5


# #### selecting the trips of lines 5

# In[49]:


route_ids_5 = routes_area5.route_id.unique()


# In[50]:


route_ids_5 = list(route_ids_5)


# In[51]:


route_ids_5


# In[52]:


trips_area_5 = trips[trips.route_id.isin(route_ids_5)]
trips_area_5.head()


# #### getting all the stops of these trips

# In[53]:


trip_id_for_stops5 = trips_area_5.trip_id.unique()


# In[54]:


trip_id_for_stops5 = list(trip_id_for_stops5)


# In[55]:


stop_times_linea5 = stop_times[stop_times.trip_id.isin(trip_id_for_stops5)]
stop_times_linea5.head()


# In[56]:


stop_id_linea5 = list(stop_times_linea5.stop_id.unique())


# In[57]:


stops_linea5 = stops[stops.stop_id.isin(stop_id_linea5)]


# In[58]:


x= stops_linea5.unary_union.envelope.centroid.x
y = stops_linea5.unary_union.envelope.centroid.y
trento_bus5 = folium.Map([y,x], zoom_start=14, tiles="OpenStreetMap")
folium.GeoJson(stops_linea5.to_json()).add_to(trento_bus5)
trento_bus5


# ### Analysis of number 5/ : get trips and stops 

# In[59]:


routes_area5barra = routes_area[routes_area['route_id'].isin(['535'])]
routes_area5barra
route_ids_5barra = routes_area5barra.route_id.unique()
route_ids_5barra = list(route_ids_5barra)


# In[60]:


trips_area_5barra = trips[trips.route_id.isin(route_ids_5barra)]


# In[61]:


trip_id_for_stops5barra = trips_area_5barra.trip_id.unique()
trip_id_for_stops5barra = list(trip_id_for_stops5barra)


# In[62]:


stop_times_linea5barra = stop_times[stop_times.trip_id.isin(trip_id_for_stops5barra)]
#stop_times_linea5barra.head()
stop_id_linea5barra = list(stop_times_linea5barra.stop_id.unique())
stops_linea5barra = stops[stops.stop_id.isin(stop_id_linea5barra)]


# In[63]:


x= stops_linea5barra.unary_union.envelope.centroid.x
y = stops_linea5barra.unary_union.envelope.centroid.y
trento_bus5barra = folium.Map([y,x], zoom_start=14, tiles="OpenStreetMap")
folium.GeoJson(stops_linea5barra.to_json()).add_to(trento_bus5barra)
trento_bus5barra


# In[64]:


ritornobarra = trips_area_5barra['direction_id'] == 1
ritornobarra


# As you can see from the map and from the code, bus number 5/ only goes from the city center to Povo. 

# ### zip file with the new datasets with districts: 5 and 5/

# #### bus 5

# In[65]:


routeids = list(trips_area_5.route_id.unique())
routes_area = routes[routes.route_id.isin(routeids)]
agencyids = list(routes_area.agency_id.unique())
agency_area = agency[agency.isin(agencyids)]
shapeids = list(trips_area_5.shape_id.unique())
shapes_area = shapes[shapes.shape_id.isin(shapeids)]
transfers_area=transfers[transfers.from_stop_id.isin(stop_id_linea5 )]
transfers_area=transfers[transfers.to_stop_id.isin(stop_id_linea5 )]


# In[66]:


stop_times_linea5.to_csv("stop_times.txt",index=False)


# In[67]:


stops_linea5.head()


# In[68]:


stops_linea5.crs


# In[69]:


stops_linea5.head()


# In[70]:


stops_linea5.index=range(0,len(stops_linea5))


# In[71]:


# zone_id is the same for all the stops of the subset
# 'poli.shp' usee to give to all the stops the corresponding district


# In[72]:


import shapefile
from shapely.geometry import Point 
from shapely.geometry import shape
from shapely.geometry.polygon import Polygon


# In[73]:


fname = "poli_sociali.shp"

poli = gpd.read_file(fname)
poli.head()


# In[74]:


print(poli.crs)
print(stops_linea5.crs)


# In[75]:


poli = poli.to_crs({'init': 'epsg:4326'})
poli.head()


# In[76]:


quartiere = [0 for i in range(0, len(stops_linea5))]
for i in range(0, len(stops_linea5)):
    point= stops_linea5['geometry'][i]
    for j in range(0, len(poli)):
        quart = poli['nome_quart'][j]
        polygon = poli['geometry'][j]
        if polygon.contains(point): 
            quartiere[i] = quart


# In[77]:


stops_linea5['quartiere'] = quartiere


# In[78]:


stops_linea5.head()


# In[79]:


stops_linea5.drop(columns=['geometry']).to_csv('stops.txt',index=False)


# In[80]:


routes_area.to_csv('routes.txt',index=False)
trips_area.to_csv("trips.txt",index=False)
shapes_area.to_csv('shapes.txt',index=False)
agency.to_csv('agency.txt',index=False)
calendar.to_csv('calendar.txt',index=False)
calendar_dates.to_csv('calendar_dates.txt',index=False)


# In[81]:


gtfs_povo5 = 'gtfs_linea_5.zip'


# In[82]:


zf = zipfile.ZipFile(gtfs_povo5, mode='w')
try:
    zf.write('routes.txt')
    zf.write('trips.txt')
    zf.write('shapes.txt')
    zf.write('agency.txt')
    zf.write('calendar.txt')
    zf.write('calendar_dates.txt')
    zf.write('stops.txt')
    zf.write('stop_times.txt')
finally:
    zf.close()


# #### Bus 5/

# In[83]:


routeids = list(trips_area_5barra.route_id.unique())
routes_area = routes[routes.route_id.isin(routeids)]
agencyids = list(routes_area.agency_id.unique())
agency_area = agency[agency.isin(agencyids)]
shapeids = list(trips_area_5barra.shape_id.unique())
shapes_area = shapes[shapes.shape_id.isin(shapeids)]
transfers_area=transfers[transfers.from_stop_id.isin(stop_id_linea5barra )]
transfers_area=transfers[transfers.to_stop_id.isin(stop_id_linea5barra )]


# In[84]:


stop_times_linea5barra.to_csv("stop_times.txt",index=False)


# In[85]:


stops_linea5barra.index=range(0,len(stops_linea5barra))


# In[86]:


quartiere = [0 for i in range(0, len(stops_linea5barra))]
for i in range(0, len(stops_linea5barra)):
    point= stops_linea5barra['geometry'][i]
    for j in range(0, len(poli)):
        quart = poli['nome_quart'][j]
        polygon = poli['geometry'][j]
        if polygon.contains(point): 
            quartiere[i] = quart


# In[87]:


stops_linea5barra['quartiere'] = quartiere


# In[88]:


stops_linea5barra.drop(columns=['geometry']).to_csv('stops.txt',index=False)


# In[89]:


routes_area.to_csv('routes.txt',index=False)
trips_area.to_csv("trips.txt",index=False)
shapes_area.to_csv('shapes.txt',index=False)
agency.to_csv('agency.txt',index=False)
calendar.to_csv('calendar.txt',index=False)
calendar_dates.to_csv('calendar_dates.txt',index=False)


# In[90]:


gtfs_povo5barra = 'gtfs_linea_5barra.zip'


# In[91]:


zf = zipfile.ZipFile(gtfs_povo5barra, mode='w')
try:
    zf.write('routes.txt')
    zf.write('trips.txt')
    zf.write('shapes.txt')
    zf.write('agency.txt')
    zf.write('calendar.txt')
    zf.write('calendar_dates.txt')
    zf.write('stops.txt')
    zf.write('stop_times.txt')
finally:
    zf.close()


# ## Check the number of bus passing in a stop

# Seelcting the way going, in order to get the list of stops with name and time.  
# The aim is to check which stops are important nodes.

# In[92]:


### route 5


# In[93]:


andata = trips_area_5['direction_id'] == 0


# In[94]:


trips_5_andata = trips_area_5[andata]
service = [92019091220200610, 662019091220200610, 672019091220200610]
# I selected services that work during week days in school period.


# In[95]:


trips_5_andata_feriale = trips_5_andata[trips_5_andata.service_id.isin(service)]


# In[96]:


trips_ids = [trips_5_andata_feriale['trip_id'][882]]


# In[97]:


trips_ids = list(trips_ids)
trips_ids


# In[98]:


stop_5_andata_fer = stop_times_linea5[stop_times_linea5.trip_id.isin(trips_ids)]


# In[99]:


# stop_5_andata_fer
#fermate del 5


# In[100]:


stop_id_andata = list(stop_5_andata_fer.stop_id.unique())
# stop_id_andata


# In[101]:


def bus_per_stop(numero_linea, stop_times, trips, routes):

    stops_times_area_id = stop_times['stop_id'] == numero_linea
    stops_times_area = stop_times[stops_times_area_id]
    trip_id_area = stops_times_area.trip_id.unique()
    trip_id_area = list(trip_id_area)
    trips_area = trips[trips.trip_id.isin(trip_id_area)]
    routeids = list(trips_area.route_id.unique())
    routes_area = routes[routes.route_id.isin(routeids)]
    return(list(routes_area['route_short_name']))


# In[102]:


stops = pd.read_csv(gtfdir + os.sep + 'stops.txt')
stop_times = pd.read_csv(gtfdir + os.sep + "stop_times.txt")
trips = pd.read_csv(gtfdir + os.sep + "trips.txt")
routes = pd.read_csv(gtfdir + os.sep + "routes.txt")


# In[103]:


bus_stop5 = dict()


# In[104]:


for numero in stop_id_andata:
    
    bus_stop5[numero] = bus_per_stop(numero, stop_times, trips, routes)


# In[105]:


fermate_nodo5 = []
for key in bus_stop5:
    if len(bus_stop5[key]) > 6:
        fermate_nodo5.append(key)


# In[106]:


fermate_nodo5


# In[107]:


fermate5 = stops[stops.stop_id.isin(fermate_nodo5)]
fermate5


# Considering the stops ith higer number of buses, we have that the main nodes are in the station, in Rosmini (which is right after station, so all the buses are just continuing from there) piazza Fiera and S. Francesco. The analysis of stops will then focus on this hotspots.

# In[108]:


### route 5/


# In[109]:


andatabarra = trips_area_5barra['direction_id'] == 0


# In[110]:


trips_5barra_andata = trips_area_5barra[andatabarra]
service = [92019091220200610, 662019091220200610, 672019091220200610]


# In[111]:


trips_5barra_andata_feriale = trips_5barra_andata[trips_5barra_andata.service_id.isin(service)]


# In[112]:


trips_idsbarra = [trips_5barra_andata_feriale['trip_id'][1141]]
trips_idsbarra


# In[113]:


trips_idsbarra = list(trips_idsbarra)
trips_idsbarra


# In[114]:


# stops of r
stop_5barra_andata_fer = stop_times_linea5barra[stop_times_linea5barra.trip_id.isin(trips_idsbarra)]
# stop_5_andata_fer


# In[115]:


stop_id_andatabarra = list(stop_5barra_andata_fer.stop_id.unique())


# In[116]:


bus_stop5barra = dict()


# In[117]:


for numero in stop_id_andatabarra:
    
    bus_stop5barra[numero] = bus_per_stop(numero, stop_times, trips, routes)


# In[118]:


# bus_stop5barra


# In[119]:


fermate_nodo5barra = []
for key in bus_stop5barra:
    if len(bus_stop5barra[key]) > 6:
        fermate_nodo5barra.append(key)


# In[120]:


fermate_5barra = stops[stops.stop_id.isin(fermate_nodo5barra)] 
fermate_5barra


# ## Selected stops: arrival and departure
# 
# - Train Station
# - P. Fiera
# - Povo Valoni
# - Povo Fac. Scientifiche 

# ### DATA FOR BUS 5

# In[121]:


import seaborn as sns
import matplotlib.pyplot as plt
import partridge as ptg
import datetime
get_ipython().run_line_magic('matplotlib', 'inline')
plt.rcParams['figure.figsize'] = (10, 5) # set default size of plots

get_ipython().run_line_magic('matplotlib', 'inline')
plt.rcParams['figure.figsize'] = (10, 5) # set default size of plots

sns.set(style="white", rc={"axes.facecolor": (1, 1, 1, 0)})
sns.set_context("talk")
sns.set_palette('Set2', 10)


# In[122]:


gtfs_povo5 = 'gtfs_linea_5.zip'


# In[123]:


_date, service_ids = ptg.read_busiest_date(gtfs_povo5)

view = {
    'trips.txt': {'service_id': service_ids},
}
feed_5 = ptg.load_feed(gtfs_povo5, view)


# In[124]:


feed_5 = ptg.load_feed(gtfs_povo5, view)


# In[125]:


s_linea5 = feed_5.stops
s_linea5.head()


# In[126]:


zones = feed_5.stops[['stop_code','quartiere']].drop_duplicates()


# In[127]:


zones.head()


# In[128]:


stop_times.head()


# In[129]:


# for departure_time


# In[130]:


def to_timedelta(df):
    '''
    Turn time columns into timedelta dtype
    '''
    cols = ['departure_time']
    numeric = df[cols].apply(pd.to_timedelta, unit='s')
    df = df.copy()
    df[cols] = numeric
    return df

fermate5_part = (feed_5.stop_times[['trip_id', 'departure_time', 'stop_id']]
     .assign(date = datetime.date(2020, 3, 23))
     .merge(s_linea5[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'stop_code']], on='stop_id')
     # Much faster joins and slices with Categorical dtypes
     .merge(zones, how='left')
     .assign(zone_name=lambda x: pd.Categorical(x['quartiere']))
     .pipe(to_timedelta)
    )
fermate5_part.head()


# In[131]:


fermate5_part.to_csv("bus5_partenze_pdante.csv",index=True)


# In[132]:


# for arrival time


# In[133]:


def to_timedelta(df):
    '''
    Turn time columns into timedelta dtype
    '''
    cols = ['arrival_time']
    numeric = df[cols].apply(pd.to_timedelta, unit='s')
    df = df.copy()
    df[cols] = numeric
    return df

fermate5_arr = (feed_5.stop_times[['trip_id', 'arrival_time', 'stop_id']]
     .assign(date = datetime.date(2020, 3, 23))
     .merge(s_linea5[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'stop_code']], on='stop_id')
     # Much faster joins and slices with Categorical dtypes
     .merge(zones, how='left')
     .assign(zone_name=lambda x: pd.Categorical(x['quartiere']))
     .pipe(to_timedelta)
    )
fermate5_arr.head()


# As mentioned, I'm interested in the following stops:
# 
# For the way going to the hill:
# - Train Station ('Piazza Dante "Stazione Fs"')
# - Piazza Fiera (''Piazza di Fiera'')
# - 'Povo "Fac. Scienze"' 
# 
# For the coming back:
# - 'Povo Valoni'
# - Train Station ('Piazza Dante "Stazione Fs"')

# #### Going to Povo 

# In[ ]:


### Train Station


# In[ ]:


train = fermate5_part['stop_name'] == 'Piazza Dante "Stazione Fs"'
f_train = fermate5_part[train]


# In[ ]:


f_train


# In[ ]:


#f_partenze_staz = f_train.set_index(['departure_time'])
f_partenze_staz = f_train.set_index(['departure_time']).resample('10T')


# In[ ]:


fig = f_partenze_staz.size().plot() 
sns.despine()


# In[ ]:


f_partenze_staz.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_t = f_partenze_staz.size().reset_index().rename(columns={0: 'partenze bus'})
counts_t = counts_t.set_index('departure_time')
counts_t.head()


# In[ ]:


counts_t['departure'] = counts_t.index
counts_t.index=range(0,len(counts_t))


# In[ ]:


#counts_t


# In[ ]:


counts_t.to_csv("partenze_stazione.txt",index=True)


# In[ ]:


dataset_linechart_5 = pd.read_csv('partenze_stazione.txt', sep=',')
dataset_linechart_5.head()


# In[ ]:


dataset_linechart_5 = dataset_linechart_5.iloc[:, 1:3]
dataset_linechart_5['type'] = ''


# In[ ]:


for i in range(0,len(dataset_linechart_5)):
    stringa = str(dataset_linechart_5['departure'][i])
    stringa = stringa[7:(len(stringa)-10)]
    dataset_linechart_5['departure'][i] = stringa
    dataset_linechart_5['type'][i] = 'bus5'


# In[ ]:


dataset_linechart_5.to_csv("partenze_stazione.txt",index=True)


# In[ ]:


trasporti = pd.read_csv('mobilita_trento.txt', sep=',')


# In[ ]:


trasporti.head()


# In[ ]:


trento_arr = trasporti['arrivo'] == 'Trento'


# In[ ]:


arrivi_trento = trasporti[trento_arr]
arrivi_trento.head()


# In[ ]:


def to_timedelta(df):
    '''
    Turn time columns into timedelta dtype
    '''
    cols = ['ora_arr']
    numeric = df[cols].apply(pd.to_timedelta, unit='s')
    df = df.copy()
    df[cols] = numeric
    return df

staz = to_timedelta(arrivi_trento) 


# In[ ]:


staz.head()


# In[ ]:


stazione_prova = arrivi_trento.pipe(to_timedelta)


# In[ ]:


stazione_prova.to_csv("stazione_arrivi_pdante.csv",index=True)


# In[ ]:


staz = staz.set_index(['ora_arr']).resample('10T')


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_arrivi = staz.size().reset_index().rename(columns={0: 'arrivi stazione'})
counts_arrivi = counts_arrivi.set_index('ora_arr')
counts_arrivi.head()


# In[ ]:


counts_arrivi['arr'] = counts_arrivi.index
counts_arrivi.index=range(0,len(counts_arrivi))


# In[ ]:


#counts_arrivi


# In[ ]:


counts_arrivi.to_csv("arrivi_staz.txt",index=True)


# In[ ]:


dataset_linechart_treni = pd.read_csv('arrivi_staz.txt', sep=',')
dataset_linechart_treni.head()


# In[ ]:


dataset_linechart_treni = dataset_linechart_treni.iloc[:, 1:3]
dataset_linechart_treni['type'] = ''


# In[ ]:


for i in range(0,len(dataset_linechart_treni)):
    stringa = str(dataset_linechart_treni['arr'][i])
    stringa = stringa[7:(len(stringa)-10)]
    dataset_linechart_treni['arr'][i] = stringa
    dataset_linechart_treni['type'][i] = 'train'


# In[ ]:


dataset_linechart_treni.to_csv('arrivi_staz.txt', index=True)


# In[ ]:


import matplotlib.pyplot as plt 

fig, ax = plt.subplots(figsize = (20,10))
counts_t[['partenze bus']].plot(ax = ax)
counts_arrivi[['arrivi stazione']].plot(ax=ax)

ax.set_title('Partenze e arrivi ogni 10 minuti - Piazza Dante Stazione', fontdict = {'fontsize' : '30', 'fontweight' : '3'})
ax.annotate('Fonte Dati: TrentinoTrasporti', xy = (0.80, 0.025), xycoords = 'figure fraction', fontsize = 15, 
            color = '#555555')


start, end = ax.get_xlim()
sns.despine()


# In[ ]:


fig.savefig('train.png')


# In[ ]:


#### Piazza Fiera 


# In[ ]:


pfiera = fermate5_part['stop_name'] == 'Piazza di Fiera'
f_fiera = fermate5_part[pfiera]


# In[ ]:


f_partenze_pfiera = f_fiera.set_index(['departure_time']).resample('10T')
fig = f_partenze_pfiera.size().plot() 
sns.despine()


# In[ ]:


f_partenze_pfiera.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_f = f_partenze_pfiera.size().reset_index().rename(columns={0: 'count'})
counts_f = counts_f.set_index('departure_time')
counts_f.head()


# In[ ]:


counts_f.to_csv("partenze_fiera.txt",index=True)


# In[ ]:


import matplotlib.pyplot as plt 

fig, ax = plt.subplots(figsize = (20,10))
counts_f[['count']].plot(ax = ax)
ax.set_title('Departure in the span of 10min - Piazza Fiera', fontdict = {'fontsize' : '30', 'fontweight' : '3'})
ax.annotate('Source: TrentinoTrasporti', xy = (0.80, 0.025), xycoords = 'figure fraction', fontsize = 15,
           color = '#555555')
sns.despine()


# In[ ]:


fig.savefig('piazza.png')


# In[ ]:


#### Povo Fac. Scientifiche  


# In[ ]:


povo_andata = fermate5_arr['stop_name'] == 'Povo "Fac. Scienze"'
f_povo = fermate5_arr[povo_andata]


# In[ ]:


f_arrivipovo = f_povo.set_index(['arrival_time']).resample('10T')
fig = f_arrivipovo.size().plot() 
sns.despine()


# In[ ]:


f_arrivipovo.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_povo = f_arrivipovo.size().reset_index().rename(columns={0: 'count'})
counts_povo = counts_povo.set_index('arrival_time')
counts_povo.head()


# In[ ]:


counts_povo.to_csv("arrivi_povo.txt",index=True)


# In[ ]:


import matplotlib.pyplot as plt 

fig, ax = plt.subplots(figsize = (20,10))
counts_povo[['count']].plot(ax = ax)
ax.set_title('Bus arriving to Povo in the span of 10min', fontdict = {'fontsize' : '30', 'fontweight' : '3'})
ax.annotate('Source: TrentinoTrasporti', xy = (0.80, 0.025), xycoords = 'figure fraction', fontsize = 15,
           color = '#555555')
sns.despine()


# In[ ]:


fig.savefig('povo_andata.png')


# #### Coming back

# In[ ]:


#### Povo Valoni


# In[ ]:


pvaloni = fermate5_part['stop_name'] == 'Povo Valoni'
f_valoni = fermate5_part[pvaloni]


# In[ ]:


f_valoniritorno = f_valoni.set_index(['departure_time']).resample('10T')
fig = f_valoniritorno.size().plot() 
sns.despine()


# In[ ]:


f_valoniritorno.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_valoni = f_valoniritorno.size().reset_index().rename(columns={0: 'count'})
counts_valoni = counts_valoni.set_index('departure_time')
counts_valoni.head()


# In[ ]:


counts_valoni.to_csv("partenza_valoni.txt",index=True)


# In[ ]:


import matplotlib.pyplot as plt 

fig, ax = plt.subplots(figsize = (20,10))
counts_valoni[['count']].plot(ax = ax)
ax.set_title('Departure in the span of 10min - Povo Valoni', fontdict = {'fontsize' : '30', 'fontweight' : '3'})
ax.annotate('Source: TrentinoTrasporti', xy = (0.80, 0.025), xycoords = 'figure fraction', fontsize = 15,
           color = '#555555')
sns.despine()


# In[ ]:


fig.savefig('povo_ritorno.png')


# In[ ]:


#### Train Station


# In[ ]:


train_ritorno = fermate5_arr['stop_name'] == 'Piazza Dante "Stazione Fs"'
f_train_ritorno = fermate5_arr[train_ritorno]


# In[ ]:


f_arrivistaz = f_train_ritorno.set_index(['arrival_time']).resample('10T')
fig = f_arrivistaz.size().plot() 
sns.despine()


# In[ ]:


f_arrivistaz.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_train_back = f_arrivistaz.size().reset_index().rename(columns={0: 'arrivi bus'})
counts_train_back = counts_train_back.set_index('arrival_time')
counts_train_back.head()


# In[ ]:


counts_train_back.to_csv("arrivi_stazione.txt",index=True)


# In[ ]:


trasporti = pd.read_csv('mobilita_trento.txt', sep=',')


# In[ ]:


trento_part = trasporti['partenza'] == 'Trento'
part_trento = trasporti[trento_part]
part_trento.head()


# In[ ]:


def to_timedelta(df):
    '''
    Turn time columns into timedelta dtype
    '''
    cols = ['ora_part']
    numeric = df[cols].apply(pd.to_timedelta, unit='s')
    df = df.copy()
    df[cols] = numeric
    return df

staz_part = to_timedelta(part_trento) 


# In[ ]:


staz_part = staz_part.set_index(['ora_part']).resample('10T')


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_part = staz_part.size().reset_index().rename(columns={0: 'partenze stazione'})
counts_part = counts_part.set_index('ora_part')
counts_part.head()


# In[ ]:


import matplotlib.pyplot as plt 

fig, ax = plt.subplots(figsize = (20,10))
counts_train_back[['arrivi bus']].plot(ax = ax)
counts_part[['partenze stazione']].plot(ax = ax)

ax.set_title('Arrivi e partenze ogni 10 minuti - Piazza Dante Stazione', fontdict = {'fontsize' : '30', 'fontweight' : '3'})
ax.annotate('Source: TrentinoTrasporti', xy = (0.80, 0.025), xycoords = 'figure fraction', fontsize = 15,
           color = '#555555')
sns.despine()


# In[ ]:


fig.savefig('train_ritorno.png')


# ### DATA FOR BUS 5/

# NB: as already seen in 2.5, 5/ buses only go to Povo. No coming back. Therefore, we are interested in:
# 
# - Train Station ('Piazza Dante "Stazione Fs"')
# - Piazza Fiera (''Piazza di Fiera'')
# - 'Povo "Fac. Scienze"' 

# In[ ]:


gtfs_povo5barra = 'gtfs_linea_5barra.zip'


# In[ ]:


_date, service_ids = ptg.read_busiest_date(gtfs_povo5)

view = {
    'trips.txt': {'service_id': service_ids},
}


# In[ ]:


feed_5barra = ptg.load_feed(gtfs_povo5barra, view)


# In[ ]:


s_linea5barra = feed_5barra.stops
s_linea5barra.head()


# In[ ]:


zones = feed_5barra.stops[['stop_code','quartiere']].drop_duplicates()


# In[ ]:


def to_timedelta(df):
    '''
    Turn time columns into timedelta dtype
    '''
    cols = ['departure_time']
    numeric = df[cols].apply(pd.to_timedelta, unit='s')
    df = df.copy()
    df[cols] = numeric
    return df

fermate5barra = (feed_5barra.stop_times[['trip_id', 'departure_time', 'stop_id']]
     .assign(date = datetime.date(2020, 3, 23))
     .merge(s_linea5barra[['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'stop_code']], on='stop_id')
     # Much faster joins and slices with Categorical dtypes
     .merge(zones, how='left')
     .assign(zone_name=lambda x: pd.Categorical(x['quartiere']))
     .pipe(to_timedelta)
    )
fermate5barra.head()


# In[ ]:


fermate5barra.to_csv("bus5barra_pdante.csv",index=True)


# In[ ]:


trainbarra = fermate5barra['stop_name'] == 'Piazza Dante "Stazione Fs"'
f_train_barra = fermate5barra[trainbarra]


# In[ ]:


f_train_barra.head()


# In[ ]:


f_partenze_staz_barra = f_train_barra.set_index(['departure_time']).resample('10T')


# In[ ]:


f_partenze_staz_barra.size().reset_index().head()


# In[ ]:


from statsmodels.nonparametric.smoothers_lowess import lowess

counts_t_barra = f_partenze_staz_barra.size().reset_index().rename(columns={0: 'partenze bus'})
counts_t_barra = counts_t_barra.set_index('departure_time')
counts_t_barra.head()


# In[ ]:


counts_t_barra['departure'] = counts_t_barra.index
counts_t_barra.index=range(0,len(counts_t_barra))


# In[ ]:


counts_t_barra.to_csv('partenze_5barra.txt', index=True)


# In[ ]:


dataset_linechart = pd.read_csv('partenze_5barra.txt', sep=',')
dataset_linechart.head()


# In[ ]:


dataset_linechart = dataset_linechart.iloc[:, 1:3]
dataset_linechart['type'] = ''


# In[ ]:


for i in range(0,len(dataset_linechart)):
    stringa = str(dataset_linechart['departure'][i])
    stringa = stringa[7:(len(stringa)-10)]
    dataset_linechart['departure'][i] = stringa
    dataset_linechart['type'][i] = 'bus5barra'


# In[ ]:


dataset_linechart.to_csv('partenze_5barra.txt', index=True)


# ## Dataset for linechart union

# In[ ]:


dataline5 = pd.read_csv('partenze_stazione.txt', sep=',')
dataline5barra = pd.read_csv('partenze_5barra.txt', sep=',')
datalinetreni = pd.read_csv('arrivi_staz.txt', sep=',')


# In[ ]:


dataline5 = dataline5.iloc[:, 1:4]
dataline5.rename(columns={'partenze bus':'count',
                          'departure':'h',
                          'type':'type'}, 
                 inplace=True)
dataline5.head()


# In[ ]:


dataline5barra = dataline5barra.iloc[:, 1:4]
dataline5barra.rename(columns={'partenze bus':'count',
                          'departure':'h',
                          'type':'type'}, 
                 inplace=True)
dataline5barra.head()


# In[ ]:


datalinetreni = datalinetreni.iloc[:, 1:4]
datalinetreni.rename(columns={'arrivi stazione':'count',
                          'arr':'h',
                          'type':'type'}, 
                 inplace=True)
datalinetreni.head() 


# ## SanBartolameo Residence: how students go to Povo

# Sanbartolameo hosts more or less 800 students.  
# Therefore, the analysis also consider which bus - either number 5, 5/ or 13 - has the closest stop.

# In[ ]:


sanba_residence = (46.047082, 11.133743)


# ### Bus 13

# In[ ]:


#starting from analysis in of 2.3 


# In[ ]:


stops_linea13.head()


# In[ ]:


stops_linea13.index = range(len(stops_linea13))


# In[ ]:


stops_linea13['coord'] = None
stops_linea13['distance'] = None


# In[ ]:


for i in range (0, len(stops_linea13)):
    stops_linea13['coord'][i] = (stops_linea13['stop_lat'][i], stops_linea13['stop_lon'][i])


# In[ ]:


import pyproj

geod = pyproj.Geod(ellps='WGS84')

for i in range(0, len(stops_linea13)):
    lat0, lon0 = sanba_residence
    lat1, lon1 = stops_linea13['coord'][i] 
    
    azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
    stops_linea13['distance'][i] = distance


# In[ ]:


d = stops_linea13['distance'].min()


# In[ ]:


minimo = stops_linea13['distance'] == d
fermata13_sanba = stops_linea13[minimo]
fermata13_sanba


# ### Bus 5

# In[ ]:


#stops_linea5


# In[ ]:


stops_linea5.index = range(len(stops_linea5))


# In[ ]:


stops_linea5['coord'] = None
stops_linea5['distance'] = None


# In[ ]:


for i in range (0, len(stops_linea5)):
    stops_linea5['coord'][i] = (stops_linea5['stop_lat'][i], stops_linea5['stop_lon'][i])
    
import pyproj

geod = pyproj.Geod(ellps='WGS84')

for i in range(0, len(stops_linea5)):
    lat0, lon0 = sanba_residence
    lat1, lon1 = stops_linea5['coord'][i] 
    
    azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
    stops_linea5['distance'][i] = distance


# In[ ]:


d = stops_linea5['distance'].min()


# In[ ]:


minimo = stops_linea5['distance'] == d
fermata5_sanba = stops_linea5[minimo]
fermata5_sanba


# ### Bus 5barra

# In[ ]:


#stops_linea5barra


# In[ ]:


stops_linea5barra.index = range(len(stops_linea5barra))


# In[ ]:


stops_linea5barra['coord'] = None
stops_linea5barra['distance'] = None


# In[ ]:


for i in range (0, len(stops_linea5barra)):
    stops_linea5barra['coord'][i] = (stops_linea5barra['stop_lat'][i], stops_linea5barra['stop_lon'][i])


# In[ ]:


import pyproj

geod = pyproj.Geod(ellps='WGS84')

for i in range(0, len(stops_linea5barra)):
    lat0, lon0 = sanba_residence
    lat1, lon1 = stops_linea5barra['coord'][i] 
    
    azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
    stops_linea5barra['distance'][i] = distance


# In[ ]:


d = stops_linea5barra['distance'].min()


# In[ ]:


minimo = stops_linea5barra['distance'] == d
fermata5_sanba = stops_linea5barra[minimo]
fermata5_sanba


# ### Train

# Another solution, for students in Sanbartolameo, is the Trento-Bassano train.  
# We check the distance between the residence and the train station.

# In[ ]:


import pyproj

geod = pyproj.Geod(ellps='WGS84')
train_staz = (46.047599, 11.135170)
sanba_residence = (46.047082, 11.133743)

lat0, lon0 = sanba_residence
lat1, lon1 = train_staz
    
azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
distance


# Given the high difference between distances of bus stops number 5 and 5/, and the need to take a bus or go by walk there, the number 13 and the train seems to be the best options.  
# Therefore, students from Sanba are not considered in the article.

# ## Selecting stops for the way going and the coming back only
# 

# ### Train Station - Povo

# In[ ]:


# trips going --> direction = 0


# In[ ]:


andata = trips_area_5['direction_id'] == 0


# In[ ]:


trips_5_andata = trips_area_5[andata]


# In[ ]:


# i want only the stops served in week days between september and june
# the focus is on mobility in period of lessons


# In[ ]:


# calendar


# service_id:
# - 92019091220200610
# - 662019091220200610
# - 672019091220200610

# In[ ]:


service = [92019091220200610, 662019091220200610, 672019091220200610]


# In[ ]:


trips_5_andata_feriale = trips_5_andata[trips_5_andata.service_id.isin(service)]


# In[ ]:


# select only one trip station-Povo 5


# In[ ]:


trips_ids = [trips_5_andata_feriale['trip_id'][882]]


# In[ ]:


trips_ids = list(trips_ids)
trips_ids


# In[ ]:


stop_5_andata_fer = stop_times_linea5[stop_times_linea5.trip_id.isin(trips_ids)]


# In[ ]:


stop_5_andata_fer.head()
#fermate del 5


# In[ ]:


stop_id_andata = list(stop_5_andata_fer.stop_id.unique())


# In[ ]:


stops_andata_fer = stops[stops.stop_id.isin(stop_id_andata)]


# In[ ]:


stop_5_andata_fer.index = range(len(stop_5_andata_fer))


# In[ ]:


stops_andata_fer.index = range(len(stops_andata_fer))


# In[ ]:


stop_5_andata_fer = stop_5_andata_fer[0:13]
stop_5_andata_fer


# In[ ]:


# from https://www.daftlogic.com/sandbox-google-maps-find-altitude.htm
altitude = [194, 193, 194, 196, 198, 212, 224, 253, 261, 295, 324, 350, 383]


# In[ ]:


stop_5_andata_fer['stop_name'] = ''

stop_5_andata_fer['stop_lat'] = ''

stop_5_andata_fer['stop_lon'] = ''


stop_5_andata_fer['coord'] = ''


stop_5_andata_fer['altitude'] = altitude


stop_5_andata_fer['direction'] = ['andata' for i in range(0, len(stop_5_andata_fer))]


# In[ ]:


for i in range (0, len(stop_5_andata_fer)):
    stopid = stop_5_andata_fer['stop_id'][i]
    for j in range(0, len(stops_andata_fer)):
        if stops_andata_fer['stop_id'][j] == stopid:
            lat = stops_andata_fer['stop_lat'][j]
            lon = stops_andata_fer['stop_lon'][j]
            stop_5_andata_fer['stop_name'][i] = stops_andata_fer['stop_name'][j]            
            stop_5_andata_fer['stop_lat'][i] = lat
            stop_5_andata_fer['stop_lon'][i] = lon
            stop_5_andata_fer['coord'][i] = [lat, lon]
            i += 1


# In[ ]:


stop_5_andata_fer


# In[ ]:


### non funziona ###

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="my-application")
location = geolocator.reverse('46.065613, 11.158009')
print(location.altitude)import geocoder
g = geocoder.google([46.0681, 11.118642], method='elevation')
print(g.meters)def get_elevation(lat, long):
    query = ('https://api.open-elevation.com/api/v1/lookup'
             f'?locations={lat},{long}')
    r = requests.get(query).json()  
    elevation = pd.io.json.json_normalize(r, 'results')['elevation'].values[0]
    return elevation
# In[ ]:


### non funziona ###


# ### Povo - Train Station

# In[ ]:


# trips coming back --> direction = 1


# In[ ]:


ritorno = trips_area_5['direction_id'] == 1


# In[ ]:


trips_5_ritorno = trips_area_5[ritorno]


# In[ ]:


trips_5_ritorno_feriale = trips_5_ritorno[trips_5_ritorno.service_id.isin(service)]


# In[ ]:


trips_ids_r = [trips_5_ritorno_feriale['trip_id'][1682]]
trips_ids_r = list(trips_ids_r)


# In[ ]:


stop_5_ritorno_fer = stop_times_linea5[stop_times_linea5.trip_id.isin(trips_ids_r)]


# In[ ]:


stop_id_ritorno = list(stop_5_ritorno_fer.stop_id.unique())


# In[ ]:


stops_ritorno_fer = stops[stops.stop_id.isin(stop_id_ritorno)]


# In[ ]:


stops_ritorno_fer.index = range(len(stops_ritorno_fer))
stop_5_ritorno_fer.index = range(len(stop_5_ritorno_fer))


# In[ ]:


stop_5_ritorno_fer['stop_name'] = ''

stop_5_ritorno_fer['stop_lat'] = ''

stop_5_ritorno_fer['stop_lon'] = ''

stop_5_ritorno_fer['direction'] = ['ritorno' for i in range(0, len(stop_5_ritorno_fer))]


# In[ ]:


for i in range (0, len(stop_5_ritorno_fer)):
    stopid = stop_5_ritorno_fer['stop_id'][i]
    for j in range(0, len(stops_ritorno_fer)):
        if stops_ritorno_fer['stop_id'][j] == stopid:
            lat = stops_ritorno_fer['stop_lat'][j]
            lon = stops_ritorno_fer['stop_lon'][j]
            stop_5_ritorno_fer['stop_name'][i] = stops_ritorno_fer['stop_name'][j]            
            stop_5_ritorno_fer['stop_lat'][i] = lat
            stop_5_ritorno_fer['stop_lon'][i] = lon
            i += 1


# In[ ]:


frame = [stop_5_andata_fer, stop_5_ritorno_fer]


# In[ ]:


result = pd.concat(frame)


# In[ ]:


result.index = range(len(result))
result['linea'] = ['5' for i in range(0, len(result))]


# In[ ]:


result.to_csv('point_for_map.csv', index=False)


# In[ ]:


# map for datawrapper


# In[ ]:


shape = gpd.read_file('poli_sociali.shp')


# In[ ]:


shape.crs


# In[ ]:


shape.to_crs(epsg=4326).to_file('trento.geojson', driver = 'GeoJSON')


# In[ ]:


# get address of POVO 0, 1, 2 for datawrapper map


# In[ ]:


from geopy.geocoders import Nominatim
geolocator = Nominatim()
address = 'Via Sommarive, 9, 38123 Povo,Trento TN'
location = geolocator.geocode(address, timeout=30)
      
print(location.latitude, location.longitude)


# In[ ]:


# interactive plot of stops


# ## Using the selected output to print an interactive plot with Google

# In[ ]:


from bokeh.plotting import gmap
from bokeh.io import output_file, output_notebook, show
from bokeh.models import (
  GMapPlot, GMapOptions, ColumnDataSource, Circle, LogColorMapper, BasicTicker, ColorBar,
    DataRange1d, PanTool, WheelZoomTool, BoxSelectTool, SaveTool, HoverTool
)
import bokeh.models as bmo
from bokeh.models.mappers import ColorMapper, LinearColorMapper
from bokeh.palettes import Category20, d3

map_options = bmo.GMapOptions(lat=46.07, lng=11.138, map_type="hybrid", zoom=14)

p = gmap("AIzaSyAx7KM1GP_oShgvkuIqNksBVAVRO8so_is", map_options, title="Linea 5: fermate di andata e ritorno")

palette = d3['Category20'][3][:len(result['direction'].unique())]
color_map = bmo.CategoricalColorMapper(factors=result['direction'].unique(),
                                   palette=palette)

source = bmo.ColumnDataSource(
    data=dict(lat=result['stop_lat'],
        lon=result['stop_lon'],
        color=result['direction'],
              place = result['stop_name']
    )
)



p.circle(x="lon", y="lat", size=10,color = 'black', fill_color={'field': 'color', 'transform': color_map},
         legend='color',
         fill_alpha=0.9, source=source)

TOOLTIPS = [
    ("Place", "@place")
]

p.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), SaveTool())
p.add_tools(HoverTool(tooltips=TOOLTIPS))
show(p)



output_file("plot5.html")


# ## Graph to show where the commuter students come from

# In[ ]:


data_graph = pd.read_csv('lat_long-datagrap.txt', sep=",")


# In[ ]:


data_graph['array'] = None


# In[ ]:


for i in range(0, len(data_graph)):
    part = [data_graph['long_part'][i], data_graph['lat_part'][i]]
    arr = [data_graph['long_arr'][i], data_graph['lat_arr'][i]]
    data_graph['array'][i] = [part, arr]


# In[ ]:


data_graph


# In[ ]:


from staticmap import StaticMap, Line
#m = StaticMap(1000, 1000, 35)
m = StaticMap(900, 900, url_template='https://tile.thunderforest.com/neighbourhood/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf')


# In[ ]:


for i in range(0,4):
    coordinates = data_graph['array'][i]
    line_outline = Line(coordinates, 'white', 1)
    line = Line(coordinates, '#1E504F', 2)
    m.add_line(line_outline)
    m.add_line(line)
for i in range(4,5):
    coordinates = data_graph['array'][i]
    line_outline = Line(coordinates, 'grey', 1)
    line = Line(coordinates, '#D2322D', 2)
    m.add_line(line_outline)
    m.add_line(line)


# In[ ]:


image = m.render()


# In[ ]:


#image


# In[ ]:


image.save('provenienza.png')


# ## Map to show the position of bus stops, train station, university and students residences

# ### Map with markers

# In[ ]:


from staticmap import StaticMap, IconMarker, Line 


# In[ ]:


m = StaticMap(1000, 1000, url_template='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf')

icon_home = IconMarker((11.133746, 46.047067), './icons/house.png', 20, 40) # sanba
m.add_marker(icon_home)
icon_home = IconMarker((11.118847, 46.073256), './icons/house.png', 12, 32) # mayer
m.add_marker(icon_home)

icon_uni = IconMarker((11.1505, 46.06526), './icons/uni.png', 12, 32) # povo 0
m.add_marker(icon_uni)
icon_uni = IconMarker((11.1496, 46.0672), './icons/uni.png', 12, 32) # povo 1
m.add_marker(icon_uni)
icon_uni = IconMarker((11.1497, 46.0681), './icons/uni.png', 12, 32) # povo 2
m.add_marker(icon_uni)

icon_train = IconMarker((11.119435, 46.072167), './icons/train.png', 12, 32) # train station
m.add_marker(icon_train)
icon_train = IconMarker((11.135098, 46.047568), './icons/train.png', 12, 32) # train station sanba
m.add_marker(icon_train)
icon_train = IconMarker((11.142540, 46.065106), './icons/train.png', 12, 32) # train station mesiano
m.add_marker(icon_train)

icon_stop = IconMarker((11.1196, 46.0719), './icons/bus.png', 12, 32) # p. dante
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1186, 46.0681), './icons/bus.png', 12, 32) # rosmini
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1209, 46.0646), './icons/bus.png', 12, 32) # travai
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1233,46.0652), './icons/bus.png', 12, 32) # p. fiera
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1263, 46.0668), './icons/bus.png', 12, 32) # san francesco
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1279, 46.0695), './icons/bus.png', 12, 32) # venezia port'aquila
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1315, 46.0666), './icons/bus.png', 12, 32) # venezia cave
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1364, 46.0686), './icons/bus.png', 12, 32) # corallo
m.add_marker(icon_stop)
icon_stop = IconMarker((11.139, 46.0694), './icons/bus.png', 12, 32) # ponte lodovico
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1394, 46.0671), './icons/bus.png', 12, 32) # mesiano facoltà
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1417, 46.0649), './icons/bus.png', 12, 32) # mesiano stazione
m.add_marker(icon_stop)
icon_stop = IconMarker((11.1464, 46.0657), './icons/bus.png', 12, 32) # valoni
m.add_marker(icon_stop)
icon_stop = IconMarker((11.15, 46.0633), './icons/bus.png', 12, 32) # povo fac. scienze
m.add_marker(icon_stop)

m.add_line(Line(((11.1196, 46.0719), (11.1186, 46.0681)), 'black', 1)) # p. dante
m.add_line(Line(((11.1186, 46.0681), (11.1209, 46.0646)), 'black', 1)) # rosmini
m.add_line(Line(((11.1209, 46.0646), (11.1233,46.0652)), 'black', 1)) # travai
m.add_line(Line(((11.1233,46.0652), (11.1263, 46.0668)), 'black', 1)) # fiera
m.add_line(Line(((11.1263, 46.0668), (11.1279, 46.0695)), 'black', 1)) # s. francesco
m.add_line(Line(((11.1279, 46.0695), (11.1315, 46.0666)), 'black', 1)) # ven. p. aquila           
m.add_line(Line(((11.1315, 46.0666), (11.1364, 46.0686)), 'black', 1)) # ven. cave           
m.add_line(Line(((11.1364, 46.0686), (11.139, 46.0694)), 'black', 1)) # ven. corallo           
m.add_line(Line(((11.139, 46.0694), (11.1394, 46.0671)), 'black', 1)) # p.lodovico           
m.add_line(Line(((11.1394, 46.0671), (11.1417, 46.0649)), 'black', 1)) # mesiano fac.           
m.add_line(Line(((11.1417, 46.0649), (11.1464, 46.0657)), 'black', 1)) # mesiano staz.           
m.add_line(Line(((11.1464, 46.0657), (11.15, 46.0633)), 'black', 1)) # valoni   

image = m.render()


# In[ ]:


image


# In[ ]:


image.save('icons_mappa2.png')


# ## Closest stops to the ELEVATOR

# The elevator from via Grazioli to the faculty - Mesiano - will be leaving approximately from:
# 
# elevator(46.064571, 11.136247)

# ### Closest stops - going

# In[ ]:


stops = pd.read_csv(gtfdir + os.sep + 'stops.txt')


# In[ ]:


stops = stops.iloc[:, [0,4,5]]


# In[ ]:


stops['coords'] = None
stops['distance_from_elevator'] = None


# In[ ]:


for i in range (0, len(stops)):
    stops['coords'][i] = (stops['stop_lat'][i], stops['stop_lon'][i])


# In[ ]:


import pyproj

geod = pyproj.Geod(ellps='WGS84')
elevator = (46.064571, 11.136247)

for i in range(0, len(stops)):
    lat0, lon0 = elevator
    lat1, lon1 = stops['coords'][i] 
    
    azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
    stops['distance_from_elevator'][i] = distance


# In[ ]:


stops.sort_values("distance_from_elevator", axis = 0, 
                  ascending = True, inplace = True)


# In[ ]:


close = stops['distance_from_elevator'] <= 400
close_stops = stops[close]


# In[ ]:


close_stops


# In[ ]:


close_stops.index = range(0, len(close_stops))


# In[ ]:


for i in range(0, len(close_stops)):
    close_stops['coords'][i] = close_stops['coords'][i][::-1]

close_stops.head()


# In[ ]:


close_stops['color'] = None
color = ['gold', 'orange', 'chocolate', 'red', 'darkred', 
        'olive', 'chartreuse', 'green', 'lime', 'dodgerblue', 
        'darkblue']
close_stops['color'] = color
close_stops.head()


# In[ ]:


from staticmap import StaticMap, CircleMarker

m = StaticMap(1000, 1000, 
              url_template='https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf')
#https://tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf
#https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf


for i in range(0, len(close_stops)):
    coords = close_stops['coords'][i] 
    color = close_stops['color'][i] 
    marker_outline = CircleMarker(coords, 'white', 18)
    marker = CircleMarker(coords, color, 12)
    m.add_marker(marker_outline)
    m.add_marker(marker)


#elevator
m.add_line(Line(((11.136247, 46.064571), (11.138119, 46.064642)), 'blue', 5)) # p. dante


image = m.render()


# In[ ]:


image


# In[ ]:


#andata = close_stops['color'] == ['gold', 'orange', 'chocolate', 'red', 'darkred', 'chartreuse', 'green', 'dodgerblue']


# In[ ]:


elevator_andata = close_stops.iloc[[0,1,2,3,4,6,7,9], :]


# ### bus to reach the elevator to go up

# In[ ]:


elevator_andata


# In[ ]:


stop_times = pd.read_csv(gtfdir + os.sep + "stop_times.txt")
trips = pd.read_csv(gtfdir + os.sep + "trips.txt")
routes = pd.read_csv(gtfdir + os.sep + "routes.txt")


# In[ ]:


stops_times_area = stop_times[stop_times.stop_id.isin(elevator_andata.stop_id.values)]


# In[ ]:


trip_id_area = stops_times_area.trip_id.unique()
trip_id_area = list(trip_id_area)


# In[ ]:


trips_area = trips[trips.trip_id.isin(trip_id_area)]
trips_area.head()


# In[ ]:


routeids = list(trips_area.route_id.unique())
routeids


# In[ ]:


routes_area_ascensore_andata = routes[routes.route_id.isin(routeids)]
routes_area_ascensore_andata


# ### Closest stops - coming back

# In[ ]:


stops = pd.read_csv(gtfdir + os.sep + 'stops.txt')
stops = stops.iloc[:, [0,4,5]]
stops['coords'] = None
stops['distance_from_elevator'] = None


# In[ ]:


for i in range (0, len(stops)):
    stops['coords'][i] = (stops['stop_lat'][i], stops['stop_lon'][i])


# In[ ]:


stops.head()


# In[ ]:


import pyproj

geod = pyproj.Geod(ellps='WGS84')
elevator = (46.064746, 11.138223)


for i in range(0, len(stops)):
    lat0, lon0 = elevator
    lat1, lon1 = stops['coords'][i] 
    
    azimuth1, azimuth2, distance = geod.inv(lon0, lat0, lon1, lat1)
    
    stops['distance_from_elevator'][i] = distance


# In[ ]:


stops.sort_values("distance_from_elevator", axis = 0, 
                  ascending = True, inplace = True)


# In[ ]:


close = stops['distance_from_elevator'] <= 400
close_stops = stops[close]


# In[ ]:


close_stops.index = range(0, len(close_stops))


# In[ ]:


for i in range(0, len(close_stops)):
    close_stops['coords'][i] = close_stops['coords'][i][::-1]

close_stops.head()


# In[ ]:


close_stops['color'] = None
color = ['gold', 'red', 'darkred', 
        'green', 'lime', 'dodgerblue', 
        'darkblue']
close_stops['color'] = color
close_stops.head()


# In[ ]:


from staticmap import StaticMap, CircleMarker

m = StaticMap(1000, 1000, 
              url_template='https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf')
#https://tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=5739a95935164a99a16893aa92baecdf

for i in range(0, len(close_stops)):
    coords = close_stops['coords'][i] 
    color = close_stops['color'][i] 
    marker_outline = CircleMarker(coords, 'white', 18)
    marker = CircleMarker(coords, color, 12)
    m.add_marker(marker_outline)
    m.add_marker(marker)

#elevator
m.add_line(Line(((11.136247, 46.064571), (11.138119, 46.064642)), 'blue', 5)) # p. dante

image = m.render()


# In[ ]:


image


# In[ ]:


#andata = close_stops['color'] == ['red', 'darkred','green', 'lime']


# In[ ]:


elevator_ritorno = close_stops.iloc[[1, 2, 3, 4], :]


# In[ ]:


stop_times = pd.read_csv(gtfdir + os.sep + "stop_times.txt")
trips = pd.read_csv(gtfdir + os.sep + "trips.txt")
routes = pd.read_csv(gtfdir + os.sep + "routes.txt")


# In[ ]:


stops_times_area = stop_times[stop_times.stop_id.isin(elevator_ritorno.stop_id.values)]


# In[ ]:


trip_id_area = stops_times_area.trip_id.unique()
trip_id_area = list(trip_id_area)


# In[ ]:


trips_area = trips[trips.trip_id.isin(trip_id_area)]
trips_area.head()


# In[ ]:


routeids = list(trips_area.route_id.unique())
routeids


# In[ ]:


routes_area_ascensore_ritorno = routes[routes.route_id.isin(routeids)]
routes_area_ascensore_ritorno

