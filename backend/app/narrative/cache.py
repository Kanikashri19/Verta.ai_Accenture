import hashlib
import json
from typing import Dict, Optional, Any
from app.narrative.models import NarrativeResponse, Persona

class NarrativeCache:
    """
    Deterministic in-memory LRU / hash-based cache for narrative responses.
    Prevents redundant external LLM invocations for identical analytical payloads.
    """

    def __init__(self, max_size: int = 256):
        self._cache: Dict[str, NarrativeResponse] = {}
        self._max_size = max_size

    def compute_cache_key(
        self,
        factpack_hash: str,
        evidencepack_hash: str,
        governance_decision: str,
        persona: Persona,
        prompt_version: str = "1.0",
        model: str = "default"
    ) -> str:
        raw_str = f"{factpack_hash}:{evidencepack_hash}:{governance_decision}:{persona.value}:{prompt_version}:{model}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[NarrativeResponse]:
        return self._cache.get(cache_key)

    def set(self, cache_key: str, response: NarrativeResponse) -> None:
        if len(self._cache) >= self._max_size:
            # Simple eviction of oldest item
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[cache_key] = response

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

narrative_cache = NarrativeCache()
