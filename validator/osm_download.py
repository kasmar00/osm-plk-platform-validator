import json
import time
import requests
import os


def _should_load_from_cache(file) -> bool:
    return os.path.exists(file) and (
        os.path.getmtime(file) > (time.time() - 3600)
    )


def _fetch_osm_with_cache(cache_file: str, query: str):
    if _should_load_from_cache(cache_file):
        print(f"Loading OSM data from cache: {cache_file}")
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["elements"]

    print(f"Fetching OSM data from Overpass API for {cache_file}")

    endpoint = "https://overpass-api.de/api/interpreter"
    response = requests.post(endpoint, data="data=" + query)
    data = response.json()

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data["elements"]


def fetch_osm_platforms():
    query = """
    [out:json];

    area(id:3600049715)->.searchArea; //Poland

    node["railway"="stop"]["network"!="WKD"]["operator"!="WKD"](area.searchArea);
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
    return _fetch_osm_with_cache("platforms-osm.json", query)


def fetch_osm_stations():
    query = """
    [out:json];
    // fetch area “Poland” to search in
    area(id:3600049715)->.searchArea;
    // gather results
    (
      node["railway"="station"](area.searchArea);
      node["railway"="halt"](area.searchArea);
      node["disused:railway"="station"](area.searchArea);
      node["disused:railway"="halt"](area.searchArea);
    );
    // print results
    out geom;
    """
    return _fetch_osm_with_cache("stations-osm.json", query)