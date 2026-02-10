import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper Microservice for n8n")

# Mantenemos el modelo tiny pero optimizado
model = WhisperModel("tiny", device="cpu", compute_type="int8")

@app.get("/")
async def health():
    return {"status": "ok", "info": "Send a POST to /transcribe"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # 1. AÑADIMOS .oga a la lista de permitidos
    if not file.filename.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.oga')):
        raise HTTPException(status_code=400, detail="Formato no soportado")

    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. MEJORAMOS LA LLAMADA A TRANSCRIBE
        # Forzamos 'es' (español) y bajamos el umbral de silencio (vad_filter)
        segments, info = model.transcribe(
            temp_filename, 
            beam_size=3,              # Un poco más preciso que 1
            language="es",            # Forzamos español para evitar que detecte 'en' o silencio
            vad_filter=True,          # Limpia ruidos de fondo
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        text = " ".join([segment.text for segment in segments])
        
        # Si el texto sigue vacío, devolvemos un aviso
        if not text.strip():
            return {"text": "[No se detectó habla clara]", "duration": info.duration, "debug": "audio_read_ok"}

        return {
            "text": text.strip(),
            "language": info.language,
            "duration": info.duration
        }
    except Exception as e:
        print(f"Error: {str(e)}") # Add logging for debugging
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)