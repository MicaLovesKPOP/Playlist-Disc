from playlistdisc.checksum import damm_digit, damm_validate


def test_known_vector():
    assert damm_digit("1123456") == 3
    assert damm_validate("11234563")


def test_single_digit_change_fails():
    assert not damm_validate("11234573")


def test_adjacent_transposition_fails():
    assert not damm_validate("11235463")
