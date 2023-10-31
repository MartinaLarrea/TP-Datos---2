import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from olist.load_data import load_all_data
data = load_all_data("./data")

# ORDERS

orders = data['orders'].copy()
orders = orders[orders["order_status"] == "delivered"]

date_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                'order_delivered_customer_date', 'order_estimated_delivery_date']

for column in date_columns:
    orders[column] = pd.to_datetime(orders[column])

orders = orders[['order_id', 'order_status', 'order_purchase_timestamp',
                'order_delivered_customer_date', 'order_estimated_delivery_date']]

orders['tiempo_de_espera'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']).dt.days
orders['tiempo_de_espera_previsto'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']).dt.days.astype(float)

orders["real_vs_esperado"] = (orders['tiempo_de_espera'] - orders['tiempo_de_espera_previsto'])
orders['real_vs_esperado'] = orders['real_vs_esperado'].apply(lambda x: x if x > 0 else 0)

orders.drop('order_purchase_timestamp', axis=1, inplace=True)
orders.drop('order_delivered_customer_date', axis=1, inplace=True)
orders.drop('order_estimated_delivery_date', axis=1, inplace=True)

orders.rename(columns={'order_status': 'status_de_la_orden'}, inplace=True)

# REVIEWS

reviews = data['order_reviews'].copy()
reviews = reviews[["order_id", "review_score"]]

reviews['es_cinco_estrellas'] = reviews['review_score'].apply(lambda x: 1 if x == 5 else 0)
reviews['es_una_estrella'] = reviews['review_score'].apply(lambda x: 1 if x == 1 else 0)

# NUMERO_DE_PRODUCTOS

numero_de_productos = data['order_items'].copy()
numero_de_productos = numero_de_productos.groupby('order_id').size().reset_index(name='numero_de_productos')


# NUMERO_DE_VENDEDORES

order_items = data['order_items'].copy()
numero_de_vendedores = order_items.groupby('order_id')['seller_id'].nunique().reset_index()
numero_de_vendedores = numero_de_vendedores.rename(columns={'seller_id': 'numero_de_vendedores'})

# CALCULAR_PRECIO_Y_TRANSPORTE

order_items = data['order_items'].copy()
calcular_precio_y_transporte = order_items.groupby('order_id')[['price', 'freight_value']].sum().reset_index()

# DISTANCIAS

from math import radians, sin, cos, asin, sqrt

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Computa distancia entre dos pares (lat, lng)
    Ver - (https://en.wikipedia.org/wiki/Haversine_formula)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))

geolocation = data['geolocation'].copy()
sellers = data['sellers'].copy()

geo = geolocation.groupby('geolocation_zip_code_prefix')[['geolocation_lat', 'geolocation_lng']].first().reset_index()
geo_sellers = geo.rename(columns={'geolocation_zip_code_prefix': 'seller_zip_code_prefix'})
sellers = sellers[['seller_id', 'seller_zip_code_prefix']]

sellers_loc = pd.merge(sellers, geo_sellers, on='seller_zip_code_prefix', how='left')
sellers_loc = sellers_loc.rename(columns={'geolocation_lat': 'lat_seller', "geolocation_lng" : "lon_seller"})


customers = data['customers'].copy()

geo_customers = geo.rename(columns={'geolocation_zip_code_prefix': 'customer_zip_code_prefix'})
customers = customers[['customer_id', 'customer_zip_code_prefix']]

customers_loc = pd.merge(customers, geo_customers, on='customer_zip_code_prefix', how='left')
customers_loc = customers_loc.rename(columns={'geolocation_lat': 'lat_customer', "geolocation_lng" : "lon_customer"})

order_items = data['order_items'].copy()
order_items = order_items[['order_id','order_item_id', 'seller_id']]

order_seller = pd.merge(order_items, sellers_loc, on='seller_id', how='left')

orders_customer = data['orders'].copy()
orders_customer = orders_customer[['order_id', 'customer_id']]

distancias = pd.merge(order_seller, orders_customer, on='order_id', how='left')
distancias = pd.merge(distancias, customers_loc, on='customer_id', how='left')
distancias['distancia_al_cliente'] = distancias.apply(lambda row: haversine_distance(row['lon_seller'], row['lat_seller'], row['lon_customer'], row['lat_customer']), axis=1)
distancias = distancias.groupby("order_id")["distancia_al_cliente"].mean().reset_index()
distancias = distancias.dropna()


