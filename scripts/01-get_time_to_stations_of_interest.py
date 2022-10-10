import datetime
import os
from typing import List

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm


def main(station_coords_path: str, output_path: str) -> None:
    load_dotenv()

    station_coords_df = pd.read_csv(station_coords_path)
    soi_min_route_duration_df = get_min_route_duration_to_stations_of_interest(
        stations_of_interest=["Victoria", "Eastcote"],
        station_coords_df=station_coords_df,
        cm_api_key=os.getenv("CM_API_KEY"),
    )

    soi_min_route_duration_df.to_csv(output_path)


def get_min_route_duration_to_stations_of_interest(
    stations_of_interest: List[str], station_coords_df: pd.DataFrame, cm_api_key: str
) -> pd.DataFrame:
    """Obtain the time of the fastest routes to stations of interest.

    To a set of stations of interest, find the fastest routes from any other
    station.

    Parameters
    ----------
    stations_of_interest : List[str]
        names of the stations of interest.
    station_coords_df : pd.DataFrame
        contains the coords of all stations.
    cm_api_key : str
        CityMapper API key.

    Returns
    -------
    pd.DataFrame
        contains the duration of the fastest routes to each station of interest
        in minutes.
    """

    # city mapper API expects strings
    station_coords_df["x"] = station_coords_df["x"].astype(str)
    station_coords_df["y"] = station_coords_df["y"].astype(str)

    soi_min_route_duration = list()

    for soi in stations_of_interest:

        min_route_duration = list()
        stations = list()

        soi_df = station_coords_df.loc[station_coords_df["NAME"] == soi].copy()

        for station in tqdm(station_coords_df.itertuples()):

            if station.NAME == soi:
                continue

            # the duration of each route is based on next tuesday at 8am
            # next being the following tuesday from when this script is run
            min_route_duration.append(
                get_min_route_duration(
                    cm_api_key=cm_api_key,
                    coords_a=[soi_df["y"].values[0], soi_df["x"].values[0]],
                    coords_b=[station.y, station.x],
                    date_time=get_next_tuesday_iso(hour=8),
                )
            )

            stations.append(station.NAME)

        soi_min_route_duration.append(
            pd.DataFrame(
                {"soi": [soi for _ in stations], "station": stations, "min_route_duration": min_route_duration}
            )
        )

    soi_min_route_duration_df = pd.concat(soi_min_route_duration)

    return soi_min_route_duration_df


def get_next_tuesday_iso(hour: int) -> str:
    """Obtain the date of next Tuesday in an ISO 8601 format.

    Parameters
    ----------
    hour : int
        the hour to be set in the returned date.

    Returns
    -------
    str
        date and time of next Tuesday in an ISO 8601 format.
    """
    today = datetime.datetime.today().replace(hour=hour, minute=00)

    # weekday() returns a int specifying the day e.g. Mon = 0, Tues = 1 etc
    days_diff = 1 - today.weekday()

    # if tuesday has already passed, we move to next week
    if days_diff <= 0:
        days_diff += 7

    next_tues = today + datetime.timedelta(days_diff)

    # convert to iso 8601 format
    next_tues_iso = next_tues.replace(tzinfo=datetime.timezone.utc).isoformat()

    return next_tues_iso


def get_min_route_duration(cm_api_key: str, coords_a: List[str], coords_b: List[str], date_time: str) -> float:
    """Obtain the duration of the fastest route between two places.

    Parameters
    ----------
    cm_api_key : str
        CityMapper API key.
    coords_a : List[str]
        coordinates of first place of interest.
    coords_b : List[str]
        coordinates of second place of interest.
    date_time : str
        the date and time on which to calculate the route durations.

    Returns
    -------
    float
        duration of the fastest route between the two places in minutes.
    """
    headers = {"Citymapper-Partner-Key": cm_api_key}
    params = {
        "start": ",".join(coords_a),
        "end": ",".join(coords_b),
        "time": date_time,
        "time_type": "depart",
    }
    attempt = 0
    min_transit_duration = None

    # try 2 times as API is sometimes flaky
    while attempt < 2 and min_transit_duration is None:
        try:
            attempt += 1
            cm_response = requests.get(
                url="https://api.external.citymapper.com/api/1/directions/transit", params=params, headers=headers
            )
            min_transit_duration = min([route["duration_seconds"] / 60 for route in cm_response.json()["routes"]])
        except KeyError:
            min_transit_duration = None

    return min_transit_duration


if __name__ == "__main__":
    main("data/raw/london_stations_coords.csv", "data/processed/soi_min_route_duration.csv")
