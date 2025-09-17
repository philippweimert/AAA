from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    message: str

# Configure logging
log_file_path = ROOT_DIR / 'server.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Email configuration
async def send_email(contact_data: ContactForm):
    """Send contact form data via email"""
    try:
        # Email body
        body = f"""
Neue Kontaktanfrage über die Website:

Name: {contact_data.name}
E-Mail: {contact_data.email}
Unternehmen: {contact_data.company or 'Nicht angegeben'}
Telefon: {contact_data.phone or 'Nicht angegeben'}

Nachricht:
{contact_data.message}

---
Gesendet am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}
"""
        # Log the email content for now (in production, this would actually send)
        logger.info(f"Contact form submission: {body}")
        
        return {"status": "success", "message": "Nachricht erfolgreich gesendet"}
        
    except Exception as e:
        logger.error(f"Failed to process contact form: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Senden der Nachricht")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/contact")
async def submit_contact_form(contact_data: ContactForm):
    """Handle contact form submission"""
    try:
        result = await send_email(contact_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in contact form: {str(e)}")
        raise HTTPException(status_code=500, detail="Ein unerwarteter Fehler ist aufgetreten")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'build' directory
static_files_path = ROOT_DIR / 'frontend' / 'build'
app.mount("/static", StaticFiles(directory=static_files_path / 'static'), name="static")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve the React app for any other path."""
    return FileResponse(static_files_path / 'index.html')
