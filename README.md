# rightprice

What is the right price for your property of interest?

## Installation

I recommend using [uv](https://docs.astral.sh/uv/) to manage the Python version, virtual environment and `rightprice` installation:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install rightprice
```

## Usage

`rightprice` retrieves sold property prices for a given UK postcode, allowing you to analyze historical sale data in your area of interest.

### Basic Usage

```python
from rightprice.sold_prices import SoldPriceRetriever

# Retrieve sold prices for a postcode
retriever = SoldPriceRetriever("SE3 0AA")
df = retriever.retrieve()

# View the data
print(df)
```

### Advanced Options

You can filter results by search radius and time period:

```python
# Search within 0.5 miles, last 5 years
retriever = SoldPriceRetriever(
    postcode="SE3 0AA",
    radius=0.5,    # Valid: 0.25, 0.5, 1, 3, 5, 10 (miles)
    years=5        # Valid: 2, 3, 5, 10, 15, 20 (years)
)
df = retriever.retrieve()
```

### Output Format

The returned DataFrame contains the following columns:

- `address` - Property address
- `property_type` - Type of property (e.g., "Detached", "Semi-Detached")
- `n_bedrooms` - Number of bedrooms
- `date` - Sale date
- `price` - Sale price in GBP

## Disclaimer

**This tool is for educational and personal research purposes only.**

Please ensure you:
- Respect the website's `robots.txt` and terms of service
- Use rate limiting to avoid overloading servers (the tool includes a 1-second delay between page requests)
- Do not use this for commercial purposes without proper authorization
