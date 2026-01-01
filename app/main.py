from fastapi import FastAPI

from app.api import auth, db, query

app = FastAPI(
    title="DataMind",
    description="Natural Language to SQL Data Analytics Tool",
    version="0.1.0",
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(db.router, prefix="/db", tags=["database"])
app.include_router(query.router, prefix="/query", tags=["query"])

# Health check
@app.get("/")
def root():
    return {"message" : "Datamind APIs are up and running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
