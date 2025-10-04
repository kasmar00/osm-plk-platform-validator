# OSM <=> PLK Platform Validator

## Glossary
- platform - pol. "Peron"
- track - pol. "Tor"
- station - means all places where passengers can board and disembark from trains: stations, stops (halts), etc. pol. "Stacja", "Przystanek", etc.

## Plan
1. Get a list of platforms (tracks) from PLK
1. Get all stations, platforms and stop positions (with tracks) from OSM
1. Assign each platform and stop position to a station
1. Get track number for each stop position
1. Compare the list of tracks and platforms from PLK with the list from OSM
1. Generate a report
1. publish report

## Query
```c
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
```
