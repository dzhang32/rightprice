# rightprice

[![test_deploy](https://github.com/dzhang32/rightprice/actions/workflows/test_deploy.yml/badge.svg)](https://github.com/dzhang32/autogroceries/actions/rightprice/test_deploy.yml)
[![codecov](https://codecov.io/gh/dzhang32/rightprice/branch/main/graph/badge.svg)](https://codecov.io/gh/dzhang32/rightprice)
[![pypi](https://img.shields.io/pypi/v/rightprice.svg)](https://pypi.org/project/rightprice/)

`rightprice` helps you decide whether the property you want to buy is worth the price by retrieving the prices of sold houses.

## Installation

I recommend using [uv](https://docs.astral.sh/uv/) to manage the Python version, virtual environment and `rightprice` installation:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install rightprice
```

## Usage

`rightprice` retrieves sold property prices for a given UK postcode. `rightprice` is designed to be used as a CLI tool, with a single command:

```bash
> rightprice retrieve-sold-prices --help
Usage: rightprice retrieve-sold-prices [OPTIONS] POSTCODE

  Retrieve sold property prices for a given postcode.

Options:
  --radius FLOAT         Search radius in miles. Valid values: 0.25, 0.5, 1,
                         3, 5, 10.
  --years INTEGER        Number of years back to search. Valid values: 2, 3,
                         5, 10, 15, 20.
  -o, --output-dir PATH  Output directory. Defaults to current directory.
  --help                 Show this message and exit.
```

### Output Format

The output `.csv` will be named based on the input parameters (e.g., `se3-0aa_radius-0.5_years-5.csv`) and contain the following columns:

| address | property_type | n_bedrooms | date | price |
|---------|---------------|------------|------|-------|
| 123 Main Street, London | Semi-Detached | 3 | 15 Jan 2024 | 575000 |
| 45 Park Road, London | Terraced | 2 | 03 Dec 2023 | 425000 |
| 78 High Street, London | Detached | 4 | 22 Nov 2023 | 750000 |

## Disclaimer

️`rightprice` is developed for **educational use only**. Users are responsible for:

- Following website's `robots.txt` and Terms of Service.
- Using appropriate delays and respecting rate limits.
- Complying with applicable laws.
