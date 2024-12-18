#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
import zipfile
import io
import os
from sqlalchemy import create_engine
import re
from bs4 import BeautifulSoup

def formatear_nombre_metacritic(nombre):
    nombre = nombre.lower()
    nombre = nombre.replace(':', '-')
    nombre = nombre.replace('’', '')
    nombre = nombre.replace("'", '')
    nombre = nombre.replace('.', '')
    nombre = nombre.replace(' ', '-')
    nombre = re.sub(r'-+', '-', nombre)
    return nombre

def obtener_score_metacritic(nombre_juego):
    api_key = '' # Agregar API Key de ScraperAPI
    nombre_formateado = formatear_nombre_metacritic(nombre_juego)

    url_metacritic = f"https://www.metacritic.com/game/{nombre_formateado}"
    url = f'https://api.scraperapi.com?api_key={api_key}&url={url_metacritic}'
    
    try:
        headers = {"User-Agent": "Mac Firefox"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            
            critic_score = soup.find('div', class_='c-siteReviewScore', attrs={'data-v-e408cafe': ''})
            
            if critic_score:
                return critic_score.text.strip()
            else:
                return "No se encontró el score"
        
        else:
            print(f"Error: No se pudo acceder a la página (Código de estado: {response.status_code})")
            return None

    except requests.RequestException as e:
        return f"Error en la solicitud: {e}"
    
response = requests.get('https://www.kaggle.com/api/v1/datasets/download/jummyegg/rawg-game-dataset')
zip_file = zipfile.ZipFile(io.BytesIO(response.content))
zip_file.extractall()

games = pd.read_csv('game_info.csv')

games.drop(columns=['slug', 'tba', 'updated', 'website', 'rating','rating_top','suggestions_count','ratings_count', 'playtime', 'achievements_count', 'game_series_count', 'reviews_count', 'esrb_rating', 'added_status_yet', 'added_status_owned', 'added_status_beaten', 'added_status_toplay', 'added_status_dropped', 'added_status_playing'], inplace=True)
games.isnull().sum()

games.dropna(subset=['released', 'developers', 'genres', 'publishers', 'platforms', "metacritic"], inplace=True)

if False : games['metacritic'] = games['name'].apply(obtener_score_metacritic)

games['released'] = games['released'].str[:4]
games.rename(columns={'released': 'released_year'}, inplace=True)



# Unir los géneros en una sola cadena con separador ", "
games['genres'] = games['genres'].apply(lambda x: x.replace("||", ", ").strip())
games['platforms'] = games['platforms'].apply(lambda x: x.replace("||", ", ").strip())
games['developers'] = games['developers'].apply(lambda x: x.replace("||", ", ").strip())
games['publishers'] = games['publishers'].apply(lambda x: x.replace("||", ", ").strip())

db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'videogames_db')
db_user = os.getenv('DB_USER', 'user')
db_password = os.getenv('DB_PASSWORD', 'password')

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}')
games.to_sql('videojuegos', engine, if_exists='replace', index=False)

