# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos y los instala
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de la aplicación
COPY . .

# Expone el puerto en el que la aplicación se ejecutará
EXPOSE 8000

# Comando para ejecutar la aplicación
# RUN uvicorn main:app --reload