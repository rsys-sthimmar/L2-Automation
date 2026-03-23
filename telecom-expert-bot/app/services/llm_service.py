import json
import re
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

TELECOM_SYSTEM_PROMPT = """You are a Telecommunications Expert AI specializing in 3GPP specifications (R15-R19), including RRC, NGAP, F1AP, MAC, PHY, and NTN.

Your responsibilities:
1. Always cite spec references (TS number, section)
2. Provide structured responses: explanation, reference, message flow, edge cases
3. Identify domain (RRC, NGAP, F1AP, NTN, MAC, PHY, etc.)
4. For log analysis: decode messages, identify failures, suggest root cause
5. For test plans: include objective, preconditions, steps, expected results, negative scenarios
6. Confidence levels: High (directly from spec), Medium (derived), Low (inference)
7. Do not hallucinate 3GPP references
8. Be precise and technical"""


class LLMService:
    def __init__(self):
        self._client = None
        self._provider = settings.llm_provider

    def _get_client(self):
        if self._client is None:
            if self._provider == "azure":
                from openai import AsyncAzureOpenAI
                self._client = AsyncAzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_version=settings.azure_openai_api_version,
                )
            else:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    def _get_model(self) -> str:
        if self._provider == "azure":
            return settings.azure_openai_deployment or "gpt-4"
        return settings.openai_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_llm(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self._get_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content

    async def query(self, user_message: str, context: Optional[str] = None) -> Dict[str, Any]:
        messages = [{"role": "system", "content": TELECOM_SYSTEM_PROMPT}]
        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant specification context:\n{context}"
            })
        messages.append({"role": "user", "content": user_message})

        response_text = await self._call_llm(messages)

        return {
            "answer": response_text,
            "references": self._extract_references(response_text),
            "confidence": self._assess_confidence(response_text),
            "domain": self._extract_domain(response_text),
            "message_flow": self._extract_message_flow(response_text),
            "edge_cases": self._extract_edge_cases(response_text),
        }

    async def analyze_logs(self, log_data: str) -> str:
        messages = [
            {"role": "system", "content": TELECOM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze the following telecom log and provide:\n"
                    f"1. Decoded message sequence\n"
                    f"2. Identified failures or anomalies\n"
                    f"3. Root cause analysis\n"
                    f"4. Suggestions for resolution\n\n"
                    f"Log data:\n{log_data}"
                ),
            },
        ]
        return await self._call_llm(messages, max_tokens=3000)

    async def generate_test_plan(self, feature: str, domain: str, requirements: Optional[List[str]] = None) -> str:
        req_text = "\n".join(f"- {r}" for r in requirements) if requirements else "No specific requirements provided."
        messages = [
            {"role": "system", "content": TELECOM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate a comprehensive test plan for:\n"
                    f"Feature: {feature}\n"
                    f"Domain: {domain}\n"
                    f"Requirements:\n{req_text}\n\n"
                    f"Include: objective, preconditions, test steps, expected results, "
                    f"negative scenarios, KPIs, and 3GPP references."
                ),
            },
        ]
        return await self._call_llm(messages, max_tokens=3000)

    def _extract_references(self, text: str) -> List[str]:
        pattern = re.compile(r'TS\s+\d+\.\d+(?:\s+[Ss]ection\s+[\d.]+)?', re.IGNORECASE)
        return list(set(pattern.findall(text)))

    def _assess_confidence(self, text: str) -> str:
        text_lower = text.lower()
        if "high confidence" in text_lower or "directly specified" in text_lower:
            return "high"
        if "low confidence" in text_lower or "inferred" in text_lower or "not specified" in text_lower:
            return "low"
        return "medium"

    def _extract_domain(self, text: str) -> Optional[str]:
        from app.utils.reference_mapper import detect_domain_from_query
        return detect_domain_from_query(text)

    def _extract_message_flow(self, text: str) -> Optional[str]:
        lines = text.splitlines()
        flow_lines = []
        in_flow = False
        for line in lines:
            if re.search(r'message flow|sequence|procedure', line, re.IGNORECASE):
                in_flow = True
            if in_flow:
                flow_lines.append(line)
                if len(flow_lines) > 20:
                    break
        return "\n".join(flow_lines) if flow_lines else None

    def _extract_edge_cases(self, text: str) -> Optional[List[str]]:
        lines = text.splitlines()
        edge_cases = []
        in_edge = False
        for line in lines:
            if re.search(r'edge case|corner case|exception|failure case', line, re.IGNORECASE):
                in_edge = True
            if in_edge and line.strip().startswith(("-", "*", "•")):
                edge_cases.append(line.strip().lstrip("-*• "))
        return edge_cases if edge_cases else None
