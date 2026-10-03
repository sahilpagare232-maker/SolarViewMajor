import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_buildings(sw_lat, sw_lon, ne_lat, ne_lon):

    query = f"""
    [out:json][timeout:60];
    (
      way["building"]({sw_lat},{sw_lon},{ne_lat},{ne_lon});
      
    );
    out ids;
    """

    headers = {
        "User-Agent": "SolarViewMajor/1.0",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers=headers,
        timeout=120
    )

    print("Status:", response.status_code)
    print("Response:", response.text[:500])

    response.raise_for_status()

    return response.json()