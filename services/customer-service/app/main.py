"""
Customer Service - FastAPI Application
Handles customer authentication, profiles, and order history for multi-tenant SaaS
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db
from .routes import customers
from shared.utils.logger import setup_logger

logger = setup_logger("customer-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    logger.info("Customer Service starting up...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Customer Service shutting down...")


app = FastAPI(
    title="Customer Service",
    description="Customer authentication and profile management for restaurant SaaS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    customers.router,
    prefix="/api/v1/customers",
    tags=["customers"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "customer-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Customer Service",
        "version": "1.0.0",
        "docs": "/docs"
    }
