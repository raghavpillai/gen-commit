import argparse
import os
import subprocess
import sys

import tiktoken
from pydantic import BaseModel, Field

from .utils.config import read_config, read_version_from_pyproject
from .utils.llm_wrapper import anthropic_chat, openai_chat
from .utils.prompts import (
    COMMIT_PROMPT_SYSTEM,
    COMMIT_PROMPT_WITH_DESCRIPTION,
)

CONFIG: dict = read_config()
MAX_LINE_LENGTH: int = CONFIG.get("MAX_LINE_LENGTH", 300)
MAX_TOKENS_ALLOWED: int = CONFIG.get("MAX_TOKENS_ALLOWED", 30000)
VERSION: str = read_version_from_pyproject()


class CommitMessage(BaseModel):
    thinking: str = Field(
        ...,
        description="Your concise thought process of the diffs",
    )
    commit_message: str = Field(
        ..., description="Brief descriptive commit message in no longer than 10 words"
    )
    commit_description: str = Field(
        ..., description="Hyphenated bullet point list of changes"
    )


def format_diff(diff_text: str) -> str:
    file_changes: dict[str, list[tuple[str, str]]] = {}
    current_file: str = ""

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            current_file = line.split()[-1].lstrip("b/")
            file_changes[current_file] = []
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                file_changes[current_file].append(
                    ("add", line[1:MAX_LINE_LENGTH].strip())
                )
        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                file_changes[current_file].append(
                    ("remove", line[1:MAX_LINE_LENGTH].strip())
                )

    # Format into a structured output
    formatted_diff_text: str = "### Git Changes Summary ###\n\n"
    for filename, changes in file_changes.items():
        formatted_diff_text += f"File: {filename}\n"
        formatted_diff_text += "Changes:\n"
        limit: int = 30 if filename.endswith(".lock") else 2000
        for change_type, content in changes[:limit]:
            prefix = "+" if change_type == "add" else "-"
            formatted_diff_text += f"{prefix} {content}\n"
        if len(changes) > limit:
            formatted_diff_text += (
                f"\n... ({len(changes) - limit} additional changes truncated)\n"
            )
        formatted_diff_text += "\n"

    return formatted_diff_text


def get_llm_func(model_line: str) -> tuple[callable, str]:
    provider, model = model_line.lower().split(":", 1)
    if provider == "openai":
        return openai_chat, model
    elif provider == "anthropic":
        return anthropic_chat, model
    else:
        raise ValueError(f"Invalid model: {model}")


def generate_commit_message(diff_text: str) -> CommitMessage:
    tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model("gpt-4o")
    if not diff_text:
        return "No changes to commit", ""

    token_list: list[int] = tokenizer.encode(diff_text)
    truncated_tokens: list[int] = token_list[:MAX_TOKENS_ALLOWED]
    truncated_diff: str = tokenizer.decode(truncated_tokens)
    config: dict = read_config()
    model: str = config.get("MODEL")
    if not model:
        raise ValueError("MODEL not found in config")

    llm_func: callable
    model_name: str
    llm_func, model_name = get_llm_func(model)

    llm_response: CommitMessage = llm_func(
        model=model_name,
        system_prompt=COMMIT_PROMPT_SYSTEM,
        user_prompt=COMMIT_PROMPT_WITH_DESCRIPTION.format(diffs=truncated_diff),
        response_model=CommitMessage,
    )
    return llm_response


def initialize() -> bool:
    home_dir: str = os.path.expanduser("~")
    config_file: str = os.path.join(home_dir, ".gen-commit")
    if os.path.exists(config_file):
        user_input = (
            input(f"Config file already exists at {config_file}. Overwrite? (Y/n): ")
            .strip()
            .lower()
        )
        if user_input not in ["y", ""]:
            print("Initialization cancelled.")
            return False

    with open(config_file, "w") as f:
        f.write(
            "MODEL=anthropic:claude-3-5-sonnet-20241022\nOPENAI_API_KEY=\nANTHROPIC_API_KEY="
        )
    return True


def gencommit():
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser()
    arg_parser.add_argument("-m", type=str, help="Override commit message")
    arg_parser.add_argument("-d", type=str, help="Override commit description")
    arg_parser.add_argument(
        "--init", "--initialize", action="store_true", help="Initialize gen-commit"
    )
    arg_parser.add_argument(
        "--version", "--v", action="version", version=f"%(prog)s {VERSION}"
    )
    found_args, unknown_args = arg_parser.parse_known_args()

    has_message: bool = found_args.m is not None
    has_description: bool = found_args.d is not None

    if found_args.init:
        success: bool = initialize()
        if success:
            print("gen-commit initialized successfully, wrote config to ~/.gen-commit")
            sys.exit(0)
        else:
            print("gen-commit initialization failed.")
            sys.exit(1)

    try:
        # Check if there are any commits
        subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD"], text=True
        ).strip()
        commits_exist = True
    except subprocess.CalledProcessError:
        commits_exist = False

    if "-a" in unknown_args:
        # Check for unstaged changes
        unstaged_changes = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
        ).strip()
        if not unstaged_changes:
            print("No changes detected.")
            sys.exit(1)

    staged_changes = subprocess.check_output(
        ["git", "diff", "--staged", "--name-only"],
        text=True,
    ).strip()
    if not staged_changes and "-a" not in unknown_args:
        print("No changes staged for commit.")
        sys.exit(1)

    commit_message: str
    commit_description: str
    if commits_exist:
        diff_output: str = subprocess.check_output(
            ["git", "diff", "--staged"], text=True
        ).strip()
        formatted_diff: str = format_diff(diff_output)
        commit_message_object: CommitMessage = generate_commit_message(
            diff_text=formatted_diff
        )
        commit_message = commit_message_object.commit_message
        commit_description = commit_message_object.commit_description
    else:
        commit_message: str = found_args.m if has_message else "Initial commit"
        commit_description: str = found_args.d if has_description else ""

    commit_message = commit_message.replace('"', '\\"')
    commit_description = commit_description.replace('"', '\\"')

    commit_command: str
    if commit_description:
        commit_command = f"""git commit {" ".join(unknown_args)} -m "{commit_message}" -m "{commit_description}" """
    else:
        commit_command = (
            f"""git commit {" ".join(unknown_args)} -m "{commit_message}" """
        )

    subprocess.run(commit_command, shell=True, check=True)


if __name__ == "__main__":
    gencommit()
