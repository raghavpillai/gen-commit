import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { z } from "zod";

const HOME_DIR = homedir();
export const CONFIG_FILE = join(HOME_DIR, ".gen-commit");

const ConfigSchema = z.object({
  MODEL: z.string().min(1, "MODEL is required and cannot be empty"),
  OPENAI_API_KEY: z.string().optional(),
  ANTHROPIC_API_KEY: z.string().optional(),
  GOOGLE_API_KEY: z.string().optional(),
  MAX_TOKENS_ALLOWED: z.string().optional(),
});

export type Config = z.infer<typeof ConfigSchema>;

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export function readConfig(): Config {
  if (!existsSync(CONFIG_FILE)) {
    throw new ConfigError(
      `Config file not found at ${CONFIG_FILE}. Please run \`gencommit --init\` to create a config file.`,
    );
  }

  const config: Record<string, string> = {};
  const fileContent = readFileSync(CONFIG_FILE, "utf-8");

  for (const line of fileContent.split("\n")) {
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.startsWith("#")) {
      const separatorIndex = trimmedLine.indexOf("=");
      if (separatorIndex !== -1) {
        const key = trimmedLine.slice(0, separatorIndex).trim();
        const value = trimmedLine.slice(separatorIndex + 1).trim();
        if (key) {
          config[key] = value;
        }
      }
    }
  }

  try {
    return ConfigSchema.parse(config);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const issues = error.issues.map((issue) => issue.message).join(", ");
      throw new ConfigError(`Invalid config file at ${CONFIG_FILE}: ${issues}`);
    }
    throw error;
  }
}

export function readVersionFromPackageJson(): string {
  try {
    const packageJsonPath = join(process.cwd(), "package.json");
    if (existsSync(packageJsonPath)) {
      const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf-8"));
      return packageJson.version || "0.0.0";
    }
  } catch (_error) {
    try {
      const packageJson = require("../../package.json");
      return packageJson.version || "0.0.0";
    } catch {
      return "0.0.0";
    }
  }
  return "0.0.0";
}
