import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

app = FastAPI()

# --- CONFIGURACIÓN DINÁMICA ---
# Cambia esta variable en Render: WHISPER_MODEL = "base" o "small"
MODEL_NAME = os.getenv("WHISPER_MODEL", "base") 

print(f"--- Cargando modelo: {MODEL_NAME} ---")
# Usamos cpu_threads=1 para no asustar a Render
model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=1)

@app.get("/")
async def health():
    # Retornamos estado y modelo para verificar cuál está cargado
    return {"status": "online", "model": MODEL_NAME}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Validación básica de extensión (opcional, pero recomendada)
    if not file.filename.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.oga')):
        raise HTTPException(status_code=400, detail="Formato no soportado")

    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # El initial_prompt ayuda a que el modelo no alucine con el contexto específico
        prompt = "Transcripción de Jonathan Petersen: psicología, n8n, desarrollo web, cal.com, automatización, checklist."
        
        segments, info = model.transcribe(
            temp_filename, 
            beam_size=5, 
            language="es",
            initial_prompt=prompt
        )
        
        text = " ".join([segment.text for segment in segments])
        return {
            "text": text.strip(), 
            "model_used": MODEL_NAME, 
            "duration": info.duration,
            "language": info.language
        }
    except Exception as e:
        # En caso de error, devolvemos 500 para que n8n sepa que falló
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)