from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import auth, db, query
from app.db.session import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DataMind",
    description="Natural Language to SQL Data Analytics Tool",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and optionally load NL2SQL model"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Optional: Eager load NL2SQL model at startup (recommended for production)
    # Uncomment the following to load the model when the server starts
    # instead of on first request
    """
    try:
        from app.engines.ml.nl2sql_service import get_nl2sql_service
        logger.info("Loading NL2SQL model at startup...")
        service = get_nl2sql_service()
        service.load_model()
        logger.info("NL2SQL model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load NL2SQL model: {e}")
    """

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(db.router, prefix="/db", tags=["database"])
app.include_router(query.router, prefix="/query", tags=["query"])

# Health check
@app.get("/")
def root():
    return {"message": "Datamind APIs are up and running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}



# Health check
@app.get("/")
def root():
    return {"message" : "Datamind APIs are up and running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
