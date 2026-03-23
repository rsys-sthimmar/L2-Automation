import re
from typing import Dict, List, Optional, Any


SPEC_REFERENCE_MAP = {
    "RRCSetup": ("TS 38.331", "6.2.2"),
    "RRCSetupComplete": ("TS 38.331", "6.2.2"),
    "RRCSetupRequest": ("TS 38.331", "6.2.2"),
    "RRCReestablishment": ("TS 38.331", "6.2.2"),
    "RRCReestablishmentRequest": ("TS 38.331", "6.2.2"),
    "RRCReestablishmentComplete": ("TS 38.331", "6.2.2"),
    "RRCRelease": ("TS 38.331", "6.2.2"),
    "RRCReconfiguration": ("TS 38.331", "6.2.2"),
    "RRCReconfigurationComplete": ("TS 38.331", "6.2.2"),
    "MeasurementReport": ("TS 38.331", "6.2.2"),
    "InitialUEMessage": ("TS 38.413", "9.2.5"),
    "InitialContextSetupRequest": ("TS 38.413", "9.2.1"),
    "InitialContextSetupResponse": ("TS 38.413", "9.2.1"),
    "NGSetupRequest": ("TS 38.413", "9.2.6"),
    "NGSetupResponse": ("TS 38.413", "9.2.6"),
    "UEContextReleaseRequest": ("TS 38.413", "9.2.3"),
    "UEContextReleaseCommand": ("TS 38.413", "9.2.3"),
    "UEContextReleaseComplete": ("TS 38.413", "9.2.3"),
    "PathSwitchRequest": ("TS 38.413", "9.2.4"),
    "F1SetupRequest": ("TS 38.473", "9.2.7"),
    "F1SetupResponse": ("TS 38.473", "9.2.7"),
    "UEContextSetupRequest": ("TS 38.473", "9.2.1"),
    "UEContextSetupResponse": ("TS 38.473", "9.2.1"),
    "DLRRCMessageTransfer": ("TS 38.473", "9.2.4"),
    "ULRRCMessageTransfer": ("TS 38.473", "9.2.4"),
    "Paging": ("TS 38.331", "6.2.2"),
    "SystemInformation": ("TS 38.331", "6.2.2"),
    "MIB": ("TS 38.331", "6.2.2"),
    "SIB1": ("TS 38.331", "6.2.2"),
}

DOMAIN_PATTERNS = {
    "RRC": re.compile(r"\bRRC\w+|\bMIB\b|\bSIB\d*\b", re.IGNORECASE),
    "NGAP": re.compile(r"\bNG\w+|\bInitialUEMessage\b|\bUEContextRelease\b", re.IGNORECASE),
    "F1AP": re.compile(r"\bF1\w+|\bDLRRC\w+|\bULRRC\w+", re.IGNORECASE),
    "MAC": re.compile(r"\bMAC\w+|\bBSR\b|\bSR\b|\bRAR\b", re.IGNORECASE),
    "PHY": re.compile(r"\bPRACH\b|\bPDCCH\b|\bPDSCH\b|\bPUSCH\b|\bPUCCH\b", re.IGNORECASE),
}


def detect_domain(message_name: str) -> str:
    for domain, pattern in DOMAIN_PATTERNS.items():
        if pattern.search(message_name):
            return domain
    return "UNKNOWN"


def extract_ies(log_line: str) -> Dict[str, str]:
    ies = {}
    ie_pattern = re.compile(r'(\w+)\s*[=:]\s*([^\s,;]+)')
    for match in ie_pattern.finditer(log_line):
        key, value = match.group(1), match.group(2)
        if key not in ("INFO", "DEBUG", "ERROR", "WARNING", "WARN"):
            ies[key] = value
    return ies


def decode_message(log_line: str) -> Optional[Dict[str, Any]]:
    # Sort by length descending so longer/more-specific names match before shorter ones
    known_messages = sorted(SPEC_REFERENCE_MAP.keys(), key=len, reverse=True)
    for msg_name in known_messages:
        if msg_name.lower() in log_line.lower():
            spec, section = SPEC_REFERENCE_MAP[msg_name]
            domain = detect_domain(msg_name)
            ies = extract_ies(log_line)
            return {
                "message_name": msg_name,
                "domain": domain,
                "spec_reference": f"{spec} Section {section}",
                "information_elements": ies,
                "raw_line": log_line.strip(),
            }
    return None


def decode_log(log_text: str) -> List[Dict[str, Any]]:
    decoded = []
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue
        result = decode_message(line)
        if result:
            decoded.append(result)
    return decoded


class RRCDecoder:
    def decode(self, log_line: str) -> Optional[Dict[str, Any]]:
        result = decode_message(log_line)
        if result and result["domain"] == "RRC":
            return result
        return None


class NGAPDecoder:
    def decode(self, log_line: str) -> Optional[Dict[str, Any]]:
        result = decode_message(log_line)
        if result and result["domain"] == "NGAP":
            return result
        return None


class F1APDecoder:
    def decode(self, log_line: str) -> Optional[Dict[str, Any]]:
        result = decode_message(log_line)
        if result and result["domain"] == "F1AP":
            return result
        return None
