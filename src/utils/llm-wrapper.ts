import { createAnthropic } from "@ai-sdk/anthropic";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { createOpenAI } from "@ai-sdk/openai";
import { generateObject } from "ai";
import type { z } from "zod";
import { type Config, readConfig } from "./config";

export interface ModelParams {
  provider: string;
  modelName: string;
  apiKey: string;
}

export function getModelParams(): ModelParams {
  const config: Config = readConfig();

  if (!config.MODEL) {
    throw new Error("MODEL not found in config");
  }

  const [provider, modelName] = config.MODEL.toLowerCase().split(":", 2);

  if (!provider || !modelName) {
    throw new Error('Invalid MODEL format. Expected "provider:model-name"');
  }

  let apiKey: string | undefined;

  switch (provider) {
    case "openai":
      apiKey = config.OPENAI_API_KEY;
      if (!apiKey) {
        throw new Error("OPENAI_API_KEY not found in config");
      }
      break;
    case "anthropic":
      apiKey = config.ANTHROPIC_API_KEY;
      if (!apiKey) {
        throw new Error("ANTHROPIC_API_KEY not found in config");
      }
      break;
    case "google":
      apiKey = config.GOOGLE_API_KEY;
      if (!apiKey) {
        throw new Error("GOOGLE_API_KEY not found in config");
      }
      break;
    default:
      throw new Error(`Invalid provider: ${provider}`);
  }

  return { provider, modelName, apiKey };
}

export function getModel(params: ModelParams) {
  const { provider, modelName, apiKey } = params;

  switch (provider) {
    case "openai": {
      const openai = createOpenAI({ apiKey });
      return openai(modelName);
    }
    case "anthropic": {
      const anthropic = createAnthropic({ apiKey });
      return anthropic(modelName);
    }
    case "google": {
      const google = createGoogleGenerativeAI({ apiKey });
      return google(modelName);
    }
    default:
      throw new Error(`Unsupported provider: ${provider}`);
  }
}

export async function chat<T extends z.ZodType>(
  systemPrompt: string,
  userPrompt: string,
  schema: T,
): Promise<z.infer<T>> {
  const params = getModelParams();
  const model = getModel(params);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000);

  try {
    const result = await generateObject({
      model,
      schema,
      system: systemPrompt,
      prompt: userPrompt,
      abortSignal: controller.signal,
      providerOptions: {
        openai: {
          reasoningEffort: "minimal",
        },
        anthropic: {
          reasoningEffort: "minimal",
        },
        google: {
          reasoningEffort: "minimal",
        },
      },
    });

    return result.object as z.infer<T>;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(
      `Failed to generate object using ${params.provider}:${params.modelName}: ${errorMessage}`,
    );
  } finally {
    clearTimeout(timeoutId);
  }
}
