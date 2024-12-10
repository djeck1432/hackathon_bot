from dataclasses import dataclass
from string import Template


@dataclass
class TemplateNames:
    """Class to hold all the templates used in the bot."""

    greeting: Template
    repo_header: Template
    issue_detail: Template
    no_missed_deadlines: Template
    issue_summary: Template
    no_issues: Template
    issue_list_item: Template
    support_contact: Template
    no_support: Template


TEMPLATES = TemplateNames(
    greeting=Template("Hello $user_mention!\nWould you like to check some issues?"),
    repo_header=Template(
        "=" * 50 + "\n<b>Repository: $author/$repo</b>\n" + "=" * 50 + "\n\n"
    ),
    issue_detail=Template(
        "-----------------------------------\n"
        "Issue: $title\n"
        "User: $user\n"
        "Assigned:\n"
        "\t\t\t\tDays ago: $days\n"
        "-----------------------------------\n"
    ),
    no_missed_deadlines=Template("No missed deadlines.\n"),
    issue_summary=Template(
        "-----------------------------------\n"
        "Issue: $title\n"
        "-----------------------------------\n"
    ),
    no_issues=Template("No available issues.\n"),
    issue_list_item=Template(
        "-----------------------------------\n"
        "$issue\n"
        "-----------------------------------\n"
    ),
    support_contact=Template("Support Contact:\n$repo_message\n$support_link"),
    no_support=Template("Support Contact:\n$repo_message\nNo support provided."),
)
