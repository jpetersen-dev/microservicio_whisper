# Usamos una imagen más moderna y eficiente
FROM python:3.11-slim

# Instalamos ffmpeg, necesario para procesar formatos de audio
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Creamos un directorio de trabajo y un usuario sin privilegios
WORKDIR /app
RUN useradd -ms /bin/bash appuser
RUN chown -R appuser:appuser /app

# Copiamos primero el fichero de dependencias
COPY requirements.txt .

# Instalamos las dependencias de Python (aprovechando la caché de Docker)
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Cambiamos al usuario sin privilegios
USER appuser

EXPOSE 10000

# Comando para iniciar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]