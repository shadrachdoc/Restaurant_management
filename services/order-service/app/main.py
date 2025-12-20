"""
Order Service - Main application
Handles online orders, table sessions, and assistance requests
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from shared.config.settings import settings
from shared.utils.logger import setup_logger
from .database import init_db, close_db
from .routes import orders, sessions, assistance

# Setup logger
logger = setup_logger("order-service", settings.log_level, settings.log_format)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Order Service...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Order Service...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Restaurant Management - Order Service",
    description="Online Order Management, Table Sessions, and Assistance Requests",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    orders.router,
    prefix="/api/v1",
    tags=["Orders"]
)

app.include_router(
    sessions.router,
    prefix="/api/v1",
    tags=["Table Sessions"]
)

app.include_router(
    assistance.router,
    prefix="/api/v1",
    tags=["Assistance Requests"]
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint"""
    return {
        "service": "Order Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "order-service"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )
