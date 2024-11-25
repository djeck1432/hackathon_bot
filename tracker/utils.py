import logging
from datetime import datetime
from typing import Tuple, Any, Dict, List

import requests
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta

from .models import Repository, TelegramUser
from .values import HEADERS, ISSUES_URL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@sync_to_async
def get_all_repositories(tele_id: str) -> list[dict]:
    """
    A function that returns a list of repositories asyncronously.
    :param tele_id: str
    :return: Repositories
    """
    from .models import TelegramUser

    repositories = TelegramUser.objects.get(
        telegram_id=tele_id
    ).user.repository_set.values()

    return list(repositories)


@sync_to_async
def get_user(uuid: str) -> tuple["CustomUser"]:
    """
    Retunrs an user instantce
    :param uuid: str
    :return: tuple(CustomUser, )
    """
    from .models import CustomUser

    user = CustomUser.objects.get(id=uuid)

    return (user,)


@sync_to_async
def create_telegram_user(user: object, telegram_id: str) -> None:
    """
    Creates a new TelegramUser object
    :param user: CustomUser object
    :param telegram_id: telegram id
    :return: None
    """
    from .models import TelegramUser

    if not TelegramUser.objects.filter(telegram_id=telegram_id, user=user).exists():
        TelegramUser.objects.create(user=user, telegram_id=telegram_id)


def check_issue_assignment_events(issue: dict) -> dict:
    """
    Checks an issue's timeline for assignment events to determine if it was
    newly assigned or reassigned to a different contributor.

    :param issue: The issue dictionary.
    :return: Dictionary with reassignment details and the exact time if applicable.
    """
    try:
        events_url = issue.get("events_url", str())

        response = requests.get(events_url, headers=HEADERS)
        response.raise_for_status()

        if response.ok:
            events = response.json()
            assignment_info = {
                "assignee": None,
                "assigned_at": None,
            }

            for event in events:
                if event.get("event") == "assigned":
                    assignment_info["assignee"] = event.get("assignee", dict()).get(
                        "login", str()
                    )
                    assignment_info["assigned_at"] = event.get("created_at", str())

            return assignment_info
    except requests.exceptions.RequestException as e:
        logger.info(e)
    return {}


def get_all_open_and_assigned_issues(url: str) -> list[dict]:
    """
    Retrieves all open and assigned issues from the given URL.
    :param url: An API endpoint for issues.
    :return: A list of dictionaries representing open and assigned issues.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        if response.ok:
            issues = response.json()

            open_assigned_issues = list(
                filter(
                    lambda issue: issue.get("state") == "open"
                    and issue.get("assignee")
                    and not issue.get("draft")
                    and not issue.get("pull_request"),
                    issues,
                )
            )

            return open_assigned_issues

    except requests.exceptions.RequestException as e:
        logger.info(e)
    return []


def get_all_open_pull_requests(url: str) -> list[dict]:
    """
    Retrieves all open pull requests from a given URL.

    :param url: The API endpoint for pull requests.
    :return: A list of dictionaries representing open pull requests.
    """
    try:
        response = requests.get(url, headers=HEADERS, params={"state": "open"})
        response.raise_for_status()

        if response.ok:
            response = response.json()

            return response

    except requests.exceptions.RequestException as e:
        logger.info(e)
    return []


def get_issues_without_pull_requests(
    issues_url: str, pull_requests_url: str
) -> list[dict]:
    """
    Matches open, assigned issues with open or draft pull requests by the same user.

    :param issues_url: The API endpoint for issues.
    :param pull_requests_url: The API endpoint for pull requests.
    :return: List of issues with matched PR details if found.
    """
    issues = get_all_open_and_assigned_issues(issues_url)

    for issue in issues:
        issue["assignment_info"] = check_issue_assignment_events(issue)
        assigned_at = issue.get("assignment_info", dict()).get("assigned_at")

        time_delta = (
            relativedelta(
                dt1=datetime.now(),
                dt2=datetime.strptime(assigned_at, "%Y-%m-%dT%H:%M:%SZ"),
            )
            if assigned_at
            else str()
        )

        issue["days"] = time_delta.days if time_delta else 0

    pull_requests = get_all_open_pull_requests(pull_requests_url)

    pull_requests_users = [
        pull_request.get("user", dict()).get("login")
        for pull_request in pull_requests
        if pull_request.get("user", dict()).get("login")
    ]

    result = list()

    for issue in issues.copy():
        if (
            issue.get("days", 0) >= 1
            and issue.get("assignee", dict()).get("login") not in pull_requests_users
        ):
            result.append(issue)

    return result


def get_all_available_issues(url: str) -> list[dict]:
    """
    Retrieves all available issues from a given URL.
    :param url: The API endpoint for issues.
    :return: A list of dictionaries representing available issues.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        if response.ok:
            issues = response.json()

            available_issues = list(
                filter(
                    lambda issue: issue.get("state") == "open"
                    and not issue.get("assignee")
                    and not issue.get("draft")
                    and not issue.get("pull_request"),
                    issues,
                )
            )
            return available_issues

    except requests.exceptions.RequestException as e:
        logger.info(e)
    return []


def get_all_opened_issues(url: str) -> list[dict]:
    """
    Retrieves all opened issues from the given URL.
    :param url: An API endpoint for issues.
    :return: A list of dictionaries representing opened issues.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        if response.ok:
            issues = response.json()

            opened_issues = list(
                filter(
                    lambda issue: issue.get("state") == "open"
                    and not issue.get("draft")
                    and not issue.get("pull_request"),
                    issues,
                )
            )

            return opened_issues
    except requests.exceptions.RequestException as e:
        logger.info(e)
    return []


def get_existing_issues_for_subscribed_users(repositories: list[dict]) -> dict[str, list[str]]:
    """
    Retrieves open issues for a given list of repositories.

    :param repositories: List of repositories with "author" and "name".
    :return: Dictionary with repository names as keys and lists of open issue titles as values.
    """

    repository_data = {}
    for repository in repositories:
        issues = get_all_opened_issues(ISSUES_URL.format(
            owner=repository.get("author", str()),
            repo=repository.get("name", str())))
        repository_data[repository.get("name", str())] = [issue.get("title") for issue in issues]
    return repository_data


def compare_two_repo_dicts(dict1: dict[str, list[str]],
                           dict2: dict[str, list[str]]) -> dict[str, list[str]]:
    diff = {}
    for key in dict1:
        len_1 = len(dict1[key])
        len_2 = len(dict2[key])
        if len_1 > len_2:
            new_issues = len_1 - len_2
            diff.update({key: dict1[key][:new_issues]})
    return diff
