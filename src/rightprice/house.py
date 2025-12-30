from pydantic import BaseModel


class House(BaseModel):
    """
    A property with its sold price history.

    Attributes:
        address: Full address of the property.
        property_type: Type of property (e.g. "Detached", "Semi-Detached").
        n_bedrooms: Number of bedrooms.
        dates: List of sale dates in chronological order.
        prices: List of sale prices corresponding to each date.
    """

    address: str
    property_type: str | None
    n_bedrooms: int | None
    dates: list[str]
    prices: list[int | None]
