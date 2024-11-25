import logging
import os

import json
from asgiref.sync import async_to_sync
from django.db.models import Q
from celery import Celery, shared_task
import redis
from dotenv import load_dotenv

from tracker.values import ISSUES_URL
from tracker.models import TelegramUser, Repository
from tracker.telegram.bot import send_new_issue_notification
from tracker.utils import get_all_opened_issues, get_existing_issues_for_subscribed_users, compare_two_repo_dicts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


load_dotenv()
# Connect to Redis


@shared_task()
def get_relevant_recipients() -> None:
    """
    Retrieves a mapping of Telegram users subscribed for
    new-issue-notifications to the repositories they are subscribed to.

    :return: A dictionary where keys are Telegram user IDs, and values are lists of subscribed repository names.
    """
    subscribed_users = TelegramUser.objects.filter(
        notify_about_new_issues=True
    ).first().user
    repositories = Repository.objects.filter(user__in=subscribed_users).values("author", "name")
    existing_issues = get_existing_issues_for_subscribed_users(repositories)

    cache = redis.Redis(host=os.environ.get("REDIS_HOST"), port=6379, decode_responses=True)
    if not cache.exists("task_first_run_flag"):
        cache.set("existing:issues", json.dumps(existing_issues))
        return

    cached_existing_issues = cache.get("existing:issues")
    cached_existing_issues = json.loads(str(cached_existing_issues))
    new_issues = compare_two_repo_dicts(existing_issues, cached_existing_issues)
    repos_with_new_issues = [key for key in new_issues]

    user_repo_map = {}
    for telegram_user in subscribed_users:
        repos = Repository.objects.filter(user=telegram_user.user, name__in=repos_with_new_issues)

        logger.info(f"Telegram User: {telegram_user.telegram_id}")
        for repo in repos:
            if telegram_user.telegram_id not in user_repo_map:
                user_repo_map[telegram_user.telegram_id] = []

            user_repo_map[telegram_user.telegram_id].append(repo.name)

    async_to_sync(send_new_issue_notification)(user_repo_map, new_issues)
