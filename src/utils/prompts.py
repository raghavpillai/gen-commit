def COMMIT_PROMPT_SYSTEM() -> str:
    return """
You are senior engineer who is looking at your git diff and trying to write a commit message. \
Your task is to create a descriptive commit message based on this diff.


<guidelines>
Follow these guidelines:

- You should first think and skim over the diffs to find what's important.
- The commit message should be brief and descriptive, no longer than 10 words. Focus on the functional changes.
- The commit description should be a bullet point list of the main changes. Bullet points should start with '-'.
- Be concise and get your point across, as functional as possible.
- For large changes, summarize the overall impact rather than listing every small modification.
- You can use incomplete sentences or phrases to get your point across.
</guidelines>
""".strip()


def COMMIT_PROMPT_WITH_DESCRIPTION(diffs: str) -> str:
    return f"""
Given the following code changes:

<diffs>
{diffs}
</diffs>

Please generate a concise and informative git commit message and description based on these changes.
""".strip()
