from django.db.models import Q
from celery import Celery

from tracker.models import TelegramUser, Repository

app = Celery('tasks', broker='redis://localhost:6379/0')


@app.on_after_configure.connect
def check_for_new_issues(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')


@app.task
def test(arg):
    print(arg)


def get_relevant_recipients(repositories: list) -> dict[str, list]:

    subscribed_users = TelegramUser.objects.filter(
        notify_about_new_issues=True,
        user__repository__name__in=repositories  # Assuming 'name' identifies the repositories.
    ).distinct()

    user_repo_map = {}

    for telegram_user in subscribed_users:
        repositories = Repository.objects.filter(user=telegram_user.user, name__in=repositories)

        print(f"Telegram User: {telegram_user.telegram_id}")
        for repo in repositories:
            # Initialize the list for this telegram_id if it doesn't exist
            if telegram_user.telegram_id not in user_repo_map:
                user_repo_map[telegram_user.telegram_id] = []
            # Append the repository name to the user's list
            user_repo_map[telegram_user.telegram_id].append(repo.name)
            print(f"  Subscribed Repository: {repo.name}")

    return user_repo_map
