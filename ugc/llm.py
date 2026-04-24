from loguru import logger

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from ollama import chat as ollama_chat
except ImportError:
    ollama_chat = None


class LLMRouter:
    def __init__(self, primary: str, primary_model: str,
                 fallback: str, fallback_model: str,
                 anthropic_api_key: str = ""):
        self.primary = primary
        self.primary_model = primary_model
        self.fallback = fallback
        self.fallback_model = fallback_model
        self.anthropic_api_key = anthropic_api_key

    def select(self) -> tuple:
        if self.primary == "anthropic" and self.anthropic_api_key:
            return self.primary, self.primary_model
        if self.primary == "ollama":
            return self.primary, self.primary_model
        return self.fallback, self.fallback_model

    def chat(self, prompt: str, system: str = "") -> str:
        provider, model = self.select()
        try:
            if provider == "anthropic":
                return self._chat_anthropic(prompt, system, model)
            else:
                return self._chat_ollama(prompt, system, model)
        except Exception as e:
            logger.warning(f"{provider} failed: {e}, trying fallback")
            if provider != self.fallback:
                if self.fallback == "anthropic":
                    return self._chat_anthropic(prompt, system, self.fallback_model)
                return self._chat_ollama(prompt, system, self.fallback_model)
            raise

    def _chat_anthropic(self, prompt: str, system: str, model: str) -> str:
        if Anthropic is None:
            raise ImportError("anthropic package not installed")
        client = Anthropic(api_key=self.anthropic_api_key)
        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text

    def _chat_ollama(self, prompt: str, system: str, model: str) -> str:
        if ollama_chat is None:
            raise ImportError("ollama package not installed")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = ollama_chat(model=model, messages=messages)
        return resp["message"]["content"]
