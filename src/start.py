from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

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


@app.get("/")
async def root():
    return RedirectResponse("/docs")
