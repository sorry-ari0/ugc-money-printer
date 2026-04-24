import os
import toml


class UGCConfig:
    def __init__(self, config_path: str = ""):
        if not config_path:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root, "config.toml")

        raw = {}
        if os.path.isfile(config_path):
            raw = toml.load(config_path).get("ugc", {})

        self.active_account: str = raw.get("active_account", "ari.from.jelly")
        self.output_dir: str = raw.get("output_dir", "storage/output")

        llm = raw.get("llm", {})
        self.llm_primary: str = llm.get("primary", "anthropic")
        self.llm_primary_model: str = llm.get("primary_model", "claude-sonnet-4-6")
        self.llm_fallback: str = llm.get("fallback", "ollama")
        self.llm_fallback_model: str = llm.get("fallback_model", "llama-agent:latest")
        self.anthropic_api_key: str = llm.get("anthropic_api_key", "")

        enhance = raw.get("enhance", {})
        self.caption_style: str = enhance.get("default_caption_style", "word-pop")
        self.default_music: bool = enhance.get("default_music", True)
        self.silence_trim: bool = enhance.get("silence_trim", True)
        self.auto_publish: bool = enhance.get("auto_publish", False)

        publish = raw.get("publish", {})
        self.platforms: list = publish.get(
            "platforms", ["tiktok", "instagram", "youtube", "twitter", "linkedin"]
        )
        self.ayrshare_api_key: str = publish.get("ayrshare_api_key", "")

        scout = raw.get("scout", {})
        self.scout_max_accounts: int = scout.get("max_accounts", 20)
        self.scout_refresh_hours: int = scout.get("refresh_interval_hours", 168)

    @property
    def root_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def account_dir(self, handle: str = "") -> str:
        h = handle or self.active_account
        return os.path.join(self.root_dir, "storage", "accounts", h)

    def videos_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "videos")

    def assets_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "assets")

    def scouts_dir(self, handle: str = "") -> str:
        return os.path.join(self.account_dir(handle), "scouts")
