import sqlite3
import pandas as pd
  
# Conexión con la base de datos SQLite
connection = sqlite3.connect(r'Movielens.db')
  
# Cargar ficheros CSV en un DataFrame de Pandas
links_data = pd.read_csv('Database/ml-latest-small/ml-latest-small/links.csv')
movies_data = pd.read_csv('Database/ml-latest-small/ml-latest-small/movies.csv')
ratings_data = pd.read_csv('Database/ml-latest-small/ml-latest-small/ratings.csv')
tags_data = pd.read_csv('Database/ml-latest-small/ml-latest-small/tags.csv')

# Pasar los DataFrame a SQL y subirlos a la base de datos
links_data.to_sql('links', connection, if_exists='replace', index=False, dtype='INTEGER') # Especifico el tipo porque si no lo ponía como real
movies_data.to_sql('movies', connection, if_exists='replace', index=False)
ratings_data.to_sql('ratings', connection, if_exists='replace', index=False)
tags_data.to_sql('tags', connection, if_exists='replace', index=False)

# Se crea un cursor para ejecutar las órdenes SQL
cursor = connection.cursor()

# Se cierra la conexión con la base de datos
connection.close()