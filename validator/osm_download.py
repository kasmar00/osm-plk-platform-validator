import json
import time
import requests
import os


def should_load_from_cache() -> bool:
    return os.path.exists("platforms-osm.json") and (
        os.path.getmtime("platforms-osm.json") > (time.time() - 86400)
    )


def fetch_osm_data():
    if should_load_from_cache():
        print("Loading OSM data from cache")
        with open("platforms-osm.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["elements"]

    print("Fetching OSM data from Overpass API")

    query = """
    [out:json];

    area(id:3600049715)->.searchArea; //Poland


    node["railway"="stop"](area.searchArea);
    foreach {
    way(bn)[railway] -> .ways;
    if (ways.count(ways) > 0) {
        convert result
                ::id = id(),
                ::geom = center(geom()),
                _track_ref = ways.u(t["railway:track_ref"]),
                :: = ::;
    (._;>;);
    out geom;
    }
    }
"""
    endpoint = "https://overpass-api.de/api/interpreter"
    response = requests.post(endpoint, data="data=" + query)
    data = response.json()

    with open("platforms-osm.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data["elements"]
