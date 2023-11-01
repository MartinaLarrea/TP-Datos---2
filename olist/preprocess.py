import pandas as pd
from math import radians, sin, cos, asin, sqrt


def transformar_columnas_datetime(orders):
    date_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                'order_delivered_customer_date', 'order_estimated_delivery_date']

    for column in date_columns:
        orders[column] = pd.to_datetime(orders[column])
    
    return orders


def tiempo_de_espera(orders):
    orders['tiempo_de_espera'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']).dt.days
    orders['tiempo_de_espera_previsto'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']).dt.days.astype(float)
    return orders


def real_vs_esperado(orders):
    orders["real_vs_esperado"] = (orders['tiempo_de_espera'] - orders['tiempo_de_espera_previsto'])
    orders['real_vs_esperado'] = orders['real_vs_esperado'].apply(lambda x: x if x > 0 else 0)
    return orders


def puntaje_de_compra(reviews):
    reviews['es_cinco_estrellas'] = reviews['review_score'].apply(lambda x: 1 if x == 5 else 0)
    reviews['es_una_estrella'] = reviews['review_score'].apply(lambda x: 1 if x == 1 else 0)
    return reviews

def calcular_numero_productos(order_items):
    order_items = order_items.groupby('order_id').size().reset_index(name='numero_de_productos')
    return order_items

def numero_de_vendedores(order_items):
    numero_de_vendedores = order_items.groupby('order_id')['seller_id'].nunique().reset_index()
    numero_de_vendedores = numero_de_vendedores.rename(columns={'seller_id': 'numero_de_vendedores'})
    return numero_de_vendedores


def calcular_precio_y_transporte(order_items):
    precio_y_transporte = order_items.groupby('order_id')[['price', 'freight_value']].sum().reset_index()
    return precio_y_transporte

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


def calcular_distancia_vendedor_comprador(orders, geolocation, customers, order_items, sellers):
    # Agrupo por zipcode y traigo el primer valor de lat y lon ya que un mismo zipcode puede tener muchas latitudes y longitudes y necesitamos solamente una por zipcode
    geo = geolocation.groupby('geolocation_zip_code_prefix')[['geolocation_lat', 'geolocation_lng']].first().reset_index()
    # Renombro la columna para poder mergearla con el dataset de sellers
    geo_sellers = geo.rename(columns={'geolocation_zip_code_prefix': 'seller_zip_code_prefix'})
    # Me quedo con las columnas que necesito
    sellers = sellers[['seller_id', 'seller_zip_code_prefix']]
    # Hago el merge left para que todos los sellers tengan su lat y lon y que no traiga aquellos registros que no tienen coincidencias en el dataset de sellers
    sellers_loc = pd.merge(sellers, geo_sellers, on='seller_zip_code_prefix', how='left')
    # Renombro las columnas para que, a la hora de traer las lat y lon de los compradores no se pisen ni se confundan
    sellers_loc = sellers_loc.rename(columns={'geolocation_lat': 'lat_seller', "geolocation_lng" : "lon_seller"})
    # Hago lo mismo pero con los clientes, mismo proceso
    geo_customers = geo.rename(columns={'geolocation_zip_code_prefix': 'customer_zip_code_prefix'})
    customers = customers[['customer_id', 'customer_zip_code_prefix']]

    customers_loc = pd.merge(customers, geo_customers, on='customer_zip_code_prefix', how='left')
    customers_loc = customers_loc.rename(columns={'geolocation_lat': 'lat_customer', "geolocation_lng" : "lon_customer"})
    # La union entre seller y customers se da así: sellers <-seller_id-> order_item <-order_id-> orders <-customer_id->customers
    # Por lo tanto voy a traer los dos dataset que las conectan sellers y customer y me quedaré con solo las columnas necesarias para los merges
    order_items = order_items[['order_id','order_item_id', 'seller_id']]

    order_seller = pd.merge(order_items, sellers_loc, on='seller_id', how='left')

    orders_customer = orders[['order_id', 'customer_id']]
    # Uno con el de sellers
    distancias = pd.merge(order_seller, orders_customer, on='order_id', how='left')
    # Uno con el de customers
    distancias = pd.merge(distancias, customers_loc, on='customer_id', how='left')
    # Aplico la función para calcular la distancia entre seller y cliente
    distancias['distancia_al_cliente'] = distancias.apply(lambda row: haversine_distance(row['lon_seller'], row['lat_seller'], row['lon_customer'], row['lat_customer']), axis=1)
    # Agrupo por order_id y caluclo el promedio de la distancia, ya que hasta el momento, cada orden estaba abierta por order_item y una misma orden podía tener más de un producto, por ende más de un vendedor, a distintas distancias
    distancias = distancias.groupby("order_id")["distancia_al_cliente"].mean().reset_index()
    # Elimino los vacios
    distancias = distancias.dropna()
    return distancias