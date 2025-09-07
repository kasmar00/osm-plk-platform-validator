import overpass
import overpy

#TODO: automate this download


def fetch_osm_data():
    # api = overpass.API()
    query = """
    //[out:json][timeout:25];

    area(id:3600130935)->.searchArea;

    node["railway"="stop"](area.searchArea);
    foreach {
        way(bn)[railway][ref] -> .ways;
        if (ways.count(ways) > 0) {
            convert result
                    ::id = id(),
                    ::geom = center(geom()),
                    _track_ref = ways.u(t["railway:track_ref"]),
                    :: = ::;
        //out geom;
        }
    };
    """
    # response = api.get(query, verbosity="geom")
    api = overpy.Overpass()
    response = api.query(query)
    # print(response.)
    print(f"Fetched: {len(response.nodes)} nodes, {len(response.ways)} ways, {len(response.relations)} relations")
    # print(f"Fetched {len(response['elements'])} elements from OSM")
    # print(
    #     [
    #         el["properties"]["name"]
    #         for el in response["elements"][:5]
    #         if "name" in el["properties"]
    #     ]
    # )
    return response
