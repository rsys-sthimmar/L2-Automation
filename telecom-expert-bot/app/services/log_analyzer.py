import re
from typing import Dict, Any, List, Optional

from app.utils.protocol_decoder import decode_log
from app.models.query import ConfidenceLevel


class LogAnalyzer:
    def __init__(self):
        self._failure_patterns = [
            re.compile(r'\b(fail|failure|error|reject|timeout|abort)\b', re.IGNORECASE),
            re.compile(r'\b(cause|reason)\s*[=:]\s*(\w+)', re.IGNORECASE),
        ]

    async def analyze(self, log_text: str, llm_service=None) -> Dict[str, Any]:
        decoded_messages = decode_log(log_text)
        failures = self._detect_failures(log_text)
        procedure_map = self._build_procedure_map(decoded_messages)

        raw_analysis = None
        root_cause = None
        suggestions = []

        if llm_service:
            try:
                raw_analysis = await llm_service.analyze_logs(log_text)
                root_cause, suggestions = self._parse_llm_analysis(raw_analysis)
            except Exception:
                root_cause = self._infer_root_cause(failures, decoded_messages)
                suggestions = self._generate_suggestions(failures)
        else:
            root_cause = self._infer_root_cause(failures, decoded_messages)
            suggestions = self._generate_suggestions(failures)

        confidence = self._assess_confidence(decoded_messages, failures)

        return {
            "decoded_messages": decoded_messages,
            "failures": failures,
            "procedure_map": procedure_map,
            "root_cause": root_cause,
            "suggestions": suggestions,
            "confidence": confidence,
            "raw_analysis": raw_analysis,
        }

    def _detect_failures(self, log_text: str) -> List[str]:
        failures = []
        for line in log_text.splitlines():
            for pattern in self._failure_patterns:
                if pattern.search(line):
                    failures.append(line.strip())
                    break
        return failures

    def _build_procedure_map(self, decoded_messages: List[Dict]) -> Optional[str]:
        if not decoded_messages:
            return None
        lines = []
        for i, msg in enumerate(decoded_messages):
            lines.append(f"{i+1}. [{msg['domain']}] {msg['message_name']} ({msg['spec_reference']})")
        return "\n".join(lines)

    def _infer_root_cause(self, failures: List[str], decoded_messages: List[Dict]) -> Optional[str]:
        if not failures:
            return None
        if any("timeout" in f.lower() for f in failures):
            return "Possible timeout in procedure - check timer configurations"
        if any("reject" in f.lower() for f in failures):
            return "Message rejection detected - check cause codes and configuration"
        if any("fail" in f.lower() for f in failures):
            return "Failure detected in message sequence - review IE values and state machine"
        return "Failure detected - manual analysis recommended"

    def _generate_suggestions(self, failures: List[str]) -> List[str]:
        suggestions = []
        if not failures:
            return ["Log appears normal. No failures detected."]
        if any("timeout" in f.lower() for f in failures):
            suggestions.append("Check and adjust timer T3xx values per TS 38.331 Table 7.1-1")
        if any("reject" in f.lower() for f in failures):
            suggestions.append("Inspect cause IE values in rejection messages")
            suggestions.append("Verify configuration consistency between nodes")
        suggestions.append("Enable detailed logging at protocol layer for more context")
        return suggestions

    def _parse_llm_analysis(self, raw_analysis: str):
        lines = raw_analysis.splitlines()
        root_cause = None
        suggestions = []
        in_suggestions = False
        for line in lines:
            if "root cause" in line.lower():
                root_cause = line.strip()
            if "suggestion" in line.lower() or "recommend" in line.lower():
                in_suggestions = True
            if in_suggestions and line.strip().startswith(("-", "*", "•", "1", "2", "3")):
                suggestions.append(line.strip().lstrip("-*• 1234567890."))
        return root_cause, suggestions

    def _assess_confidence(self, decoded_messages: List[Dict], failures: List[str]) -> str:
        if decoded_messages and len(decoded_messages) > 3:
            return ConfidenceLevel.high
        if decoded_messages:
            return ConfidenceLevel.medium
        return ConfidenceLevel.low
