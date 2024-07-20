COMMIT_PROMPT_SYSTEM = "You are a Git analyzer who is given the output of a git diff. Your task is to create a descriptive commit message based on this diff."


COMMIT_PROMPT_NO_DESCRIPTION = """
<diffs>
{diff}
</diffs>

Please generate a concise and informative git commit message and description based on these changes. Follow these guidelines:

1. The commit message should be brief and descriptive, no longer than 10 words.
2. The commit description should be a bullet point list of the main changes.
3. Be concise and get your point across, as functional as possible.
4. For large changes, summarize the overall impact rather than listing every small modification.

Provide your response in the following structured format:
<output>
<commit_message>
[Brief descriptive commit message in no longer than 10 words]
</commit_message>
</output>

"""

COMMIT_PROMPT_WITH_DESCRIPTION = """
Given the following code changes:

<diffs>
{diffs}
</diffs>

Please generate a concise and informative git commit message and description based on these changes. Follow these guidelines:

1. The commit message should be brief and descriptive, no longer than 10 words.
2. The commit description should be a bullet point list of the main changes.
3. Be concise and get your point across, as functional as possible.
4. For large changes, summarize the overall impact rather than listing every small modification.

Provide your response in the following structured format:

<output>
<commit_message>
[Brief descriptive commit message]
</commit_message>
<commit_description>
[Hyphenated bullet point list of changes]
</commit_description>
</output>
"""
