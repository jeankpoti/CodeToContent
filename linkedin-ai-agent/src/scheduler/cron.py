"""
Daily Post Scheduler

Schedules and triggers daily LinkedIn post generation.
"""

import sys
from pathlib import Path
from datetime import datetime, time
from typing import Callable, Optional
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import ConfigStore, UserConfig


class PostScheduler:
    """Manages scheduled daily posts for all users."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.config_store = ConfigStore()
        self._post_callback: Optional[Callable] = None
        self._jobs: dict[int, str] = {}  # chat_id -> job_id

    def set_post_callback(self, callback: Callable) -> None:
        """
        Set the callback function for generating posts.

        Args:
            callback: Async function that takes chat_id and generates a post
        """
        self._post_callback = callback

    def start(self) -> None:
        """Start the scheduler and load existing schedules."""
        if not self.scheduler.running:
            self.scheduler.start()
            print("Post scheduler started")

        # Load existing schedules
        self._load_all_schedules()

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Post scheduler stopped")

    def _load_all_schedules(self) -> None:
        """Load schedules for all configured users."""
        configs = self.config_store.list_all()

        for config in configs:
            if config.preferred_time and config.github_url:
                self.schedule_user(config)

    def schedule_user(self, config: UserConfig) -> bool:
        """
        Schedule daily posts for a user.

        Args:
            config: User configuration

        Returns:
            True if scheduled successfully
        """
        if not config.preferred_time:
            return False

        # Parse time
        try:
            hour, minute = map(int, config.preferred_time.split(":"))
        except:
            return False

        # Remove existing job if any
        self.unschedule_user(config.chat_id)

        # Create new job
        job_id = f"post_{config.chat_id}"

        self.scheduler.add_job(
            self._trigger_post,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            args=[config.chat_id],
            replace_existing=True,
            name=f"Daily post for chat {config.chat_id}"
        )

        self._jobs[config.chat_id] = job_id
        print(f"Scheduled daily post for chat {config.chat_id} at {config.preferred_time}")

        return True

    def unschedule_user(self, chat_id: int) -> bool:
        """
        Remove scheduled posts for a user.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if unscheduled successfully
        """
        job_id = self._jobs.pop(chat_id, None)

        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                print(f"Unscheduled posts for chat {chat_id}")
                return True
            except:
                pass

        return False

    def update_schedule(self, chat_id: int, new_time: str) -> bool:
        """
        Update the schedule for a user.

        Args:
            chat_id: Telegram chat ID
            new_time: New time in HH:MM format

        Returns:
            True if updated successfully
        """
        config = self.config_store.get(chat_id)
        config.preferred_time = new_time

        return self.schedule_user(config)

    async def _trigger_post(self, chat_id: int) -> None:
        """
        Trigger post generation for a user.

        Args:
            chat_id: Telegram chat ID
        """
        if not self._post_callback:
            print(f"No post callback set, skipping post for chat {chat_id}")
            return

        config = self.config_store.get(chat_id)

        # Verify user still has a repo connected
        if not config.github_url:
            print(f"No repo connected for chat {chat_id}, skipping")
            return

        print(f"Triggering daily post for chat {chat_id}")

        try:
            await self._post_callback(chat_id)
        except Exception as e:
            print(f"Error generating post for chat {chat_id}: {e}")

    def get_next_run(self, chat_id: int) -> Optional[datetime]:
        """
        Get the next scheduled run time for a user.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Next run datetime or None
        """
        job_id = self._jobs.get(chat_id)

        if job_id:
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time

        return None

    def list_schedules(self) -> list[dict]:
        """
        List all scheduled jobs.

        Returns:
            List of schedule info dicts
        """
        schedules = []

        for chat_id, job_id in self._jobs.items():
            job = self.scheduler.get_job(job_id)
            if job:
                schedules.append({
                    "chat_id": chat_id,
                    "job_id": job_id,
                    "next_run": job.next_run_time,
                    "name": job.name
                })

        return schedules


# Singleton instance
post_scheduler = PostScheduler()
