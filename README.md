# rightprice

What is the right price for your property of interest?

## Installation

I recommend using [uv](https://docs.astral.sh/uv/) to manage the python version, virtual environment and `rightprice` installation:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install rightprice
```

## Additional setup

### Code coverage

- Add a "CODECOV_TOKEN" secret (obtained from [here](https://app.codecov.io/gh/dzhang32/test_python_package/)) to your repo via `Settings` -> `Secrets and variables` -> `Actions`. 


### Deploying docs to gh-pages

1. Go to your repository's `Settings` -> `Actions` -> `General`.
2. Scroll to `Workflow permissions` and allow GHA to have `Read and write permissions` so it can create/push to the `gh-pages` branch.
3. Go to `Settings` -> `Pages`.
4. Configure your repo to deploy from the root of `gh-pages` branch.




### Deploying to PyPI

- Go to your [PyPi publishing settings](https://pypi.org/manage/account/publishing/) and fill in the following details:

    - **PyPI Project Name:** rightprice
    - **Owner:** dzhang32
    - **Repository name:** rightprice
    - **Workflow name:** test_deploy.yml
    - **Environment name:** (leave blank)

