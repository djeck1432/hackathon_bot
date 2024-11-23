import logging
import os

import json
from asgiref.sync import async_to_sync
from django.db.models import Q
from celery import Celery, shared_task
import redis
from dotenv import load_dotenv

from tracker.models import TelegramUser, Repository
from tracker.telegram.bot import send_new_issue_notification

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


load_dotenv()
# Connect to Redis


@shared_task()
def get_relevant_recipients():
    """
    Retrieves a mapping of Telegram users subscribed for
    new-issue-notifications to the repositories they are subscribed to.

    :return: A dictionary where keys are Telegram user IDs, and values are lists of subscribed repository names.
    """

    Repository.objects.filter
    repository_data = {
        "spotnet": ["issue1", "issue2"]
    }
    user_data = {"name": "Alice", "age": 30}
    cache = redis.Redis(host=os.environ.get("REDIS_HOST"), port=6379, decode_responses=True)

    # Set a cache entry without expiration
    user_data = {"name": "Alice", "age": 30}
    cache.set("user:123", json.dumps(user_data))
    
    # Check TTL (should return -1 for no expiration)
    ttl = cache.ttl("user:123")
    logger.info(f"TTL for user:123: {ttl}")  # Output: -1

    # Retrieve the data
    cached_data = cache.get("user:123")
    if cached_data:
        user = json.loads(cached_data)
        print(f"User found in cache: {user}")
    else:
        print("User not found in cache.")

    repositories = ["spotnet"]
    repository_data = {
        "spotnet": ["issue1", "issue2"]
    }
    subscribed_users = TelegramUser.objects.filter(
        notify_about_new_issues=True,
        user__repository__name__in=repositories  # Assuming 'name' identifies the repositories.
    )

    user_repo_map = {}

    for telegram_user in subscribed_users:
        repos = Repository.objects.filter(user=telegram_user.user, name__in=repositories)

        logger.info(f"Telegram User: {telegram_user.telegram_id}")
        for repo in repos:
            # Initialize the list for this telegram_id if it doesn't exist
            if telegram_user.telegram_id not in user_repo_map:
                user_repo_map[telegram_user.telegram_id] = []
            # Append the repository name to the user's list
            user_repo_map[telegram_user.telegram_id].append(repo.name)
            logger.info(f"  Subscribed Repository: {repo.name}")

    async_to_sync(send_new_issue_notification)(user_repo_map)
