import os
import shutil
import uuid
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper Microservice - Render Optimized")

# --- CARGA DE CONFIGURACIÓN ---
# Usamos variables de entorno para que sea flexible sin tocar el código
MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
THREADS = int(os.getenv("WHISPER_THREADS", 1))
API_KEY_SECRET = os.getenv("API_KEY", "") # Opcional: para proteger tu API

# --- INICIALIZACIÓN DEL MODELO ---
# Lo cargamos una sola vez al arrancar el servicio
print(f"--- Cargando modelo {MODEL_NAME} con {THREADS} hilos ---")
model = WhisperModel(
    MODEL_NAME, 
    device="cpu", 
    compute_type="int8", # Crítico para RAM
    cpu_threads=THREADS,
    num_workers=THREADS
)

@app.get("/")
async def health():
    return {
        "status": "online", 
        "model": MODEL_NAME, 
        "threads": THREADS,
        "message": "Envíe POST a /transcribe"
    }

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...), 
    x_api_key: str = Header(None)
):
    # 1. Seguridad básica (si configuraste API_KEY en Render)
    if API_KEY_SECRET and x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=403, detail="No autorizado")

    # 2. Validar formatos (incluyendo .oga de Telegram)
    if not file.filename.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.oga')):
        raise HTTPException(status_code=400, detail="Formato de audio no soportado")

    temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
    start_time = time.time()
    
    try:
        # 3. Guardar el audio temporalmente
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. Transcripción con ajustes de velocidad máxima
        # beam_size=1 es el modo 'Turbo'. Menos preciso pero mucho más rápido.
        segments, info = model.transcribe(
            temp_filename, 
            beam_size=1, 
            language="es",         # Forzamos español para ahorrar CPU
            vad_filter=True,       # Ignora silencios
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Unimos los segmentos de texto
        text = " ".join([segment.text for segment in segments])
        
        processing_time = time.time() - start_time
        print(f"--- Procesado en {processing_time:.2f}s | Audio: {info.duration:.2f}s ---")

        return {
            "text": text.strip() if text.strip() else "[No se detectó voz]",
            "language": info.language,
            "duration": round(info.duration, 2),
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 5. Siempre limpiar el archivo temporal para no llenar el disco
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)