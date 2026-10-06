import pytest
from pydantic import ValidationError
from models.area_models import AreaRequest


def test_valid_bounding_box():
    request = AreaRequest.model_validate({"coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 20, "ne_lng": 73}})
    assert request.coordinates.sw_lat == 19


@pytest.mark.parametrize("coordinates", [
    {"sw_lat": 91, "sw_lng": 72, "ne_lat": 92, "ne_lng": 73},
    {"sw_lat": 20, "sw_lng": 72, "ne_lat": 19, "ne_lng": 73},
    {"sw_lat": 19, "sw_lng": 73, "ne_lat": 20, "ne_lng": 72},
])
def test_rejects_invalid_bounds(coordinates):
    with pytest.raises(ValidationError):
        AreaRequest.model_validate({"coordinates": coordinates})
