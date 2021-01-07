
# coding: utf-8

# In[1]:


import pandas as pd
import matplotlib.pyplot as plt
import descartes
import geopandas as gpd
from shapely.geometry import Point, Polygon


# In[3]:


shape = gpd.read_file('poli_sociali.shp')
shape.head()


# In[9]:


trento = shape[shape.nome_quart=='POVO']


# In[10]:


area = trento.geometry
id = int(trento.index[0])
area = area[id]


# In[11]:


area


# In[12]:


trento


# In[13]:


trento.to_file('shape_povo.geojson', driver = 'GeoJSON')

