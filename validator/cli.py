import csv
import itertools
import json
from typing import List, NamedTuple
from .osm_download import fetch_osm_data

PLK_Platform = NamedTuple(
    "PLK_Platform", [("station_name", str), ("platform", str), ("track", str)]
)


def load_platforms_from_plk() -> List[PLK_Platform]:
    path = "platforms-plk.tsv"
    platforms = []
    with open(path, "r", encoding="utf-8") as f:
        rd = csv.reader(f, delimiter="\t", quotechar='"')
        next(rd)  # skip header
        for row in rd:
            platforms.append(PLK_Platform(*row))

    return platforms


OSM_Platform = NamedTuple(
    "OSM_Platform",
    [
        ("station_name", str),
        # ("platform", str), #TODO: not yet tracking platform refs, only track refs
        ("track", str),
        ("location", tuple[float, float]),
    ],
)


def load_platforms_from_osm() -> List[OSM_Platform]:
    platforms = []
    data = fetch_osm_data()
    for element in data:
        platforms.append(
            OSM_Platform(
                station_name=element["tags"].get("name", ""),
                track=element["tags"].get("_track_ref", ""),
                location=tuple(element["geometry"]["coordinates"]),
            )
        )

    return platforms

def compare(all_platforms: List[PLK_Platform], osm_platforms: List[OSM_Platform]) -> None:
    all_grouped = {}
    for k, v in itertools.groupby(
        sorted(all_platforms, key=lambda x: x.station_name),
        key=lambda x: x.station_name,
    ):
        all_grouped[k] = list(v)
    osm_grouped = {}
    for k, v in itertools.groupby(
        sorted(osm_platforms, key=lambda x: x.station_name),
        key=lambda x: x.station_name,
    ):
        osm_grouped[k] = list(v)

    stations_with_no_platforms = 0
    stations_with_missing_platforms = 0
    stations_with_more_platforms = 0
    for station, platforms in dict(all_grouped).items():
        platforms = list(platforms)
        osm_platforms = list(osm_grouped.get(station, []))
        if len(platforms) != len(osm_platforms):
            print(f"Station: {station} (PLK: {len(platforms)}, OSM: {len(osm_platforms)})")
            if len(osm_platforms)==0:
                stations_with_no_platforms +=1
            elif len(platforms)>len(osm_platforms):
                stations_with_missing_platforms+=1
            else:
                stations_with_more_platforms+=1

    print()
    print("Stations with no platforms in OSM:", stations_with_no_platforms)
    print("Stations with missing platforms:", stations_with_missing_platforms)
    print("Stations with more platforms in OSM than PLK:", stations_with_more_platforms)
        

def main() -> None:
    plk_platforms = load_platforms_from_plk()
    osm_platforms = load_platforms_from_osm()

    compare(plk_platforms, osm_platforms)
    print("Stats")
    print(f"PLK has {len(plk_platforms)} platforms")
    print(f"OSM has {len(osm_platforms)} platforms")
    print(f"OSM is missing {len(plk_platforms) - len(osm_platforms)} platforms, which is {100 * (len(plk_platforms) - len(osm_platforms)) / len(plk_platforms):.2f}% of PLK platforms")