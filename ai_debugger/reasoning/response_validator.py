from typing import Dict, List, Any

class InvalidRCAResponse(Exception):
    pass

def validate_rca_response(response: Dict[str, Any], evidence: List[Dict]) -> Dict[str, Any]:
    required_keys = {"root_cause", "supporting_evidence_ids", "confidence"}
    
    if not required_keys.issubset(response.keys()):
        raise InvalidRCAResponse(f"Missing required fields: {required_keys - response.keys()}")
    
    if not isinstance(response["supporting_evidence_ids"], list):
        raise InvalidRCAResponse("supporting_evidence_ids must be a list")
    
    if not isinstance(response["confidence"], (int, float)):
        raise InvalidRCAResponse("confidence must be a number")
    
    if not (0.0 <= response["confidence"] <= 1.0):
        raise InvalidRCAResponse("confidence must be between 0 and 1")
    
    valid_ids = {e.get("id") for e in evidence if e.get("id")}
    
    for eid in response["supporting_evidence_ids"]:
        if eid not in valid_ids:
            raise InvalidRCAResponse(f"Invalid evidence reference: {eid}")
    
    return response
