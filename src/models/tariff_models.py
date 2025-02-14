from pydantic import BaseModel
from typing import Dict


class CountryInfoResponse(BaseModel):
    iso: str
    current_tariff: float
    import_intensity: float
    default_pass_through: float
class TariffRequest(BaseModel):
    new_tariffs: Dict[str, float]
    old_tariffs: Dict[str, float]
    pass_through: float = 1.0
class PriceEffect(BaseModel):
    country: str
    price_effect: float
    diff_tariffs: float
