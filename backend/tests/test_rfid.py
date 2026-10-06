import pytest
from fastapi import HTTPException

from app.rfid import canonical_rfid_uid


def test_rfid_uid_normalization_accepts_common_formats():
    assert canonical_rfid_uid("E9 AE 14 05") == "E9AE1405"
    assert canonical_rfid_uid("e9:ae:14:05") == "E9AE1405"
    assert canonical_rfid_uid("e9-ae-14-05") == "E9AE1405"


@pytest.mark.parametrize("value", ["", "abc", "E9 AE 14 0Z", "1234567", "123456789"])
def test_rfid_uid_normalization_rejects_malformed_values(value):
    with pytest.raises(HTTPException) as error:
        canonical_rfid_uid(value)
    assert error.value.status_code == 422
