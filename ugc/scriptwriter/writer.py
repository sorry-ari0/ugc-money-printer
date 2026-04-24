import json
import os
import re
from ugc.analyzer.style_profiler import StyleProfiler


class ScriptWriter:
    def write_script(self, prompt: str, style_hints: dict, llm, duration_seconds: int = 60) -> dict:
        style_context = ""
        if style_hints:
            if "pacing" in style_hints:
                avg = style_hints["pacing"].get("avg_duration", 0)
                style_context += f"Average video duration: {avg:.0f}s. "
            if "hashtags" in style_hints:
                top = style_hints["hashtags"].get("top_tags", [])[:10]
                if top:
                    tags = ", ".join(f"#{t}" for t in top)
                    style_context += f"Common hashtags: {tags}. "
            if "engagement" in style_hints:
                eng = style_hints["engagement"]
                style_context += f"Avg views: {eng.get('avg_views', 0):.0f}. "
            if "llm_themes" in style_hints:
                style_context += f"Content themes: {style_hints['llm_themes']}. "

        system = (
            "You are a viral video scriptwriter. Write scripts optimized for short-form video. "
            "Return ONLY valid JSON with these keys: "
            "hook (string, first 3 seconds to grab attention), "
            "body (list of strings, each a section of the main content), "
            "cta (string, call to action), "
            "suggested_broll (list of strings, search terms for b-roll footage), "
            "estimated_duration (integer, seconds), "
            "hashtags (list of strings without # prefix). "
            f"Target duration: {duration_seconds} seconds. "
            f"{style_context}"
        )

        response = llm.chat(prompt=prompt, system=system)

        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
        if match:
            response = match.group(1)

        return json.loads(response.strip())

    def write_script_for_creator(self, prompt: str, handle: str, accounts_dir: str, llm, duration_seconds: int = 60) -> dict:
        profile_path = os.path.join(accounts_dir, handle, "style_profile.json")
        style_hints = StyleProfiler.load_profile(profile_path)
        return self.write_script(prompt, style_hints, llm, duration_seconds)

    @staticmethod
    def format_teleprompter(script: dict) -> str:
        lines = []
        lines.append(f"[HOOK] {script.get('hook', '')}")
        lines.append("")
        for i, section in enumerate(script.get("body", []), 1):
            lines.append(f"{i}. {section}")
        lines.append("")
        lines.append(f"[CTA] {script.get('cta', '')}")
        return "\n".join(lines)

    @staticmethod
    def save_script(script: dict, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
