import pandas as pd
from sqlalchemy import create_engine

# Conexión a la base de datos
engine = create_engine('postgresql://user:password@localhost:5432/videogames_db')  

# Carga el dataset
df = pd.read_csv('dataset/dataset.csv') 
df.to_sql('videojuegos', engine, if_exists='replace', index=False)
print("Datos cargados exitosamente.")