import os
import json
import time
from typing import Dict, Any, Optional

class LLMResponseError(Exception):
    pass

class BaseLLMClient:
    def analyze(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError

class MockLLMClient(BaseLLMClient):
    def __init__(self, mode: str = "good"):
        self.mode = mode
    
    def analyze(self, prompt: str) -> Dict[str, Any]:
        if self.mode == "bad":
            return {"invalid": "response"}
        
        # Simulate processing time
        time.sleep(0.5)
        
        return {
            "root_cause": "Container OOMKilled due to memory limit exhaustion",
            "supporting_evidence_ids": ["E1", "E2"],
            "confidence": 0.85
        }

class OpenAILLMClient(BaseLLMClient):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "10"))
    
    def analyze(self, prompt: str) -> Dict[str, Any]:
        start = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a production incident analysis engine. Respond in JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content.strip())
            
            if time.time() - start > self.timeout:
                raise LLMResponseError("LLM response timeout")
            
            return parsed
            
        except json.JSONDecodeError:
            raise LLMResponseError("LLM returned invalid JSON")
        except Exception as e:
            raise LLMResponseError(str(e))

def get_llm_client(mode: str = "good", provider: Optional[str] = None):
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "mock")
    
    if provider == "openai":
        try:
            return OpenAILLMClient()
        except Exception as e:
            print(f"OpenAI client failed: {e}, falling back to mock")
            return MockLLMClient(mode=mode)
    
    return MockLLMClient(mode=mode)
