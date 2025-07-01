from fastapi import FastAPI
from app.database import engine, Base
from app.api.v1 import users, items ,utils

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Simple FastAPI Demo",
    description="A simple demo with Users and Items",
    version="1.0.0"
)

# Include API routes
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])
app.include_router(utils.router, tags=["Health Check"])

@app.get("/")
def root():
    return {
        "message": "Welcome to Simple FastAPI Demo!",
        "docs": "/docs"
    }