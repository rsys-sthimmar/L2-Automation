import re
from typing import Dict, Any, List, Optional

from app.utils.reference_mapper import map_to_spec_reference


class TestPlanGenerator:
    async def generate(
        self,
        feature: str,
        domain: str,
        requirements: Optional[List[str]] = None,
        llm_service=None,
    ) -> Dict[str, Any]:
        spec_info = map_to_spec_reference(domain)
        spec_ref = spec_info.get("spec", f"TS for {domain}")

        if llm_service:
            try:
                raw = await llm_service.generate_test_plan(feature, domain, requirements)
                return self._parse_llm_test_plan(raw, feature, domain, spec_ref)
            except Exception:
                pass

        return self._generate_default_plan(feature, domain, requirements, spec_ref)

    def _generate_default_plan(
        self,
        feature: str,
        domain: str,
        requirements: Optional[List[str]],
        spec_ref: str,
    ) -> Dict[str, Any]:
        return {
            "objective": f"Verify {feature} functionality in {domain} domain per {spec_ref}",
            "preconditions": [
                f"UE supports {domain} capabilities",
                f"Network configured per {spec_ref}",
                "Test environment is stable and calibrated",
                "All required equipment is connected and operational",
            ],
            "steps": [
                {"step": 1, "action": "Initialize test environment", "description": f"Configure UE and network for {domain}"},
                {"step": 2, "action": f"Trigger {feature}", "description": "Initiate the feature under test"},
                {"step": 3, "action": "Monitor message exchange", "description": f"Capture and verify {domain} messages"},
                {"step": 4, "action": "Verify completion", "description": "Confirm successful feature execution"},
                {"step": 5, "action": "Verify KPIs", "description": "Check performance indicators meet requirements"},
            ],
            "expected_results": [
                f"{feature} completes successfully",
                f"All {domain} messages conform to {spec_ref}",
                "No unexpected failures or timeouts",
                "KPIs within acceptable thresholds",
            ],
            "negative_scenarios": [
                {
                    "scenario": "Network unavailable",
                    "action": "Remove network connectivity during feature execution",
                    "expected": "Appropriate failure handling and recovery",
                },
                {
                    "scenario": "Invalid configuration",
                    "action": "Configure with unsupported parameters",
                    "expected": "Rejection with correct cause code",
                },
                {
                    "scenario": "Timer expiry",
                    "action": "Block response to trigger timeout",
                    "expected": "Timer-based recovery procedure triggered",
                },
            ],
            "kpis": [
                f"{feature} setup success rate > 99%",
                f"{feature} latency within spec limits",
                "Zero protocol errors",
            ],
            "references": [spec_ref] + ([r for r in (requirements or [])] if requirements else []),
        }

    def _parse_llm_test_plan(self, raw: str, feature: str, domain: str, spec_ref: str) -> Dict[str, Any]:
        lines = raw.splitlines()
        objective = f"Verify {feature} functionality in {domain} domain"
        preconditions = []
        steps = []
        expected_results = []
        negative_scenarios = []
        kpis = []
        references = [spec_ref]

        current_section = None
        step_num = 1

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            lower = line_stripped.lower()
            if "objective" in lower:
                current_section = "objective"
                objective = line_stripped
            elif "precondition" in lower:
                current_section = "preconditions"
            elif "step" in lower and ("test" in lower or "procedure" in lower):
                current_section = "steps"
            elif "expected result" in lower:
                current_section = "expected_results"
            elif "negative" in lower or "corner case" in lower:
                current_section = "negative_scenarios"
            elif "kpi" in lower or "metric" in lower:
                current_section = "kpis"
            elif "reference" in lower:
                current_section = "references"
            elif line_stripped.startswith(("-", "*", "•")):
                content = line_stripped.lstrip("-*• ")
                if current_section == "preconditions":
                    preconditions.append(content)
                elif current_section == "steps":
                    steps.append({"step": step_num, "action": content, "description": content})
                    step_num += 1
                elif current_section == "expected_results":
                    expected_results.append(content)
                elif current_section == "kpis":
                    kpis.append(content)

        if not preconditions:
            preconditions = [f"UE supports {domain} capabilities", f"Network configured per {spec_ref}"]
        if not steps:
            steps = [{"step": 1, "action": "Execute test", "description": f"Test {feature}"}]
        if not expected_results:
            expected_results = [f"{feature} executes successfully per {spec_ref}"]

        return {
            "objective": objective,
            "preconditions": preconditions,
            "steps": steps,
            "expected_results": expected_results,
            "negative_scenarios": negative_scenarios,
            "kpis": kpis,
            "references": references,
        }
