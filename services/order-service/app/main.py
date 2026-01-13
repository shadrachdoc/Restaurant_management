"""
Order Service - Main application
Handles online orders, table sessions, and assistance requests
"""
from fastapi import FastAPI, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from shared.config.settings import settings
from shared.utils.logger import setup_logger
from .database import init_db, close_db
from .routes import orders, sessions, assistance, analytics
from .websocket import manager
from .rabbitmq_consumer import start_consumer

# Setup logger
logger = setup_logger("order-service", settings.log_level, settings.log_format)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Order Service...")
    await init_db()
    logger.info("Database initialized")

    # Start RabbitMQ consumer in background
    asyncio.create_task(start_consumer())
    logger.info("RabbitMQ consumer started")

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

app.include_router(
    analytics.router,
    prefix="/api/v1",
    tags=["Analytics & Predictions"]
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


@app.websocket("/ws/orders/{restaurant_id}")
async def websocket_endpoint(websocket: WebSocket, restaurant_id: str):
    """
    WebSocket endpoint for real-time order notifications
    Clients connect to receive instant notifications when new orders arrive
    """
    await manager.connect(websocket, restaurant_id)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connection",
                "message": f"Connected to order notifications for restaurant {restaurant_id}",
                "restaurant_id": restaurant_id
            },
            websocket
        )

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")

            # Echo heartbeat/ping messages
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, restaurant_id)
        logger.info(f"WebSocket client disconnected from restaurant {restaurant_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, restaurant_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )
