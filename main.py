import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper Microservice for n8n")

# Cargamos el modelo 'tiny' con cuantización int8 para ahorrar RAM
model = WhisperModel("tiny", device="cpu", compute_type="int8")

@app.get("/")
async def health():
    return {"status": "alive", "info": "Send a POST to /transcribe"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Crear un nombre único para evitar colisiones
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Transcripción (beam_size=1 es más rápido y usa menos memoria)
        segments, info = model.transcribe(temp_filename, beam_size=1)
        text = " ".join([segment.text for segment in segments])
        
        return {
            "text": text.strip(),
            "language": info.language,
            "duration": info.duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)