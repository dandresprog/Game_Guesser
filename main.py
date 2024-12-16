from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import psycopg2
from random import randint
import os


app = FastAPI()

# Montar la carpeta "static" para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'videogames_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        host=os.getenv('DB_HOST', 'localhost'),  
        port="5432"
    )


# Ruta para la página principal
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# Ruta para obtener un juego aleatorio
@app.get("/random-game")
def get_random_game():
    try:
        conn = get_connection()
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
        conn = get_connection()  # Obtener conexión del pool
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
 
    print(target_game)
    print(user_guess)

    if not user_guess or not target_game:
        return {"error": "Invalid input data"}

    # Establecer la conexión a la base de datos
    conn = get_connection()
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
        "metacritic": target_game[1] if target_game[1] else "Desconocido",
        "released_year": target_game[2] if target_game[2] else "Desconocido",
        "platforms": target_game[3] if target_game[3] else "Desconocido",
        "developers": target_game[4] if target_game[4] else "Desconocido",
        "genres": target_game[5] if target_game[5] else "Desconocido",
        "publishers": target_game[6] if target_game[6] else "Desconocido"
    }

    print(user_game_data)
    print(target_game_data)

    # Comparar los datos de ambos juegos
    similarities = {}
    for key in user_game_data:
        if user_game_data[key] == target_game_data[key]:
            similarities[key] = True
        else:
            similarities[key] = False
    
    # Si no es correcto, devolver las similitudes
    return {"similarities": similarities}
