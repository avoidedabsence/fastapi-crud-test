from typing import Any

import jwt
from fastapi import APIRouter, Depends, Request, Security
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from config import Config
from database.dao import Database
from database.models import (
    ActivityIn,
    ActivityOut,
    BuildingIn,
    BuildingOut,
    BuildingUpdate,
    OrganizationIn,
    OrganizationOut,
    OrganizationUpdate,
)

router = APIRouter()

# auth placeholder -------
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

SECRET = Config.SECRET
ALGO = "HS256"


def check_key(api_key: str = Security(api_key_header)) -> str:
    try:
        data = jwt.decode(api_key, SECRET, algorithms=[ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Неверный API-ключ") from jwt.PyJWTError
    if data.get("scope") != "api-access":
        raise HTTPException(401, "Неверный API-ключ")
    return api_key


# auth placeholder -------


"""
POST REQUESTS
"""


@router.post(
    "/api/organization/create",
    summary="Создать организацию",
    response_model=OrganizationOut,
    status_code=200,
    tags=["POST Запросы"],
    dependencies=[Depends(check_key)],
)
async def create_organization_h(
    req: Request,
    org_mod: OrganizationIn,
) -> dict[str, Any] | HTTPException:
    try:
        result = await Database.create_organization(org_mod)

        if result:
            result = OrganizationOut.model_validate(result).model_dump(
                exclude_none=True,
            )
            return result
    except Exception as e:
        raise HTTPException(400, e.__class__.__name__) from e

    raise HTTPException(500, "ISE")


@router.post(
    "/api/building/create",
    summary="Создать здание",
    response_model=BuildingOut,
    status_code=200,
    tags=["POST Запросы"],
    dependencies=[Depends(check_key)],
)
async def create_building_h(
    req: Request,
    build_mod: BuildingIn,
) -> dict[str, Any] | HTTPException:
    try:
        result = await Database.create_building(build_mod)

        if result:
            result = BuildingOut.model_validate(result).model_dump(exclude_none=True)
            return result
    except Exception as e:
        raise HTTPException(400, e.__class__.__name__) from e

    raise HTTPException(500, "ISE")


@router.post(
    "/api/activity/create",
    summary="Создать деятельность",
    tags=["POST Запросы"],
    dependencies=[Depends(check_key)],
)
async def create_activity_h(
    req: Request,
    act_mod: ActivityIn,
):
    try:
        result = await Database.create_activity(act_mod)

        if result:
            result = ActivityOut.model_validate(result).model_dump(exclude_none=True)
            return result

    except Exception as e:
        raise HTTPException(400, e.__class__.__name__) from e

    raise HTTPException(500, "ISE")


"""
PUT REQUESTS
"""


@router.put(
    "/api/organization/update",
    summary="Обновить организацию",
    response_model=OrganizationOut,
    status_code=200,
    tags=["PUT Запросы"],
    dependencies=[Depends(check_key)],
)
async def update_organization_h(
    req: Request,
    org_mod: OrganizationUpdate,
) -> dict[str, Any] | HTTPException:
    try:
        result = await Database.update_organization(org_mod)

        if result:
            result = OrganizationOut.model_validate(result).model_dump(
                exclude_none=True,
            )
            return result

    except Exception as e:
        raise HTTPException(400, e.__class__.__name__) from e

    raise HTTPException(500, "ISE")


@router.put(
    "/api/building/update",
    summary="Обновить здание",
    response_model=BuildingOut,
    status_code=200,
    tags=["PUT Запросы"],
    dependencies=[Depends(check_key)],
)
async def update_building_h(
    req: Request,
    build_mod: BuildingUpdate,
) -> dict[str, Any] | HTTPException:
    try:
        result = await Database.update_building(build_mod)

        if result:
            result = BuildingOut.model_validate(result).model_dump(exclude_none=True)
            return result

    except Exception as e:
        raise HTTPException(400, e.__class__.__name__) from e

    raise HTTPException(500, "ISE")
