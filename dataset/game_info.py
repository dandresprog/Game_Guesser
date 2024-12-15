#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
import zipfile
import io

response = requests.get('https://www.kaggle.com/api/v1/datasets/download/jummyegg/rawg-game-dataset')
zip_file = zipfile.ZipFile(io.BytesIO(response.content))
zip_file.extractall()

games = pd.read_csv('game_info.csv')
games.info()

games.drop(columns=['slug', 'tba', 'updated', 'website', 'rating','rating_top','suggestions_count','ratings_count', 'playtime', 'achievements_count', 'game_series_count', 'reviews_count', 'esrb_rating', 'added_status_yet', 'added_status_owned', 'added_status_beaten', 'added_status_toplay', 'added_status_dropped', 'added_status_playing'], inplace=True)


games.isnull().sum()


games.dropna(subset=['released', 'developers', 'genres', 'publishers', 'platforms', "metacritic"], inplace=True)


games.info()


games['released'] = games['released'].str[:4]
games.rename(columns={'released': 'released_year'}, inplace=True)


# Unir los géneros en una sola cadena con separador ", "
games['genres'] = games['genres'].apply(lambda x: x.replace("||", ", ").strip())
games['platforms'] = games['platforms'].apply(lambda x: x.replace("||", ", ").strip())
games['developers'] = games['developers'].apply(lambda x: x.replace("||", ", ").strip())
games['publishers'] = games['publishers'].apply(lambda x: x.replace("||", ", ").strip())


games.to_csv('game_info_cleaned.csv')

