# Whisper API Microservice

Este es un microservicio basado en FastAPI que utiliza `faster-whisper` para exponer un endpoint de transcripción de audio. Está diseñado para ser ligero y desplegarse fácilmente en plataformas como Render.

## Características

- **API Rápida**: Construido con [FastAPI](https://fastapi.tiangolo.com/).
- **Transcripción Eficiente**: Usa `faster-whisper` con el modelo `tiny` y cuantización `int8` para un bajo consumo de memoria.
- **Contenerizado**: Incluye un `Dockerfile` optimizado para producción.
- **Seguro**: Se ejecuta con un usuario no-root dentro del contenedor.

## Endpoints

### Health Check

Comprueba si el servicio está activo.

- **URL**: `/`
- **Método**: `GET`
- **Respuesta Exitosa**:
  ```json
  {
    "status": "alive",
    "info": "Send a POST to /transcribe"
  }
  ```

### Transcribir Audio

Envía un archivo de audio para obtener su transcripción.

- **URL**: `/transcribe`
- **Método**: `POST`
- **Body**: `multipart/form-data`
  - **key**: `file`
  - **value**: Tu archivo de audio (ej: `audio.mp3`, `audio.wav`).

- **Respuesta Exitosa**:
  ```json
  {
    "text": "Este es el texto transcrito del audio.",
    "language": "es",
    "duration": 15.3
  }
  ```

## Despliegue en Render

1.  **Repositorio**: Sube este código a un repositorio de GitHub.
2.  **Web Service**: En Render, crea un nuevo "Web Service".
3.  **Configuración**:
    - **Runtime**: `Docker`.
    - **Plan**: `Free` (o el que prefieras).
    - **Variable de Entorno**:
      - `Key`: `PORT`
      - `Value`: `10000`
4.  **Desplegar**: Conecta tu repositorio y despliega.

## Ejecución Local (con Docker)

1.  **Construir la imagen**:
    ```sh
    docker build -t whisper-api .
    ```

2.  **Ejecutar el contenedor**:
    ```sh
    docker run -p 10000:10000 whisper-api
    ```

El servicio estará disponible en `http://localhost:10000`.
