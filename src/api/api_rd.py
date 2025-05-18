from datetime import datetime as dt
from typing import List

import jwt
from fastapi import APIRouter, Depends, Query, Request, Security
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from config import Config
from database.dao import Database
from database.models import (
    BuildingDelete,
    BuildingOut,
    OrganizationDelete,
    OrganizationOut,
)

router = APIRouter()

# auth placeholder -------
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

SECRET = Config.SECRET
ALGO = "HS256"


def check_key(api_key: str = Security(api_key_header)):
    try:
        data = jwt.decode(api_key, SECRET, algorithms=[ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Неверный API-ключ") from jwt.PyJWTError
    if data.get("scope") != "api-access":
        raise HTTPException(401, "Неверный API-ключ")
    return api_key


# auth placeholder -------

"""
GET REQUESTS
"""


@router.get("/api/token", tags=["Аутентификация"], summary="Получить токен")
async def get_token(req: Request):
    token = jwt.encode(
        {
            "encode-time": dt.utcnow().strftime("%d %b %Y, %H:%M:%S"),
            "scope": "api-access",
        },
        SECRET,
        algorithm=ALGO,
    )
    return {"api_key": token}


@router.get(
    "/api/organization/byId/",
    summary="Получить организацию по ID",
    response_model=OrganizationOut,
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def organization_by_self_id(
    req: Request,
    org_id: int = Query(..., description="ID организации"),
) -> JSONResponse:
    model = await Database.get_organization_by_id(org_id)
    if model:
        model = OrganizationOut.model_validate(model).model_dump(exclude_none=True)
        return model

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


@router.get(
    "/api/organizations/byTitle/",
    summary="Поиск организаций по названию",
    response_model=List[OrganizationOut],
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def search_for_organizations_h(
    req: Request,
    query: str = Query(..., description="Подстрока для поиска в названии организации"),
) -> JSONResponse:
    result = await Database.search_for_organizations(query)
    if result:
        result = [OrganizationOut.model_validate(model).model_dump(exclude_none=True) for model in result]

        return result

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


@router.get(
    "/api/organizations/byBuildingId/",
    summary="Получить организации в здании",
    response_model=List[OrganizationOut],
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def organizations_by_building_id(
    req: Request,
    building_id: int = Query(..., description="ID здания"),
) -> JSONResponse:
    result = await Database.get_organizations_by_bid(building_id)

    if result:
        result = [OrganizationOut.model_validate(model).model_dump(exclude_none=True) for model in result]

        return result

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


@router.get(
    "/api/organizations/byActivity/",
    summary="Получить организации по деятельности",
    response_model=List[OrganizationOut],
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def organizations_by_activity_label(
    req: Request,
    label: str = Query(..., description="Название деятельности"),
    strict: bool = Query(
        False,
        description=(
            "Если True — ищет строго по лейблу.\n\nЕсли False — включает потомков или совпадающих по иерархии."
        ),
    ),
) -> JSONResponse:
    result = await Database.get_organizations_by_activity(label, strict=strict)

    if result:
        result = [OrganizationOut.model_validate(model).model_dump(exclude_none=True) for model in result]

        return result

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


@router.get(
    "/api/organizations/inRadius/",
    summary="Получить организации в радиусе",
    response_model=List[OrganizationOut],
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def organizations_in_radius_m(
    req: Request,
    radius: float = Query(..., description="Радиус в метрах"),
    lat: float = Query(..., description="Широта точки"),
    lon: float = Query(..., description="Долгота точки"),
) -> JSONResponse:
    result = await Database.organizations_within_radius(lat, lon, radius)

    if result:
        result = [OrganizationOut.model_validate(model).model_dump(exclude_none=True) for model in result]

        return result

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


@router.get(
    "/api/buildings/inRadius/",
    summary="Получить здания в радиусе",
    response_model=List[BuildingOut],
    status_code=200,
    tags=["GET Запросы"],
    dependencies=[Depends(check_key)],
)
async def buildings_in_radius_m(
    req: Request,
    radius: float = Query(..., description="Радиус в метрах"),
    lat: float = Query(..., description="Широта точки"),
    lon: float = Query(..., description="Долгота точки"),
) -> JSONResponse:
    result = await Database.buildings_within_radius(lat, lon, radius)

    if result:
        result = [BuildingOut.model_validate(model).model_dump(exclude_none=True) for model in result]

        return result

    return JSONResponse({"status": "failed", "message": "Not Found"}, status_code=404)


"""
DELETE REQUESTS
"""


@router.delete(
    "/api/organization/delete",
    summary="Удалить организацию",
    tags=["DELETE Запросы"],
    dependencies=[Depends(check_key)],
)
async def delete_organization_h(
    req: Request,
    org_mod: OrganizationDelete,
) -> JSONResponse:
    result = await Database.delete_organization(org_mod)

    if result:
        return JSONResponse({"status": "ok"})

    return JSONResponse({"status": "not found"}, status_code=404)


@router.delete(
    "/api/building/delete",
    summary="Удалить здание",
    tags=["DELETE Запросы"],
    dependencies=[Depends(check_key)],
)
async def delete_building_h(req: Request, build_mod: BuildingDelete) -> JSONResponse:
    result = await Database.delete_building(build_mod)

    if result:
        return JSONResponse({"status": "ok"})

    return JSONResponse({"status": "not found"}, status_code=404)
