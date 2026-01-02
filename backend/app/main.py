import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.api.routes import auth, users, cameras, models, upload, history
from app.models.user import User  # Import to register with Base
from app.services.inference.model_manager import model_manager
from app.services.alerts.alert_manager import alert_manager
from app.services.camera_service import camera_service
from app.models.history_log import LiveSessionLog, DetectionHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Violence Monitoring System...")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Configure alert services
        if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
            gmail_config = {
                'client_id': settings.GMAIL_CLIENT_ID,
                'client_secret': settings.GMAIL_CLIENT_SECRET,
                'refresh_token': settings.GMAIL_REFRESH_TOKEN,
                'sender_email': settings.GMAIL_SENDER
            }
            await alert_manager.configure_service('gmail', gmail_config)
            logger.info("Gmail alert service configured")

        if settings.TELEGRAM_BOT_TOKEN:
            telegram_config = {
                'bot_token': settings.TELEGRAM_BOT_TOKEN,
                'chat_id': settings.TELEGRAM_CHAT_ID
            }
            await alert_manager.configure_service('telegram', telegram_config)
            logger.info("Telegram alert service configured")

        # Live Camera Model is now lazy-loaded by CameraService on first use.
        # No need to pre-load here via model_manager.
        
        # Load default model if available
        # Load default model if available
        available_models = model_manager.scan_models_directory()
        if available_models:
            try:
                # Just pick the first available model as default
                default_model = available_models[0]
                
                await model_manager.load_model(
                    default_model['name'],
                    default_model['path']
                )
                await model_manager.set_active_model(default_model['name'])
                logger.info(f"Loaded default model: {default_model['name']}")
            except Exception as e:
                logger.warning(f"Failed to load default model: {e}")

        # Create default admin user if none exists
        await create_default_admin()
        
        # Task 3: Clear Live Session Logs on Restart
        from app.models.history_log import LiveSessionLog
        from sqlalchemy import delete
        async with AsyncSessionLocal() as db:
            await db.execute(delete(LiveSessionLog))
            await db.commit()
            logger.info("Cleared Live Session Logs")

        # Start Camera Service (Task 1 & 3)
        # We generally do NOT start it by default as per user request (manual trigger)
        # camera_service.start_camera()

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Violence Monitoring System...")

    try:
        # Stop Camera
        camera_service.stop_camera()
        
        # Cleanup alert services
        await alert_manager.cleanup()
        logger.info("Alert services cleaned up")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")
async def create_default_admin():
    """Create default admin user if none exists"""
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            # Check if any admin user exists
            result = await db.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                # Create default admin
                admin = User(
                    email="admin@example.com",
                    username="admin",
                    full_name="System Administrator",
                    hashed_password=get_password_hash("admin123"),
                    role=UserRole.ADMIN,
                    is_active=True
                )

                db.add(admin)
                await db.commit()

                logger.info("Created default admin user (admin@example.com / admin123)")
                logger.warning("Please change the default admin password immediately!")

        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready violence detection and monitoring system",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*"]  # Configure for production
    )

# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status_code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation exception handler"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "status_code": 422,
                "message": "Request validation failed",
                "details": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception):
    """Custom general exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_error",
                "status_code": 500,
                "message": "Internal server error" if not settings.DEBUG else str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = datetime.utcnow()

    # Process request
    response = await call_next(request)

    # Log request details
    process_time = (datetime.utcnow() - start_time).total_seconds()

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response

# API routes
api_v1_prefix = "/api/v1"

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(cameras.router, prefix=api_v1_prefix)
app.include_router(models.router, prefix=api_v1_prefix)
app.include_router(upload.router, prefix=api_v1_prefix)
app.include_router(history.router, prefix=api_v1_prefix)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Violence Monitoring System API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "services": {
            "database": "connected",  # TODO: Add actual health checks
            "redis": "connected",
            "models": len(model_manager.list_loaded_models()),
            "active_model": model_manager.active_model_name
        }
    }

@app.get("/info")
async def system_info():
    """System information endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "loaded_models": model_manager.list_loaded_models(),
        "active_model": model_manager.active_model_name,
        "alert_services": alert_manager.get_service_status(),
        "timestamp": datetime.utcnow().isoformat()
    }
