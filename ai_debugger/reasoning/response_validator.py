class InvalidRCAResponse(Exception):
    pass


def validate_rca_response(response, evidence):
    required_keys = {"root_cause", "supporting_evidence_ids", "confidence"}

    if not required_keys.issubset(response):
        raise InvalidRCAResponse("Missing required RCA fields")

    if not isinstance(response["supporting_evidence_ids"], list):
        raise InvalidRCAResponse("supporting_evidence_ids must be a list")

    if not (0.0 <= response["confidence"] <= 1.0):
        raise InvalidRCAResponse("confidence must be between 0 and 1")

    valid_ids = {e["id"] for e in evidence}

    for eid in response["supporting_evidence_ids"]:
        if eid not in valid_ids:
            raise InvalidRCAResponse(f"Invalid evidence reference: {eid}")

    return response
