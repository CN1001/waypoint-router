from app.routing import build_osrm_url, normalize_osrm_routes, parse_coordinate_pair


def test_parse_coordinate_pair_returns_lat_lng_floats():
    point = parse_coordinate_pair("13.7563,100.5018")

    assert point.lat == 13.7563
    assert point.lng == 100.5018


def test_parse_coordinate_pair_rejects_out_of_range_latitude():
    try:
        parse_coordinate_pair("91,100.5018")
    except ValueError as exc:
        assert "Latitude" in str(exc)
    else:
        raise AssertionError("Expected invalid latitude to raise ValueError")


def test_parse_coordinate_pair_rejects_missing_lng_value():
    try:
        parse_coordinate_pair("13.7563")
    except ValueError as exc:
        assert "lat,lng" in str(exc)
    else:
        raise AssertionError("Expected malformed coordinate to raise ValueError")


def test_build_osrm_url_two_waypoints_uses_lng_lat_order_and_includes_alternatives():
    a = parse_coordinate_pair("13.7563,100.5018")
    b = parse_coordinate_pair("13.7367,100.5231")

    url = build_osrm_url([a, b])

    assert "100.5018,13.7563;100.5231,13.7367" in url
    assert "alternatives=true" in url
    assert "geometries=geojson" in url


def test_build_osrm_url_three_waypoints_includes_all_stops_and_omits_alternatives():
    a = parse_coordinate_pair("13.7563,100.5018")
    b = parse_coordinate_pair("13.7450,100.5100")
    c = parse_coordinate_pair("13.7367,100.5231")

    url = build_osrm_url([a, b, c])

    assert "100.5018,13.7563;100.51,13.745;100.5231,13.7367" in url
    assert "alternatives" not in url


def test_normalize_osrm_routes_converts_geojson_lng_lat_to_leaflet_lat_lng():
    payload = {
        "routes": [
            {
                "distance": 1200.5,
                "duration": 300.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[100.5018, 13.7563], [100.5231, 13.7367]],
                },
            }
        ]
    }

    result = normalize_osrm_routes(payload)

    assert result["routes"][0]["id"] == "route-1"
    assert result["routes"][0]["distanceMeters"] == 1200.5
    assert result["routes"][0]["durationSeconds"] == 300.0
    assert result["routes"][0]["coordinates"] == [[13.7563, 100.5018], [13.7367, 100.5231]]
