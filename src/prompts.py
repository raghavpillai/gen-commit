COMMIT_PROMPT_SYSTEM = "You are a Git analyzer who is given the output of a git diff. Your task is to create a descriptive commit message based on this diff."


COMMIT_PROMPT_NO_DESCRIPTION = """
<diffs>
{diff}
</diffs>

Provide your response in the following structured format:
<output>
<commit_message>
[Brief descriptive commit message in no longer than 10 words]
</commit_message>
</output>

"""

COMMIT_PROMPT_WITH_DESCRIPTION = """
<diffs>
{diffs}
</diffs>

<output>
<commit_message>
[Brief descriptive commit message in no longer than 10 words]
</commit_message>
<commit_description>
[Bullet point list of changes that were made in the diff]
</commit_description>
</output>
"""
