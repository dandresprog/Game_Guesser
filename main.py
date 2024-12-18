import os
import uuid
import json
import psycopg2
import difflib
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
from random import randint
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

app = FastAPI()

# Montar la carpeta "static" para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_videogames_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'videogames_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        host=os.getenv('DB_HOST', 'localhost'),  
        port=os.getenv('DB_PORT', '5432')
    )

@asynccontextmanager
async def get_users_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('USER_DB_NAME', 'users_db'),
        user=os.getenv('USER_DB_USER', 'user'),
        password=os.getenv('USER_DB_PASSWORD', 'password'),
        host=os.getenv('USER_DB_HOST', 'localhost'),
        port=os.getenv('USER_DB_PORT', '5432')
    )
    try:
        yield conn
    finally:
        conn.close()
    
# Función similitud entre cadenas y verificar coincidencia por prefijo
def similarity_ratio(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def compare_names(target_name, user_name):
    # Ambos comienzan con la misma letra
    if target_name[0].lower() == user_name[0].lower():
        prefix_similarity = 0.8  # Un umbral bajo si empieza con la misma letra
    else:
        prefix_similarity = 0.0

    # Usar difflib para calcular la similitud completa
    full_similarity = similarity_ratio(target_name, user_name)
    
    # Si la similitud completa es alta o la coincidencia de prefijo es suficiente, considerarlo similar
    if full_similarity > 0.7 or prefix_similarity > 0.7:
        return "yellow", user_name  # Coincidencia parcial
    else:
        return "red", user_name  # Coincidencia baja
    
# Función para comparar listas de elementos
def compare_lists(target_list, user_list):
    """Compara listas para encontrar elementos comunes."""
    target_set = set(target_list.split(", "))
    user_set = set(user_list.split(", "))
    common = target_set & user_set
    if common:
        if target_set == user_set:
            return "green", ", ".join(user_set)  # Todos coinciden
        return "yellow", ", ".join(common)  # Coincidencias parciales
    return "red", user_list  # No hay coincidencias

# Ruta para la página principal
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# Ruta para obtener un juego aleatorio
@app.get("/random-game")
def get_random_game():
    try:
        conn = get_videogames_db_connection()
        cursor = conn.cursor()

        # Seleccionar un juego aleatorio directamente desde la base de datos
        query_random_game = """
        SELECT name, metacritic, released_year, platforms, developers, genres, publishers
        FROM videojuegos ORDER BY RANDOM() LIMIT 1;
        """
        cursor.execute(query_random_game)
        
        game = cursor.fetchone()

        if not game:  # Si no hay juegos en la base de datos
            return {"error": "No games available in the database"}
        print(game)
        conn.close()
        return game

    except Exception as e:
        print(e)
        return {"error": str(e)}

# Ruta para autocompletar juegos según el nombre
@app.get("/autocomplete")
def autocomplete_games(query: str):
    try:
        conn = get_videogames_db_connection()  # Obtener conexión del pool
        cursor = conn.cursor()

        # Buscar juegos que coincidan con la consulta
        query_autocomplete = "SELECT name FROM videojuegos WHERE name ILIKE %s LIMIT 10;"
        cursor.execute(query_autocomplete, (query + "%",))
        games = cursor.fetchall()


        return [game[0] for game in games]

    except Exception as e:
        return {"error": str(e)}

@app.post("/compare-game")
def compare_game(data: dict):
    # Obtener los datos de entrada
    target_game = data.get("target_game")
    user_guess = data.get("user_guess")
 
    similarities = {}

    if not user_guess or not target_game:
        return {"error": "Invalid input data"}

    # Establecer la conexión a la base de datos
    conn = get_videogames_db_connection()
    cursor = conn.cursor()

    # Obtener el juego adivinado (user_guess) desde la base de datos
    game_guess_query = """
    SELECT name, metacritic, released_year, platforms, developers, genres, publishers
    FROM videojuegos 
    WHERE name = %s;
    """
    cursor.execute(game_guess_query, (user_guess,))
    game = cursor.fetchone()
    # Cerrar la conexión
    conn.close()

    # Extraer la información del juego adivinado
    user_game_data = {
        "name": game[0],
        "metacritic": game[1] if game[1] else "Desconocido",
        "released_year": game[2] if game[2] else "Desconocido",
        "platforms": game[3] if game[3] else "Desconocido",
        "developers": game[4] if game[4] else "Desconocido",
        "genres": game[5] if game[5] else "Desconocido",
        "publishers": game[6] if game[6] else "Desconocido"
    }

    # Extraer la información del juego objetivo
    target_game_data = {
        "name": target_game[0],
        "metacritic": target_game[1],
        "released_year": target_game[2],
        "platforms": target_game[3],
        "developers": target_game[4],
        "genres": target_game[5],
        "publishers": target_game[6]
    }

    print(user_game_data)
    print(target_game_data)
    
    # Comparar las listas de elementos
    # Comparar el nombre
    color, name_value = compare_names(target_game_data["name"], user_game_data["name"])
    similarities["name"] = {
        "value": name_value,
        "color": color
    }

    # Verificar si el nombre coincide
    if target_game_data["name"].lower() == user_game_data["name"].lower():
        return JSONResponse({"message": "¡Correcto!"})
    
        # Comparar Metacritic con flechas
    target_metacritic = float(target_game_data.get("metacritic", 0))
    user_metacritic = float(user_game_data.get("metacritic", 0))
    if user_metacritic < target_metacritic:
        arrow = "↑"
    elif user_metacritic > target_metacritic:
        arrow = "↓"
    else:
        arrow = "="

    similarities["metacritic"] = {
        "value": f"{user_metacritic} {arrow}",
        "color": "green" if user_metacritic == target_metacritic else "red"
    }

    # Comparar año de salida
    target_year = int(target_game_data.get("released_year", 0))
    user_year = int(user_game_data.get("released_year", 0))
    if user_year < target_year:
        arrow = "↑"
    elif user_year > target_year:
        arrow = "↓"
    else:
        arrow = "="

    similarities["released_year"] = {
        "value": f"{user_year} {arrow}",
        "color": "green" if user_year == target_year else "red"
    }

    # Comparar Platforms
    color, value = compare_lists(target_game_data.get("platforms", ""), user_game_data.get("platforms", ""))
    similarities["platforms"] = {"value": value, "color": color}

    # Comparar Developers
    color, value = compare_lists(target_game_data.get("developers", ""), user_game_data.get("developers", ""))
    similarities["developers"] = {"value": value, "color": color}

    # Comparar Genres
    color, value = compare_lists(target_game_data.get("genres", ""), user_game_data.get("genres", ""))
    similarities["genres"] = {"value": value, "color": color}

    # Comparar Publishers
    color, value = compare_lists(target_game_data.get("publishers", ""), user_game_data.get("publishers", ""))
    similarities["publishers"] = {"value": value, "color": color}


    return JSONResponse({"similarities": similarities})

def generar_user_id():
    return str(uuid.uuid4())


@app.middleware("http")
async def middleware_usuario(request: Request, call_next):
    user_id = request.cookies.get('user_id')
    
    if not user_id:
        user_id = generar_user_id()
    
    request.state.user_id = user_id
    
    response = await call_next(request)
    
    response.set_cookie(
        key='user_id', 
        value=user_id, 
        httponly=True,
        secure=True,
        max_age=30*24*60*60
    )
    
    return response


@app.post("/guardar_progreso")
async def guardar_progreso(request: Request, datos_progreso: dict):
    user_id = request.state.user_id
    
    query = """
    INSERT INTO progreso_usuarios (user_id, datos_progreso, fecha)
    VALUES (%s, %s, NOW())
    ON CONFLICT (user_id) DO UPDATE 
    SET datos_progreso = %s, fecha = NOW()
    """
    
    async with get_users_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                logger.info("Ejecutando consulta: %s", query)
                logger.info("Con parámetros: %s, %s", user_id, json.dumps(datos_progreso))
                cursor.execute(query, (user_id, json.dumps(datos_progreso), json.dumps(datos_progreso)))
                conn.commit()
                logger.info("Commit exitoso")
                return {"status": "progreso guardado"}
            except Exception as e:
                conn.rollback()
                logger.error("Error al guardar el progreso: %s", str(e))
                return {"error": str(e)}


@app.get("/obtener_progreso")
async def obtener_progreso(request: Request):
    user_id = request.state.user_id
    
    query = "SELECT datos_progreso FROM progreso_usuarios WHERE user_id = %s"
    
    async with get_users_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            resultado = cursor.fetchone()
    
    if resultado:
        progress_data = resultado[0] if isinstance(resultado[0], dict) else json.loads(resultado[0])
        return JSONResponse(content=progress_data)
    else:
        return JSONResponse(content={}, status_code=404)

