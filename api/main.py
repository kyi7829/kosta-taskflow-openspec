import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

load_dotenv()

from api.database import engine, Base
from api.routers import auth, teams, tasks, messages

app = FastAPI(title="TaskFlow API", version="1.0.0")

# CORS
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5500")
cors_origins = [o.strip() for o in cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables on startup (for local dev; production uses alembic)
@app.on_event("startup")
def on_startup():
    from api import models  # noqa
    Base.metadata.create_all(bind=engine)


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        # Already in our format
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": detail},
        )
    # Plain string or other
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Extract first error message
    msg = "입력값이 올바르지 않습니다"
    if errors:
        first = errors[0]
        err_msg = first.get("msg", "")
        # pydantic v2 prefixes with "Value error, "
        if "Value error, " in err_msg:
            msg = err_msg.replace("Value error, ", "")
        elif err_msg:
            msg = err_msg
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": msg}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "서버 오류가 발생했습니다"}},
    )


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(messages.router, prefix="/api", tags=["messages"])


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Static Files (로컬 개발용) ─────────────────────────────────────────────────
# frontend/ 폴더를 루트(/)에서 서빙 — http://localhost:8000 으로 접근
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
