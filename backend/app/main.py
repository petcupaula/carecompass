"""
CareCompass Backend API

AI-powered patient communication quality analyzer.
Integrates Plaud (transcription), Interhuman AI (engagement analysis), 
and Crusoe (coaching generation).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import sessions_router, dashboard_router

app = FastAPI(
    title="CareCompass API",
    description="AI Shadow Coach for Healthcare Providers",
    version="0.1.0",
)

# CORS for iOS app and web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {
        "name": "CareCompass API",
        "version": "0.1.0",
        "description": "AI Shadow Coach for Healthcare Providers",
        "endpoints": {
            "sessions": "/sessions",
            "dashboard": "/dashboard",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
