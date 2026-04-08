from config import EMAIL_LINK


# Keep in sync with website: app/api/github/create-coverage-issues/route.ts gitCommand()
def git_command(new_branch_name: str) -> str:
    return (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {new_branch_name}\n"
        f"git pull origin {new_branch_name}\n"
        f"```"
    )


UPDATE_COMMENT_FOR_422 = f"Hey, I'm a bit lost here! Not sure which file I should be fixing. Could you give me a bit more to go on? Maybe add some details to the PR or drop a comment with some extra hints? Thanks!\n\nHave feedback or need help?\nFeel free to email {EMAIL_LINK}."
UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE = f"No changes were detected. Please add more details to the PR and try again.\n\nHave feedback or need help?\n{EMAIL_LINK}"
