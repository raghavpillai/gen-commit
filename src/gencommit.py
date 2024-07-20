import os
import sys
import subprocess
import tiktoken
import argparse
import xml.etree.ElementTree as ET
from .utils.prompts import (
    COMMIT_PROMPT_SYSTEM,
    COMMIT_PROMPT_NO_DESCRIPTION,
    COMMIT_PROMPT_WITH_DESCRIPTION,
)
from .utils.llm_wrapper import anthropic_chat, openai_chat
from .utils.config import read_version_from_pyproject, read_config

MAX_LINE_LENGTH: int = 300
MAX_TOKENS_ALLOWED: int = 20480
VERSION: str = read_version_from_pyproject()


def format_diff(diff_text: str) -> str:
    added_lines: list[str] = []
    removed_lines: list[str] = []
    all_lines: list[str] = diff_text.split("\n")
    for line in all_lines:
        if line.startswith("+"):
            added_lines.append(line[:MAX_LINE_LENGTH])
        elif line.startswith("-"):
            removed_lines.append(line[:MAX_LINE_LENGTH])
    formatted_diff_text: str = (
        "ADDED:\n" + "\n".join(added_lines) + "\nREMOVED:\n" + "\n".join(removed_lines)
    )
    return formatted_diff_text


def get_llm_func(model_line: str) -> tuple[callable, str]:
    provider, model = model_line.lower().split(":", 1)

    if provider == "openai":
        return openai_chat, model
    elif provider == "anthropic":
        return anthropic_chat, model
    else:
        raise ValueError(f"Invalid model: {model}")


def _format_response_xml(xml_response: str) -> tuple[str, str]:
    root_element: ET.Element = ET.fromstring(xml_response)

    commit_message: str = (
        root_element.find("commit_message").text.strip()
        if root_element.find("commit_message") is not None
        else ""
    )

    commit_description: str = ""
    description_element: ET.Element = root_element.find("commit_description")
    if description_element is not None:
        commit_description = "\n".join(
            [
                line.strip()
                for line in description_element.text.split("\n")
                if line.strip()
            ]
        )

    return commit_message, commit_description


def generate_commit_message(diff_text: str) -> tuple[str, str]:
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

    llm_response: str = llm_func(
        model=model_name,
        system_prompt=COMMIT_PROMPT_SYSTEM,
        user_prompt=COMMIT_PROMPT_WITH_DESCRIPTION.format(diffs=truncated_diff),
    )
    try:
        return _format_response_xml(llm_response)
    except Exception as e:
        error_file = os.path.expanduser("~/gen-commit-error.txt")
        with open(error_file, "w") as f:
            f.write(f"Error: {str(e)}\n\nRaw response:\n{llm_response}")
        print(f"Error parsing LLM response. Details written to {error_file}")
        raise


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
            "MODEL=anthropic:claude-3-5-sonnet-20240620\nOPENAI_API_KEY=\nANTHROPIC_API_KEY="
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
            ["git", "diff", "HEAD"] + unknown_args, text=True
        ).strip()
        formatted_diff: str = format_diff(diff_output)
        commit_message, commit_description = generate_commit_message(
            diff_text=formatted_diff
        )
    else:
        commit_message: str = found_args.m if has_message else "Initial commit"
        commit_description: str = found_args.d if has_description else ""

    commit_command: str
    if commit_description:
        commit_command = f'git commit {" ".join(unknown_args)} -m "{commit_message}" -m "{commit_description}"'
    else:
        commit_command = f'git commit {" ".join(unknown_args)} -m "{commit_message}"'
    os.system(commit_command)


if __name__ == "__main__":
    gencommit()
