import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from olist.load_data import load_all_data
data = load_all_data("./data")

# ORDERS
from olist.preprocess import transformar_columnas_datetime
from olist.preprocess import tiempo_de_espera
from olist.preprocess import real_vs_esperado

orders = data['orders'].copy()
orders = orders[orders["order_status"] == "delivered"]

orders = transformar_columnas_datetime(orders)

orders = orders[['order_id', 'order_status', 'order_purchase_timestamp',
                'order_delivered_customer_date', 'order_estimated_delivery_date']]

orders = tiempo_de_espera(orders)

orders = real_vs_esperado(orders)

orders.drop('order_purchase_timestamp', axis=1, inplace=True)
orders.drop('order_delivered_customer_date', axis=1, inplace=True)
orders.drop('order_estimated_delivery_date', axis=1, inplace=True)

orders.rename(columns={'order_status': 'status_de_la_orden'}, inplace=True)

# REVIEWS
from olist.preprocess import puntaje_de_compra

reviews = data['order_reviews'].copy()
reviews = reviews[["order_id", "review_score"]]

reviews = puntaje_de_compra(reviews)

# NUMERO_DE_PRODUCTOS
from olist.preprocess import calcular_numero_productos

numero_de_productos = data['order_items'].copy()
numero_de_productos = calcular_numero_productos(numero_de_productos)


# NUMERO_DE_VENDEDORES
from olist.preprocess import numero_de_vendedores

order_items = data['order_items'].copy()
numero_de_vendedores = numero_de_vendedores(order_items)

# CALCULAR_PRECIO_Y_TRANSPORTE
from olist.preprocess import calcular_precio_y_transporte

order_items = data['order_items'].copy()
precio_y_transporte = calcular_precio_y_transporte(order_items)

# DISTANCIAS
from olist.preprocess import haversine_distance
from olist.preprocess import calcular_distancia_vendedor_comprador

sellers = data['sellers'].copy()
geolocation = data['geolocation'].copy()
customers = data['customers'].copy()
order_items = data['order_items'].copy()
orders_para_distancias = data['orders'].copy()
distancias = calcular_distancia_vendedor_comprador(orders_para_distancias, geolocation, customers, order_items, sellers)
