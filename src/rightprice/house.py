from pydantic import BaseModel


class House(BaseModel):
    address: str
    property_type: str | None
    n_bedrooms: int | None
    dates: list[str]
    prices: list[int | None]
