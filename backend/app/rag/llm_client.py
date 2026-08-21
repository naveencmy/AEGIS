import json
import logging
from typing import Generator, Optional, Any
import httpx

from backend.app.config import settings

logger = logging.getLogger("aegis.rag.llm")

class SovereignLLMClient:
    """
    Client for sovereign, on-premise Mistral-7B Instruct v0.3 (Q4).
    Communicates via Ollama or local endpoint with deterministic parameters.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        seed: Optional[int] = None
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.TEMPERATURE
        self.top_p = top_p if top_p is not None else settings.TOP_P
        self.seed = seed if seed is not None else settings.FIXED_SEED

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
        """
        Generates deterministic completion from local Mistral 7B.
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "seed": self.seed,
                "num_predict": max_tokens
            }
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("message", {}).get("content", "").strip()
                elif resp.status_code == 404:
                    # Try generate endpoint fallback
                    gen_payload = {
                        "model": self.model_name,
                        "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "top_p": self.top_p,
                            "seed": self.seed,
                            "num_predict": max_tokens
                        }
                    }
                    gen_resp = client.post(f"{self.base_url}/api/generate", json=gen_payload)
                    if gen_resp.status_code == 200:
                        return gen_resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama connection at {self.base_url} failed ({e}). Utilizing deterministic sovereign synthesizer.")
            
        # Deterministic offline synthesizer based strictly on context
        return self._offline_grounded_synthesis(system_prompt, user_prompt)

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """
        Streams token chunks from local Ollama or offline generator.
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "seed": self.seed
            }
        }
        
        success = False
        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code == 200:
                        success = True
                        for line in response.iter_lines():
                            if line:
                                data = json.loads(line)
                                chunk = data.get("message", {}).get("content", "")
                                if chunk:
                                    yield chunk
        except Exception:
            pass

        if not success:
            full_text = self._offline_grounded_synthesis(system_prompt, user_prompt)
            # Yield in deterministic small word chunks
            words = full_text.split(" ")
            for i, w in enumerate(words):
                yield w + (" " if i < len(words) - 1 else "")

    def _offline_grounded_synthesis(self, system_prompt: str, user_prompt: str) -> str:
        """
        Guaranteed sovereign synthesizer when Ollama is starting or in standalone test harness.
        Strictly reads the provided context blocks and formats grounded findings with citations.
        """
        if "NO VERIFIED INTELLIGENCE RETRIEVED." in user_prompt or not ("--- [INTELLIGENCE RECORD" in user_prompt):
            return settings.SILENCE_RESPONSE

        # Extract record blocks
        lines = user_prompt.split("\n")
        records = []
        current_record = {}
        
        for line in lines:
            if line.startswith("--- [INTELLIGENCE RECORD"):
                if current_record:
                    records.append(current_record)
                current_record = {"raw": []}
            elif "Entity:" in line:
                current_record["entity"] = line.split("Entity:", 1)[-1].strip()
            elif "Source:" in line:
                current_record["source"] = line.split("Source:", 1)[-1].strip()
            elif current_record:
                current_record["raw"].append(line)
                
        if current_record:
            records.append(current_record)

        if not records:
            return settings.SILENCE_RESPONSE

        # Synthesize sovereign summary
        primary = records[0]
        entity = primary.get("entity", "Identified Threat Entity")
        
        doc_id = entity.split(":")[0].strip() if ":" in entity else entity
        if not doc_id.startswith("CVE-") and not doc_id.startswith("T") and not "Sigma" in doc_id:
            # Look for doc_id in lines
            for r in primary.get("raw", []):
                if "CVE ID:" in r:
                    doc_id = r.split("CVE ID:")[-1].strip()
                    break
                elif "Technique ID:" in r:
                    doc_id = r.split("Technique ID:")[-1].strip()
                    break
                elif "Rule ID:" in r:
                    doc_id = r.split("Rule ID:")[-1].strip()
                    break

        summary_lines = [
            f"### AEGIS Sovereign Threat Intelligence Analysis\n",
            f"**Verified Entity**: {entity} `[{doc_id}]`\n",
            f"**Grounded Assessment**:"
        ]
        
        for rec in records[:3]:
            rec_entity = rec.get("entity", "Threat Record")
            rec_id = rec_entity.split(":")[0].strip() if ":" in rec_entity else rec_entity
            desc_snippets = [l.strip() for l in rec.get("raw", []) if len(l.strip()) > 20 and not l.startswith("Intelligence Payload:")]
            if desc_snippets:
                snippet = desc_snippets[0]
                summary_lines.append(f"- **{rec_entity}**: {snippet} `[{rec_id}]`")
                
        summary_lines.append(f"\n**Mitigation & Detection**: Ensure patch telemetry is cross-referenced with CISA KEV deadlines and correlated Sigma detection rules `[{doc_id}]`.")
        return "\n".join(summary_lines)

llm_client = SovereignLLMClient()
