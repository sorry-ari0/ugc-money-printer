import os
from loguru import logger
from ugc.config import UGCConfig
from ugc.accounts import AccountManager
from ugc.downloader.tiktok import TikTokDownloader
from ugc.captioner.whisperx_captioner import WhisperXCaptioner
from ugc.analyzer.style_profiler import StyleProfiler
from ugc.enhancer.pipeline import EnhancePipeline, EnhanceOptions
from ugc.publisher.ayrshare import AyrsharePublisher
from ugc.scout.viral import ViralScout
from ugc.llm import LLMRouter
from ugc.repurposer.linkedin import LinkedInRepurposer
from ugc.scriptwriter.writer import ScriptWriter


class CLI:
    def __init__(self, config_path: str = ""):
        self.config = UGCConfig(config_path)
        accts_dir = os.path.join(self.config.root_dir, "storage", "accounts")
        self.accounts = AccountManager(accts_dir)
        self.llm = LLMRouter(
            primary=self.config.llm_primary,
            primary_model=self.config.llm_primary_model,
            fallback=self.config.llm_fallback,
            fallback_model=self.config.llm_fallback_model,
            anthropic_api_key=self.config.anthropic_api_key,
        )
        self.captioner = WhisperXCaptioner()
        self.publisher = AyrsharePublisher(self.config.ayrshare_api_key)
        self.scout = ViralScout()

    def download_tiktok(self, handle: str = "") -> list:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle),
            handle=handle,
        )
        results = dl.download()
        logger.success(f"Downloaded {len(results)} videos for @{handle}")
        return results

    def analyze_style(self, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle),
            handle=handle,
        )
        videos_meta = dl._collect_metadata()
        if not videos_meta:
            logger.warning(f"No videos found for @{handle}. Run download first.")
            return {}

        profile = StyleProfiler.build_profile(videos_meta)

        try:
            captions = "\n".join(v.get("caption", "") for v in videos_meta[:20])
            analysis = self.llm.chat(
                prompt=f"Analyze these TikTok captions and identify the top 5 content themes/niches:\n\n{captions}",
                system="You are a social media analyst. Return a JSON list of themes.",
            )
            profile["llm_themes"] = analysis
        except Exception as e:
            logger.warning(f"LLM analysis skipped: {e}")

        profile_path = os.path.join(self.config.account_dir(handle), "style_profile.json")
        StyleProfiler.save_profile(profile, profile_path)
        return profile

    def enhance(self, video_path: str, options: EnhanceOptions = None) -> dict:
        if options is None:
            options = EnhanceOptions(
                caption_style=self.config.caption_style,
                add_music=self.config.default_music,
                auto_publish=self.config.auto_publish,
                platforms=self.config.platforms,
            )
        output_dir = os.path.join(self.config.output_dir, "enhanced")
        pipeline = EnhancePipeline(
            config=self.config,
            llm=self.llm,
            captioner=self.captioner,
            publisher=self.publisher,
        )
        return pipeline.enhance(video_path, output_dir, options)

    def publish(self, video_path: str, caption: str = "",
                platforms: list = None, schedule: str = None) -> list:
        platforms = platforms or self.config.platforms
        if not caption:
            try:
                caption = self.llm.chat(
                    prompt="Write a short, engaging social media caption for a video post. Keep it under 200 characters.",
                    system="You are a social media copywriter.",
                )
            except Exception:
                caption = ""
        return self.publisher.publish(video_path, caption, platforms, schedule=schedule)

    def scout_viral(self, topics: list = None, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        if not topics:
            dl = TikTokDownloader(
                output_dir=self.config.videos_dir(handle), handle=handle
            )
            meta = dl._collect_metadata()
            topics = ViralScout.extract_topics(meta)

        accounts = self.scout.discover_accounts(
            topics, handle, self.config.scout_max_accounts
        )

        report_dir = self.config.scouts_dir(handle)
        ViralScout.save_report(
            {"discovered_accounts": accounts, "topics": topics},
            os.path.join(report_dir, "discovered_accounts.json"),
        )

        return {"accounts": accounts, "topics": topics}

    def get_trends(self, handle: str = "") -> dict:
        handle = handle or self.config.active_account
        path = os.path.join(self.config.scouts_dir(handle), "trend_report.json")
        return ViralScout.load_report(path)

    def switch_account(self, handle: str):
        self.accounts.set_active(handle)
        self.config.active_account = handle
        logger.info(f"Switched to @{handle}")

    def add_account(self, handle: str):
        self.accounts.add(handle)
        logger.info(f"Added @{handle}")

    def repurpose_linkedin(self, handle: str = "", limit: int = 10) -> list:
        handle = handle or self.config.active_account
        dl = TikTokDownloader(
            output_dir=self.config.videos_dir(handle), handle=handle
        )
        videos_meta = dl._collect_metadata()
        if not videos_meta:
            logger.warning(f"No videos found for @{handle}. Run download first.")
            return []

        transcripts = {}
        for video in videos_meta[:limit]:
            vid_id = video.get("id", "")
            video_file = os.path.join(self.config.videos_dir(handle), f"{vid_id}.mp4")
            if os.path.isfile(video_file):
                try:
                    segs = self.captioner.transcribe(video_file)
                    transcripts[vid_id] = " ".join(s.word for s in segs)
                except Exception as e:
                    logger.warning(f"Transcription failed for {vid_id}: {e}")
                    transcripts[vid_id] = video.get("caption", "")
            else:
                transcripts[vid_id] = video.get("caption", "")

        profile_path = os.path.join(self.config.account_dir(handle), "style_profile.json")
        style_hints = StyleProfiler.load_profile(profile_path)

        repurposer = LinkedInRepurposer()
        posts = repurposer.batch_repurpose(
            videos_meta[:limit], transcripts, llm=self.llm, style_hints=style_hints
        )

        output_path = os.path.join(
            self.config.account_dir(handle), "linkedin_posts.json"
        )
        LinkedInRepurposer.save_posts(posts, output_path)
        logger.success(f"Generated {len(posts)} LinkedIn posts for @{handle}")
        return posts

    def write_script(self, prompt: str, handle: str = "", duration: int = 60) -> dict:
        handle = handle or self.config.active_account
        writer = ScriptWriter()
        accts_dir = os.path.join(self.config.root_dir, "storage", "accounts")
        script = writer.write_script_for_creator(prompt, handle, accts_dir, self.llm, duration)
        from datetime import datetime
        scripts_dir = os.path.join(self.config.account_dir(handle), "scripts")
        script_path = os.path.join(scripts_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        ScriptWriter.save_script(script, script_path)
        logger.success(f"Script saved to {script_path}")
        return script
