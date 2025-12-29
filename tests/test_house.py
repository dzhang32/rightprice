from rightprice.house import House


def test_house_model() -> None:
    """
    Test House initialisation.
    """
    house = House(
        address="123 Street",
        property_type="Flat",
        n_bedrooms=2,
        dates=["01 Jan 2024", "15 Jun 2020"],
        prices=[450000, 380000],
    )

    assert house.address == "123 Street"
    assert house.property_type == "Flat"
    assert house.n_bedrooms == 2
    assert len(house.dates) == 2
    assert len(house.prices) == 2
