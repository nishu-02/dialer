import phonenumbers


def normalize_and_classify(raw: str):
    try:
        parsed = phonenumbers.parse(raw, "IN")
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    region = "national" if phonenumbers.region_code_for_number(parsed) == "IN" else "international"
    return {"e164": e164, "region": region}


def _self_check():
    assert normalize_and_classify("9876543210")["region"] == "national"
    assert normalize_and_classify("+919876543210")["region"] == "national"
    assert normalize_and_classify("+14155552671")["region"] == "international"
    assert normalize_and_classify("not a number") is None
    assert normalize_and_classify("") is None
    print("phone.py self-check passed")


if __name__ == "__main__":
    _self_check()
