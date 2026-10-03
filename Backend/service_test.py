import json

from services.overpass_service import get_buildings
from services.geojson_service import osm_to_geojson


# Data saved from previous Select Area test
area ={'sw_lat': 19.075449296017254, 'sw_lng': 72.87907953388093, 'ne_lat': 19.077153691579184, 'ne_lng': 72.88333315714681}


def main():
    print("Getting buildings from Overpass...")

    osm_data = get_buildings(
        area["sw_lat"],
        area["sw_lng"],
        area["ne_lat"],
        area["ne_lng"]
    )

    print(
        f"Received {len(osm_data.get('elements', []))} OSM elements"
    )

    print("Converting OSM data to GeoJSON...")

    geojson = osm_to_geojson(osm_data)

    print(
        f"Converted {len(geojson['features'])} buildings"
    )

    # Save GeoJSON
    with open(
        "buildings.geojson",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            geojson,
            file,
            indent=2
        )

    print("GeoJSON saved to buildings.geojson")


if __name__ == "__main__":
    main()