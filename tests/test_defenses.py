from gridpoisonrag.defenses import validate_against_record


ITEM = {"item_id": "T2-001", "value": 50.0, "tolerance": 0.0}


def test_record_match_passes():
    d = validate_against_record(ITEM, "VALUE: 50 MVA\nRATIONALE: x", covered=True)
    assert not d.flagged


def test_record_mismatch_flags():
    d = validate_against_record(ITEM, "VALUE: 60 MVA\nRATIONALE: x", covered=True)
    assert d.flagged
    assert "UNKNOWN" in d.answer


def test_uncovered_does_not_oracle():
    d = validate_against_record(ITEM, "VALUE: 60 MVA\nRATIONALE: x", covered=False)
    assert not d.flagged
    assert "60" in d.answer
