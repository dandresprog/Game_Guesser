# Usamos la imagen base de Python
FROM python:3.11

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el código de la aplicación al contenedor
COPY . .


# luego instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt
