import os
import uuid
import time
from fastapi import FastAPI, Request, HTTPException, Header
from faster_whisper import WhisperModel

app = FastAPI()

# Configuración del modelo
MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
THREADS = int(os.getenv("WHISPER_THREADS", 1))
API_KEY_SECRET = os.getenv("API_KEY", "")

model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=THREADS)

@app.post("/transcribe")
async def transcribe(request: Request, x_api_key: str = Header(None)):
    # Seguridad
    if API_KEY_SECRET and x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=403, detail="No autorizado")

    # LEER EL AUDIO DIRECTAMENTE DEL CUERPO (Solución para n8n)
    audio_data = await request.body()
    if not audio_data:
        raise HTTPException(status_code=400, detail="No se recibió audio")

    temp_filename = f"temp_{uuid.uuid4()}.oga"
    start_time = time.time()
    
    try:
        with open(temp_filename, "wb") as f:
            f.write(audio_data)
        
        # Transcripción rápida
        segments, info = model.transcribe(temp_filename, beam_size=1, language="es", vad_filter=True)
        text = " ".join([segment.text for segment in segments])
        
        return {
            "text": text.strip() if text.strip() else "[Silencio detectado]",
            "duration": round(info.duration, 2),
            "processing_time": round(time.time() - start_time, 2)
        }
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)