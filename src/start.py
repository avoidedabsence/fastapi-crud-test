from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError

from api.api_cu import router as CreateUpdateRouter
from api.api_rd import router as ReadDeleteRouter
from config import Config
from database.dao import Database
from test_data import create_test_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init(Config.DB_URL, Config.DB_MAXCON)
    await create_test_data()

    yield

    await Database.close()


app = FastAPI(
    lifespan=lifespan,
    title="Тестовое задание: FastAPI CRUD on PSQL w/ ltree, postgis & SQLAlchemy",
    description=("t.me/avoidedabsence"),
)

app.include_router(ReadDeleteRouter)
app.include_router(CreateUpdateRouter)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.get("/")
async def root():
    return RedirectResponse("/docs")
