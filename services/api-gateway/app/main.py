"""
API Gateway for Restaurant Management System
Handles routing, authentication, and rate limiting for all microservices
"""
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from typing import Optional
import time
from collections import defaultdict
import asyncio

# Service URLs from environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
RESTAURANT_SERVICE_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://restaurant-service:8003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8004")
POS_SERVICE_URL = os.getenv("POS_SERVICE_URL", "http://pos-service:8005")  # Future POS service
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8007")

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

app = FastAPI(
    title="Restaurant Management API Gateway",
    description="Unified API Gateway for all restaurant management services",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting storage
rate_limit_storage = defaultdict(list)
security = HTTPBearer(auto_error=False)


# Rate limiting middleware
async def rate_limit(request: Request):
    """Simple rate limiting based on IP address"""
    client_ip = request.client.host
    current_time = time.time()

    # Clean old requests
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check rate limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    # Add current request
    rate_limit_storage[client_ip].append(current_time)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": time.time()
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def gateway(
    request: Request,
    path: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Main gateway routing function
    Routes requests to appropriate microservices
    """
    # Apply rate limiting
    await rate_limit(request)

    # Debug logging
    print(f"DEBUG: Received path: '{path}', method: {request.method}")

    # Determine target service based on path
    if path.startswith("uploads/"):
        # Route uploaded files to restaurant service
        target_url = f"{RESTAURANT_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing uploads to RESTAURANT_SERVICE: {target_url}")
    elif path.startswith("api/v1/auth") or path.startswith("api/v1/users"):
        target_url = f"{AUTH_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing to AUTH_SERVICE: {target_url}")
    elif path.startswith("api/v1/customers"):
        target_url = f"{CUSTOMER_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing to CUSTOMER_SERVICE: {target_url}")
    elif path.startswith("api/v1/orders") or path.startswith("api/v1/sessions") or path.startswith("api/v1/assistance"):
        target_url = f"{ORDER_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing to ORDER_SERVICE: {target_url}")
    elif path.startswith("api/v1/restaurants") and "/analytics/" in path:
        # Route detailed analytics endpoints to order-service (e.g., /analytics/revenue, /analytics/popular-items)
        target_url = f"{ORDER_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing detailed analytics to ORDER_SERVICE: {target_url}")
    elif path.startswith("api/v1/restaurants"):
        target_url = f"{RESTAURANT_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing to RESTAURANT_SERVICE: {target_url}")
    elif path.startswith("api/v1/pos"):  # Future POS service
        target_url = f"{POS_SERVICE_URL}/{path}"
        print(f"DEBUG: Routing to POS_SERVICE: {target_url}")
    else:
        print(f"DEBUG: No route match for path: '{path}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service not found for path: {path}"
        )

    # Prepare headers
    headers = dict(request.headers)
    # Remove host header to avoid conflicts
    headers.pop("host", None)

    # Debug logging for authorization
    print(f"DEBUG: Incoming Authorization header: {request.headers.get('authorization', 'NOT FOUND')}")
    print(f"DEBUG: Credentials object: {credentials}")

    # Authorization header is already in the headers dict from request.headers
    # No need to add it again - it's already there!
    print(f"DEBUG: Authorization header in forwarded request: {headers.get('authorization', 'NOT FOUND')}")

    # Get request body
    body = await request.body()

    # Debug log headers being sent
    if "/users" in path:
        print(f"DEBUG: Headers being sent to backend: {headers}")

    # Forward request to target service
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params
            )

            # Debug log error responses
            if response.status_code >= 400 and "/users" in path:
                print(f"DEBUG: Error response {response.status_code}: {response.text}")

            # Return response from target service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service temporarily unavailable"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timeout"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gateway error: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
