import uuid
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse

# Función para generar un ID único de usuario
def generar_user_id():
    return str(uuid.uuid4())

# Middleware para manejar cookies de usuario
@app.middleware("http")
async def middleware_usuario(request: Request, call_next):
    # Revisar si ya existe un user_id en las cookies
    user_id = request.cookies.get('user_id')
    
    # Si no existe, generar uno nuevo
    if not user_id:
        user_id = generar_user_id()
    
    # Adjuntar el user_id a la solicitud para que esté disponible en los endpoints
    request.state.user_id = user_id
    
    response = await call_next(request)
    
    # Establecer la cookie con el user_id
    response.set_cookie(
        key='user_id', 
        value=user_id, 
        httponly=True,  # Protección contra XSS
        secure=True,    # Solo se envía sobre HTTPS
        max_age=30*24*60*60  # Duración de 30 días
    )
    
    return response

# Endpoint para guardar progreso
@app.post("/guardar_progreso")
async def guardar_progreso(request: Request, datos_progreso: dict):
    # Obtener el user_id de las cookies
    user_id = request.state.user_id
    
    # Guardar en base de datos
    query = """
    INSERT INTO progreso_usuarios (user_id, datos_progreso, fecha)
    VALUES (%s, %s, NOW())
    ON CONFLICT (user_id) DO UPDATE 
    SET datos_progreso = %s, fecha = NOW()
    """
    
    # Ejecutar consulta en la base de datos
    await database.execute(
        query, 
        (user_id, json.dumps(datos_progreso), json.dumps(datos_progreso))
    )
    
    return {"status": "progreso guardado"}

# Endpoint para recuperar progreso
@app.get("/obtener_progreso")
async def obtener_progreso(request: Request):
    # Obtener el user_id de las cookies
    user_id = request.state.user_id
    
    # Recuperar de base de datos
    query = "SELECT datos_progreso FROM progreso_usuarios WHERE user_id = %s"
    resultado = await database.fetch_one(query, (user_id,))
    
    if resultado:
        return JSONResponse(content=json.loads(resultado['datos_progreso']))
    else:
        return JSONResponse(content={}, status_code=404)