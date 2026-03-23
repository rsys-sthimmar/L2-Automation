from typing import Dict, List, Optional


DOMAIN_SPEC_MAP: Dict[str, Dict] = {
    "RRC": {
        "spec": "TS 38.331",
        "title": "NR; Radio Resource Control (RRC) Protocol Specification",
        "release": "R15+",
        "sections": ["4 General", "5 Procedures", "6 Protocol Data Units", "7 Variables and Constants"],
    },
    "NGAP": {
        "spec": "TS 38.413",
        "title": "NG-RAN; NG Application Protocol (NGAP)",
        "release": "R15+",
        "sections": ["8 General", "9 NGAP Procedures", "10 Elements of Information"],
    },
    "F1AP": {
        "spec": "TS 38.473",
        "title": "NG-RAN; F1 Application Protocol (F1AP)",
        "release": "R15+",
        "sections": ["8 General", "9 F1AP Procedures", "10 Elements of Information"],
    },
    "MAC": {
        "spec": "TS 38.321",
        "title": "NR; Medium Access Control (MAC) Protocol Specification",
        "release": "R15+",
        "sections": ["5 MAC Procedures", "6 MAC Protocol Data Unit Structure"],
    },
    "PHY": {
        "spec": "TS 38.211",
        "title": "NR; Physical Channels and Modulation",
        "release": "R15+",
        "sections": ["4 Definitions", "5 Uplink", "6 Downlink", "7 Reference Signals"],
    },
    "NTN": {
        "spec": "TS 38.821",
        "title": "Solutions for NR to support Non-Terrestrial Networks (NTN)",
        "release": "R17+",
        "sections": ["4 System aspects", "5 NTN channel model", "6 Procedures"],
    },
    "PDCP": {
        "spec": "TS 38.323",
        "title": "NR; Packet Data Convergence Protocol (PDCP) Specification",
        "release": "R15+",
        "sections": ["5 PDCP Procedures", "6 PDCP PDU Structure"],
    },
    "RLC": {
        "spec": "TS 38.322",
        "title": "NR; Radio Link Control (RLC) Protocol Specification",
        "release": "R15+",
        "sections": ["5 RLC Procedures", "6 RLC PDU Structure"],
    },
    "5GC": {
        "spec": "TS 23.501",
        "title": "System Architecture for the 5G System",
        "release": "R15+",
        "sections": ["4 Architecture", "5 Network Functions", "6 Procedures"],
    },
}

KEYWORD_DOMAIN_MAP: Dict[str, str] = {
    "rrc": "RRC",
    "radio resource control": "RRC",
    "rrcsetup": "RRC",
    "handover": "RRC",
    "measurement": "RRC",
    "sib": "RRC",
    "mib": "RRC",
    "ngap": "NGAP",
    "ng application": "NGAP",
    "amf": "NGAP",
    "pdu session": "5GC",
    "f1ap": "F1AP",
    "f1 application": "F1AP",
    "du": "F1AP",
    "cu": "F1AP",
    "mac": "MAC",
    "medium access": "MAC",
    "scheduling": "MAC",
    "harq": "MAC",
    "bsr": "MAC",
    "phy": "PHY",
    "physical": "PHY",
    "prach": "PHY",
    "pdcch": "PHY",
    "pdsch": "PHY",
    "pusch": "PHY",
    "pucch": "PHY",
    "ntn": "NTN",
    "non-terrestrial": "NTN",
    "satellite": "NTN",
    "pdcp": "PDCP",
    "rlc": "RLC",
}


def detect_domain_from_query(query: str) -> Optional[str]:
    query_lower = query.lower()
    for keyword, domain in KEYWORD_DOMAIN_MAP.items():
        if keyword in query_lower:
            return domain
    return None


def map_to_spec_reference(domain: str, query: str = "") -> Dict:
    domain_upper = domain.upper()
    if domain_upper in DOMAIN_SPEC_MAP:
        return DOMAIN_SPEC_MAP[domain_upper]
    detected = detect_domain_from_query(query)
    if detected and detected in DOMAIN_SPEC_MAP:
        return DOMAIN_SPEC_MAP[detected]
    return {}


def get_spec_sections(spec_number: str) -> List[str]:
    for domain_info in DOMAIN_SPEC_MAP.values():
        if domain_info["spec"] == spec_number:
            return domain_info["sections"]
    return []


def get_all_specs() -> Dict[str, str]:
    return {domain: info["spec"] for domain, info in DOMAIN_SPEC_MAP.items()}
