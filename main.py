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
from huggingface_hub import InferenceClient

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


# Función para calcular la similitud entre cadenas
def similarity_ratio(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def compare_names(target_name, user_name):
    # Dividir los nombres en palabras para comparar
    target_words = target_name.lower().split()
    user_words = user_name.lower().split()

    # Contar cuántas palabras coinciden
    common_words = set(target_words) & set(user_words)
    word_match_count = len(common_words)

    # Usar difflib para la similitud total
    full_similarity = similarity_ratio(target_name, user_name)

    # Establecer umbrales de similitud:
    # - Si hay más del 80% de coincidencias de palabras, es una coincidencia parcial (amarillo).
    # - Si es igual, es una coincidencia total (verde).
    # - De lo contrario, no hay coincidencia (rojo).
    if full_similarity == 1:
        return "green", user_name
    elif word_match_count / len(target_words) > 0.7:
        return "yellow", user_name
    else:
        return "red", user_name


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
        conn = get_videogames_db_connection()  # Obtener conexión del pool
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
    conn = get_videogames_db_connection()  # Obtener conexión del pool
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
        "Nombre": game[0],
        "Metacritic": game[1] if game[1] else "Desconocido",
        "Año": game[2] if game[2] else "Desconocido",
        "Plataformas": game[3] if game[3] else "Desconocido",
        "Desarrolladores": game[4] if game[4] else "Desconocido",
        "Generos": game[5] if game[5] else "Desconocido",
        "Publicadores": game[6] if game[6] else "Desconocido"
    }

    # Extraer la información del juego objetivo
    target_game_data = {
        "Nombre": target_game[0],
        "Metacritic": target_game[1],
        "Año": target_game[2],
        "Plataformas": target_game[3],
        "Desarrolladores": target_game[4],
        "Generos": target_game[5],
        "Publicadores": target_game[6]
    }

    print(user_game_data)
    print(target_game_data)
    
    

    # Comparar el nombre usando la nueva función de similitud mejorada
    color ,name_value= compare_names(target_game_data["Nombre"], user_game_data["Nombre"])
    similarities["Nombre"] = {
        "value": name_value,
        "color": color
    }
        # Comparar Metacritic con flechas
    target_metacritic = float(target_game_data.get("Metacritic", 0))
    user_metacritic = float(user_game_data.get("Metacritic", 0))
    if user_metacritic < target_metacritic:
        arrow = "↑"
    elif user_metacritic > target_metacritic:
        arrow = "↓"
    else:
        arrow = "="
    similarities["Metacritic"] = {
        "value": f"{user_metacritic} {arrow}",
        "color": "green" if user_metacritic == target_metacritic else "red"
    }

    # Comparar año de salida
    target_year = int(target_game_data.get("Año", 0))
    user_year = int(user_game_data.get("Año", 0))
    if user_year < target_year:
        arrow = "↑"
    elif user_year > target_year:
        arrow = "↓"
    else:
        arrow = "="

    similarities["Año"] = {
        "value": f"{user_year} {arrow}",
        "color": "green" if user_year == target_year else "red"
    }

    # Comparar Platforms
    color, value = compare_lists(target_game_data.get("Plataformas", ""), user_game_data.get("Plataformas", ""))
    similarities["Plataformas"] = {"value": value, "color": color}

    # Comparar Developers
    color, value = compare_lists(target_game_data.get("Desarrolladores", ""), user_game_data.get("Desarrolladores", ""))
    similarities["Desarrolladores"] = {"value": value, "color": color}

    # Comparar Genres
    color, value = compare_lists(target_game_data.get("Generos", ""), user_game_data.get("Generos", ""))
    similarities["Generos"] = {"value": value, "color": color}

    # Comparar Publishers
    color, value = compare_lists(target_game_data.get("Publicadores", ""), user_game_data.get("Publicadores", ""))
    similarities["Publicadores"] = {"value": value, "color": color}
    
    print (similarities)
    if all([value["color"] == "green" for value in similarities.values()]):
        return JSONResponse({"message": "Correcto" ,"similarities": similarities})
    else:
        return JSONResponse({"message": "Incorrecto","similarities": similarities})

@app.post("/get-hint")
async def get_hint(request: Request):
    # Obtener los datos de entrada
    data = await request.json()
    target_game = data.get("target_game")

    print(target_game)
    target_game_data = {
        "Nombre": target_game[0],
    }

    name = target_game_data.get("Nombre", "")

    print(name)

    client = InferenceClient(api_key="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")

    messages = [
        {
            "role": "user",
            "content": f"Descripcion simple, muy corta y clara de {name} en español, para intentar adivinarlo, sin mencionar el nombre o nada relevante"
        }
    ]

    completion = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2", 
        messages=messages, 
        max_tokens=50
    )
    # Extraer y devolver la pista
    hint = completion.choices[0].message['content']
    print(hint)

    return JSONResponse({"hint": hint})


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