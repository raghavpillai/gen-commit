import os
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

MAX_LINE_LENGTH: int = 10000
MAX_TOKENS_ALLOWED: int = 20480
VERSION: str = "0.1.0"


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


def generate_commit_message(
    diff_text: str, use_openai: bool = False
) -> tuple[str, str]:
    tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model("gpt-4o")
    if not diff_text:
        return "No changes to commit", ""

    token_list: list[int] = tokenizer.encode(diff_text)
    truncated_tokens: list[int] = token_list[:MAX_TOKENS_ALLOWED]
    truncated_diff: str = tokenizer.decode(truncated_tokens)

    llm_chat: callable = openai_chat if use_openai else anthropic_chat

    llm_response: str = llm_chat(
        system_prompt=COMMIT_PROMPT_SYSTEM,
        user_prompt=COMMIT_PROMPT_WITH_DESCRIPTION.format(diffs=truncated_diff),
    )
    return _format_response_xml(llm_response)


def initialize():
    home_dir: str = os.path.expanduser("~")
    gen_commit_dir: str = os.path.join(home_dir, ".gen-commit")
    if not os.path.exists(gen_commit_dir):
        os.makedirs(gen_commit_dir)
        config_file: str = os.path.join(gen_commit_dir, "config")
        with open(config_file, "w") as f:
            f.write("OPENAI_API_KEY=\nANTHROPIC_API_KEY=")


def gen_commit():
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser()
    arg_parser.add_argument("-m", type=str, help="Commit message")
    arg_parser.add_argument("-d", type=str, help="Commit description")
    arg_parser.add_argument("-o", action="store_true", help="Use OpenAI")
    arg_parser.add_argument(
        "--init", "--initialize", action="store_true", help="Initialize gen-commit"
    )
    arg_parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    found_args, unknown_args = arg_parser.parse_known_args()

    has_message: bool = found_args.m is not None
    has_description: bool = found_args.d is not None
    use_openai: bool = found_args.o

    if found_args.init:
        initialize()
        print("gen-commit initialized successfully.")
        return

    try:
        # Check if there are any commits
        subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD"], text=True
        ).strip()
        commits_exist = True
    except subprocess.CalledProcessError:
        commits_exist = False

    commit_message: str
    commit_description: str
    if commits_exist:
        diff_output: str = subprocess.check_output(
            ["git", "diff", "HEAD"] + unknown_args, text=True
        ).strip()
        formatted_diff: str = format_diff(diff_output)
        commit_message, commit_description = generate_commit_message(
            diff_text=formatted_diff, use_openai=use_openai
        )
        print(commit_message)
        print(commit_description)
    else:
        commit_message: str = found_args.m if has_message else "Initial commit"
        commit_description: str = found_args.d if has_description else ""

    # commit_command: str
    # if commit_description:
    #     commit_command = f'git commit {" ".join(unknown_args)} -m "{commit_message}" -m "{commit_description}"'
    # else:
    #     commit_command = f'git commit {" ".join(unknown_args)} -m "{commit_message}"'
    # # os.system(commit_command)


if __name__ == "__main__":
    gen_commit()
