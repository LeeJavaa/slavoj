from slavoj.core.config import LLMConfig
from slavoj.domain.interfaces import LLMInterface
from slavoj.infrastructure.llm.gemini import GeminiLLM


class LLMFactory:
    """Factory for creating LLM instances based on configuration"""

    @staticmethod
    def create_llm(config: LLMConfig) -> LLMInterface:
        """Create an LLM instance based on the configuration"""
        if config.provider.lower() == "gemini":
            return GeminiLLM(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")