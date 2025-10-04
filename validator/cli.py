import csv
import itertools
import json
from typing import List, NamedTuple, Dict
from .osm_download import fetch_osm_platforms, fetch_osm_stations
import re
from .replacement_platforms import replacement_platforms

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

    return patch_platforms(platforms)


def patch_platforms(platforms: List[PLK_Platform]) -> List[PLK_Platform]:
    patched = []

    used_replacements = set()

    for platform in platforms:
        replacement = replacement_platforms.get((platform.station_name, platform.platform, platform.track), None)
        if replacement and replacement not in used_replacements:
            patched.append(PLK_Platform(
                platform.station_name, replacement[0], replacement[1]
            ))
            used_replacements.add(replacement)
        else:
            patched.append(platform)
        
    return patched


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
    data = fetch_osm_platforms()
    for element in data:
        platforms.append(
            OSM_Platform(
                station_name=element["tags"].get("name", ""),
                track=element["tags"].get("_track_ref", ""),
                location=tuple(element["geometry"]["coordinates"]),
            )
        )

    return platforms

OSM_Station = NamedTuple(
    "OSM_Station",
    [
        ("station_name", str),
        ("location", tuple[float, float]),
    ],
)


def load_stations_from_osm() -> Dict[str, OSM_Station]:
    stations = {}
    data = fetch_osm_stations()
    for element in data:
        name = element["tags"].get("name", "")
        if name:
            stations[name] = OSM_Station(
                station_name=name,
                location=(element["lat"], element["lon"]),
            )

    return stations


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
    single_track_stations_with_missing_platforms = 0
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
            if len(platforms)==1 and len(osm_platforms)==0:
                single_track_stations_with_missing_platforms+=1

    print()
    print("Stations with no platforms in OSM:", stations_with_no_platforms)
    print("Stations with missing platforms:", stations_with_missing_platforms)
    print("Stations with more platforms in OSM than PLK:", stations_with_more_platforms)
    print("Single-track stations with missing platforms:", single_track_stations_with_missing_platforms)


Report_Platform = NamedTuple(
    "Report_Platform",
    [
        ("station_name", str),
        ("platform", str),
        ("track", str),
        ("location", tuple[float, float]),
        ("exact_location", bool),
        ("single_track_platform", bool),
    ],
)


def match_platform(
    plk: PLK_Platform, clean_track: str, osm_platforms: List[OSM_Platform]
) -> OSM_Platform | None:
    for osm in osm_platforms:
        if plk.track == osm.track:
            return osm
    for osm in osm_platforms:
        if clean_track == re.sub(r"\D", "", osm.track):
            return osm
    return None


def platform_locations(
    plk_platforms: List[PLK_Platform],
    osm_platforms: List[OSM_Platform],
    osm_stations: Dict[str, OSM_Station],
) -> Dict[str, List[Report_Platform]]:
    locations: Dict[str, List[Report_Platform]] = {}
    osm_by_station = {}

    plk_grouped: Dict[str, List[PLK_Platform]] = {}
    for k, v in itertools.groupby(
        sorted(plk_platforms, key=lambda x: x.station_name),
        key=lambda x: x.station_name,
    ):
        plk_grouped[k] = list(v)
    osm_grouped: Dict[str, List[OSM_Platform]] = {}
    for k, v in itertools.groupby(
        sorted(osm_platforms, key=lambda x: x.station_name),
        key=lambda x: x.station_name,
    ):
        osm_grouped[k] = list(v)

    missing_platforms = 0
    total_platforms = 0
    missing_stations = 0
    for station, platforms in plk_grouped.items():
        osm_platforms = osm_grouped.get(station, [])
        for plk in platforms:
            clean_track = re.sub(r"\D", "", plk.track.replace("/", ",").split(",")[0].strip())
            matched_osm = match_platform(plk, clean_track, osm_platforms)
            # TODO: fix when there are multiple platforms with the same track...

            single_track_platform = len([platform for platform in platforms if platform.platform==plk.platform]) == 1

            if matched_osm is not None:
                locations.setdefault(station, []).append(
                    Report_Platform(
                        station_name=plk.station_name,
                        platform=plk.platform,
                        track=clean_track,
                        location=matched_osm.location,
                        exact_location=True,
                        single_track_platform=single_track_platform
                    )
                )
            else:
                osm_station = osm_stations.get(station, None)
                location = list(reversed(osm_station.location)) if osm_station else None
                locations.setdefault(station, []).append(
                    Report_Platform(
                        station_name=plk.station_name,
                        platform=plk.platform,
                        track=clean_track,
                        location=location,
                        exact_location=False,
                        single_track_platform = single_track_platform
                    )
                )
                if not osm_station:
                    missing_stations += 1
                missing_platforms += 1
            total_platforms += 1

    print()
    print("=== Platform locations matching ===")
    print("Total platforms:", total_platforms)
    print("Platforms with no location in OSM:", missing_platforms)
    print("Stations with no location in OSM:", missing_stations)
    print()

    return locations

def dump_report(locations: Dict[str, List[Report_Platform]]) -> None:
    with open("platforms-report.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                station: [
                    {
                        "station_name": p.station_name,
                        "platform": p.platform,
                        "track": p.track,
                        "location": p.location,
                        "exact_location": p.exact_location,
                        "single_track_platform": p.single_track_platform,
                    }
                    for p in platforms
                ]
                for station, platforms in locations.items()
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    plk_platforms = load_platforms_from_plk()
    osm_platforms = load_platforms_from_osm()
    osm_stations = load_stations_from_osm()

    compare(plk_platforms, osm_platforms)

    locations = platform_locations(plk_platforms, osm_platforms, osm_stations)
    dump_report(locations)

    print("=== Stats ===")
    print(f"PLK has {len(plk_platforms)} platforms")
    print(f"OSM has {len(osm_platforms)} platforms")
    print(f"OSM is missing {len(plk_platforms) - len(osm_platforms)} platforms, which is {100 * (len(plk_platforms) - len(osm_platforms)) / len(plk_platforms):.2f}% of PLK platforms")
