from fastapi import FastAPI
import uvicorn
from models.database import Base, engine
from routers import audio_router, tag_router, meeting_router, chat_router
from fastapi.middleware.cors import CORSMiddleware
import logging

# Initialize FastAPI app
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include audio router
app.include_router(audio_router.router)

# Include tag router
app.include_router(tag_router.router)

# Include meeting router
app.include_router(meeting_router.router)

# Include chat router
app.include_router(chat_router.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example route
@app.get("/")
def read_root():
    return {"message": "Server is running on port 8080!"}

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8080)
    except Exception as e:
        logging.error(f"Server crashed due to: {e}")
        print("An error occurred while running the server. Check logs for details.")