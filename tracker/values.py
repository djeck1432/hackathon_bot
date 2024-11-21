import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

ISSUES_URL = "https://api.github.com/repos/{owner}/{repo}/issues"
PULLS_URL = "https://api.github.com/repos/{owner}/{repo}/pulls"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f'Bearer {os.environ.get("GITHUB_AUTH_TOKEN", "")}',
    "X-GitHub-Api-Version": "2022-11-28",
}


@dataclass(frozen=True)
class DefaultModelValues:
    """
    A data class to store default maximum length values for various fields in models.

    Attributes:
    - name_max_length (int): The maximum allowed length for the 'name' field. Default is 255.
    - author_max_length (int): The maximum allowed length for the 'author' field. Default is 255.
    - link_max_length (int): The maximum allowed length for the 'link' field. Default is 255.

    This class is immutable, so its values cannot be modified after instantiation.
    """

    name_max_length: int = 255
    author_max_length: int = 255
    link_max_length: int = 255
    email_max_length: int = 255
