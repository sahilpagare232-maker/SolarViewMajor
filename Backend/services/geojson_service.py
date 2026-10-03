def osm_to_geojson(osm_data):
    features = []

    for element in osm_data.get("elements", []):
        if element.get("type") != "way":
            continue

        geometry = element.get("geometry", [])

        if len(geometry) < 3:
            continue

        coordinates = [
            [point["lon"], point["lat"]]
            for point in geometry
        ]

        # Close polygon
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        properties = element.get("tags", {}).copy()

        properties["osm_id"] = element["id"]

        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }