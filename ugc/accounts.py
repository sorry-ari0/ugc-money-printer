import json
import os
from datetime import datetime, timezone


class AccountManager:
    def __init__(self, accounts_dir: str = ""):
        if not accounts_dir:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            accounts_dir = os.path.join(root, "storage", "accounts")
        self._dir = accounts_dir
        self._index_path = os.path.join(self._dir, "accounts.json")
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.isfile(self._index_path):
            with open(self._index_path, "r") as f:
                return json.load(f)
        return {"active": "", "accounts": []}

    def _save(self):
        os.makedirs(self._dir, exist_ok=True)
        with open(self._index_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def add(self, handle: str):
        handle = handle.lstrip("@")
        if handle in self._data["accounts"]:
            return

        acct_dir = os.path.join(self._dir, handle)
        for sub in ["videos", "assets", "scouts/viral_posts", "scouts/hooks_library"]:
            os.makedirs(os.path.join(acct_dir, sub), exist_ok=True)

        metadata = {
            "handle": handle,
            "platform": "tiktok",
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": None,
        }
        with open(os.path.join(acct_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        self._data["accounts"].append(handle)
        if not self._data["active"]:
            self._data["active"] = handle
        self._save()

    def set_active(self, handle: str):
        handle = handle.lstrip("@")
        if handle not in self._data["accounts"]:
            raise ValueError(f"Account '{handle}' not registered. Add it first.")
        self._data["active"] = handle
        self._save()

    def get_active(self) -> str:
        return self._data["active"]

    def list_accounts(self) -> list:
        return list(self._data["accounts"])
