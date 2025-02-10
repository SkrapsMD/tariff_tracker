from pydantic import BaseModel
from typing import Dict


class TariffRequest(BaseModel):
    new_tariffs: Dict[str, float]
    pass_through: float = 1.0

class PriceEffect(BaseModel):
    country: str
    price_effect: float