from __future__ import annotations

from oldpages_api.shared.db.ids import new_ulid


def test_new_ulid_has_expected_shape() -> None:
    public_id = new_ulid()

    assert len(public_id) == 26
    assert public_id.isalnum()
    assert public_id.upper() == public_id
