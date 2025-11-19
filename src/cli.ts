#!/usr/bin/env node

import { execSync, spawnSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { z } from "zod";
import {
  CONFIG_FILE,
  type Config,
  ConfigError,
  readConfig,
  readVersionFromPackageJson,
} from "./utils/config";
import { chat } from "./utils/llm-wrapper";
import {
  COMMIT_PROMPT_SYSTEM,
  COMMIT_PROMPT_WITH_DESCRIPTION,
} from "./utils/prompts";

const VERSION = readVersionFromPackageJson();

const CommitMessageSchema = z.object({
  commit_message: z
    .string()
    .describe("Brief descriptive commit message in no longer than 10 words"),
  commit_description: z
    .string()
    .describe("Hyphenated bullet point list of changes"),
});

type CommitMessage = z.infer<typeof CommitMessageSchema>;

interface Args {
  m?: string;
  d?: string;
  init?: boolean;
  version?: boolean;
  unknownArgs: string[];
}

function parseArgs(): Args {
  const args = process.argv.slice(2);
  const parsed: Args = { unknownArgs: [] };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "-m" && i + 1 < args.length) {
      parsed.m = args[++i];
    } else if (arg === "-d" && i + 1 < args.length) {
      parsed.d = args[++i];
    } else if (arg === "--init" || arg === "--initialize") {
      parsed.init = true;
    } else if (arg === "--version" || arg === "--v") {
      parsed.version = true;
    } else {
      parsed.unknownArgs.push(arg);
    }
  }

  return parsed;
}

function formatDiff(diffText: string, maxLineLength: number): string {
  const fileChanges: Record<
    string,
    Array<{ type: "add" | "remove"; content: string }>
  > = {};
  let currentFile = "";

  for (const line of diffText.split("\n")) {
    if (line.startsWith("diff --git")) {
      const parts = line.split(" ");
      currentFile = parts[parts.length - 1].replace(/^b\//, "");
      fileChanges[currentFile] = [];
    } else if (line.startsWith("+") && !line.startsWith("+++")) {
      if (currentFile) {
        fileChanges[currentFile].push({
          type: "add",
          content: line.slice(1, maxLineLength + 1).trim(),
        });
      }
    } else if (line.startsWith("-") && !line.startsWith("---")) {
      if (currentFile) {
        fileChanges[currentFile].push({
          type: "remove",
          content: line.slice(1, maxLineLength + 1).trim(),
        });
      }
    }
  }

  let formattedDiff = "### Git Changes Summary ###\n\n";

  for (const [filename, changes] of Object.entries(fileChanges)) {
    formattedDiff += `File: ${filename}\n`;
    formattedDiff += "Changes:\n";

    const limit = filename.endsWith(".lock") ? 30 : 2000;
    const limitedChanges = changes.slice(0, limit);

    for (const change of limitedChanges) {
      const prefix = change.type === "add" ? "+" : "-";
      formattedDiff += `${prefix} ${change.content}\n`;
    }

    if (changes.length > limit) {
      formattedDiff += `\n... (${changes.length - limit} additional changes truncated)\n`;
    }

    formattedDiff += "\n";
  }

  return formattedDiff;
}

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

function truncateToTokenLimit(text: string, maxTokens: number): string {
  const estimatedTokens = estimateTokens(text);
  if (estimatedTokens <= maxTokens) {
    return text;
  }

  const charLimit = maxTokens * 4;
  const halfLimit = Math.floor(charLimit / 2);
  const start = text.slice(0, halfLimit);
  const end = text.slice(-halfLimit);
  return `${start}\n\n... [truncated] ...\n\n${end}`;
}

async function generateCommitMessage(
  diffText: string,
  maxTokensAllowed: number,
  maxRetries = 3,
): Promise<CommitMessage> {
  if (!diffText) {
    throw new Error("No changes to commit");
  }

  const truncatedDiff = truncateToTokenLimit(diffText, maxTokensAllowed);
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 1) {
        console.log(`Retrying... (attempt ${attempt}/${maxRetries})`);
      }

      const startTime = Date.now();

      const llmResponse = await chat<typeof CommitMessageSchema>(
        COMMIT_PROMPT_SYSTEM(),
        COMMIT_PROMPT_WITH_DESCRIPTION(truncatedDiff),
        CommitMessageSchema,
      );

      const endTime = Date.now();
      const duration = ((endTime - startTime) / 1000).toFixed(2);
      console.log(`[DEBUG] AI generation completed in ${duration}s`);

      return llmResponse;
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries) {
        const delay = Math.min(1000 * 2 ** (attempt - 1), 5000);
        console.error(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  console.error("Error generating commit message:", lastError);
  throw lastError;
}

const DEFAULT_CONFIG_TEMPLATE = `MODEL=openai:gpt-5-mini
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
MAX_LINE_LENGTH=300
MAX_TOKENS_ALLOWED=30000`;

async function initialize(): Promise<boolean> {
  const configFile = CONFIG_FILE;

  if (existsSync(configFile)) {
    const readline = require("node:readline").createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    return new Promise<boolean>((resolve) => {
      readline.question(
        `Config file already exists at ${configFile}. Overwrite? (Y/n): `,
        (answer: string) => {
          readline.close();
          const response = answer.trim().toLowerCase();

          if (response !== "y" && response !== "") {
            console.log("Initialization cancelled.");
            resolve(false);
            return;
          }

          writeFileSync(configFile, DEFAULT_CONFIG_TEMPLATE);
          console.log(
            "gen-commit initialized successfully, wrote config to ~/.gen-commit",
          );
          resolve(true);
        },
      );
    });
  }

  writeFileSync(configFile, DEFAULT_CONFIG_TEMPLATE);
  console.log(
    "gen-commit initialized successfully, wrote config to ~/.gen-commit",
  );
  return true;
}

async function main() {
  const args = parseArgs();

  if (args.version) {
    console.log(`gencommit ${VERSION}`);
    process.exit(0);
  }

  if (args.init) {
    const success = await initialize();
    process.exit(success ? 0 : 1);
  }

  let config: Config;
  try {
    config = readConfig();
  } catch (error) {
    if (error instanceof ConfigError) {
      console.error(error.message);
      process.exit(1);
    }
    throw error;
  }

  const MAX_LINE_LENGTH = parseInt(config.MAX_LINE_LENGTH || "300", 10);
  const MAX_TOKENS_ALLOWED = parseInt(config.MAX_TOKENS_ALLOWED || "30000", 10);

  const hasMessage = args.m !== undefined;
  const hasDescription = args.d !== undefined;

  let commitsExist = true;
  try {
    execSync("git rev-parse --verify HEAD", {
      encoding: "utf-8",
      stdio: "pipe",
    });
  } catch {
    commitsExist = false;
  }

  if (args.unknownArgs.includes("-a")) {
    try {
      const unstagedChanges = execSync("git status --porcelain", {
        encoding: "utf-8",
        stdio: "pipe",
      }).trim();
      if (!unstagedChanges) {
        console.error("No changes detected.");
        process.exit(1);
      }
    } catch (_error) {
      console.error("Error checking for unstaged changes");
      process.exit(1);
    }
  }

  try {
    const stagedChanges = execSync("git diff --staged --name-only", {
      encoding: "utf-8",
      stdio: "pipe",
    }).trim();
    if (!stagedChanges && !args.unknownArgs.includes("-a")) {
      console.error("No changes staged for commit.");
      process.exit(1);
    }
  } catch (_error) {
    console.error("Error checking staged changes");
    process.exit(1);
  }

  let commitMessage: string;
  let commitDescription: string;

  if (commitsExist) {
    try {
      const diffOutput = execSync("git diff --staged", {
        encoding: "utf-8",
        stdio: "pipe",
      }).trim();
      const formattedDiff = formatDiff(diffOutput, MAX_LINE_LENGTH);
      const commitMessageObject = await generateCommitMessage(
        formattedDiff,
        MAX_TOKENS_ALLOWED,
      );
      commitMessage =
        hasMessage && args.m ? args.m : commitMessageObject.commit_message;
      commitDescription =
        hasDescription && args.d
          ? args.d
          : commitMessageObject.commit_description;
    } catch (error) {
      console.error("Error generating commit message:", error);
      process.exit(1);
    }
  } else {
    commitMessage = hasMessage && args.m ? args.m : "Initial commit";
    commitDescription = hasDescription && args.d ? args.d : "";
  }

  const gitArgs = ["commit", ...args.unknownArgs, "-m", commitMessage];
  if (commitDescription) {
    gitArgs.push("-m", commitDescription);
  }

  // const result = spawnSync("git", gitArgs, {
  //   encoding: "utf-8",
  //   stdio: "inherit",
  // });

  // if (result.error || result.status !== 0) {
  //   console.error("Error executing git commit");
  //   process.exit(1);
  // }
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
