from app import create_app
from config import PORT
from dotenv import load_dotenv
import os
load_dotenv()
load_dotenv(".env.local" if os.getenv("RENDER") is None else ".env")
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)