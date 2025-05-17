from pydantic import BaseModel, ConfigDict, Field, model_validator, validator
from typing import List, Any, Optional
from sqlalchemy_utils import Ltree

# --------------------- OUTPUT    

class BuildingOut(BaseModel): 
    model_config = ConfigDict(from_attributes=True, exclude_none=True)
    
    id: int                                             = Field(description="ID здания")
    addr: str                                           = Field(description="Адрес здания", examples=["ул. Пушкина д. 1"])
    lat: float                                          = Field(description="Широта здания", examples=[56.4])
    lon: float                                          = Field(description="Долгота здания", examples=[32.3])
    organizations: Optional[List['OrganizationOut']]    = Field(default=None,
                                                             description="Список организаций в этом здании (optional)")

class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, exclude_none=True)
        
    id: int                                             = Field(description="ID деятельности")
    label: str                                          = Field(description="Наименование деятельности")
    path: str                                           = Field(description="Путь до деятельности в базе данных")
    organizations: Optional[List['OrganizationOut']]    = Field(default=None,
                                                             description="Список организаций в этом здании (optional)")
    
    @validator("path", pre=True)
    def validate_path(cls, value):
        if isinstance(value, Ltree):
            return value.path
        return value

class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, exclude_none=True)
        
    id: int                                 = Field(description="ID организации")
    title: str                              = Field(description="Название организации")
    phone: list[str]                        = Field(description="Номера телефонов организации")
    building: BuildingOut                   = Field(description="Здание, в котором находится организация")
    activities: Optional[List[ActivityOut]] = Field(default=None,
                                                    description="Список деятельностей организации (optional)")
    
# ---------------------- INPUT
    
class BuildingIn(BaseModel): 
    addr: str                           = Field(description="Адрес здания", examples=["ул. Пушкина д. 1"])
    lat: float                          = Field(description="Широта здания", examples=[56.4])
    lon: float                          = Field(description="Долгота здания", examples=[32.3])
    organizations: Optional[List[str]]  = Field(default=None,
                                               description="Список названий <b>существующих</b> организаций, которые находятся в здании (предыдущие офисы компаний будут перезаписаны на новое здание)",
                                               examples=[["Организация #1", "Организация #2", "etc..."]])

class ActivityIn(BaseModel):
    labels: list[str] = Field(description="Полный путь до создаваемой деятельности (все указанные деятельности будут созданы, даже если все предки не существуют)",
                              examples=[['Компьютеры', 'Ноутбуки', 'ASUS']])

class OrganizationIn(BaseModel):
    title: str              = Field(description="Название организации", examples=["ООО 'Тмыв'"])
    phone: list[str]        = Field(description="Список номеров телефонов организации", examples=[["79999999999", "79888888888", "etc..."]])
    building_id: int        = Field(description="ID здания, в котором находится организация", examples=[1])
    activity_ids: list[int] = Field(description="Список ID деятельностей организации", examples=[[1, 2]])

# ---------------------- UPDATE

class OrganizationUpdate(BaseModel):
    id: int                             = Field(description="ID Организации", examples=[1])
    title: Optional[str]                = Field(default=None)
    phone: Optional[list[str]]          = Field(default=None)
    b_id: Optional[int]                 = Field(default=None)
    activity_ids: Optional[list[int]]   = Field(default=None)

class BuildingUpdate(BaseModel): 
    id: int                 = Field(description="ID Организации", examples=[1])
    addr: Optional[str]     = Field(default=None, description="Адрес здания (optional)", examples=["ул. Пушкина д. 1"])
    lat: Optional[float]    = Field(default=None, description="Широта здания (optional)", examples=[56.4])
    lon: Optional[float]    = Field(default=None, description="Долгота здания (optional)",  examples=[32.3])
    
# ---------------------- DELETE

class OrganizationDelete(BaseModel):
    id: int = Field(description="ID организации", examples=[1])

class BuildingDelete(BaseModel): 
    id: int = Field(description="ID здания", examples=[1])


OrganizationOut.model_rebuild()
ActivityOut.model_rebuild()
BuildingOut.model_rebuild()