import https from 'https';
import fs from 'fs';
import os from 'os';
import { URL } from 'url';
import dotenv from 'dotenv';
import path from 'path';
import { parseDriveUrl } from './drive_vault';
import { vaultCatalogTool, vaultResolveTool } from './tools';

dotenv.config({ path: path.resolve(__dirname, '../.env') });

import {
  MultimodalReasoningInputSchema,
  MultimodalReasoningOutputSchema,
  EntityBadge,
  ActionDirective,
  AcousticAnalysis,
  VaultGroundingRef,
  MultimodalReasoningInput,
  MultimodalReasoningOutput,
} from './schemas';

export {
  MultimodalReasoningInputSchema,
  MultimodalReasoningOutputSchema,
  EntityBadge,
  ActionDirective,
  AcousticAnalysis,
  VaultGroundingRef,
  MultimodalReasoningInput,
  MultimodalReasoningOutput,
};

const DEFAULT_VERIFIED_MODELS: string[] = [
  'gemini-3.5-flash',
  'gemini-3.5-flash-lite',
  'gemini-3-flash-preview',
  'gemini-flash-lite-latest',
];

const RETIRED_MODEL_RE = /gemini-(1\.5|2\.0|2\.5)-/i;

export const STATIC_SYSTEM_INSTRUCTION = `[SYSTEM INSTRUCTION]
You are the Sovereign Lean Multimodal Reasoning Engine powered by Frontier Gemini.
Analyze the user instruction along with all audio, visual, gateway context, and Google One 5 TB Vault telemetry.
If an audio recording is present:
1. Transcribe speech into acousticAnalysis.transcript.
2. Characterize pitch, tone, frequency patterns, and noise into acousticAnalysis.audioCharacteristics.
3. Isolate discrepancies or anomalies into acousticAnalysis.detectedAnomalies.
If a Google One Vault asset is referenced, correlate observations against its documented engineering tolerances.
Always extract typed entities with confidence ratings (0.0 to 1.0), prioritized action directives (LOW, MEDIUM, HIGH, CRITICAL), sentiment (POSITIVE, NEUTRAL, NEGATIVE, MIXED), confidenceScore (0.0 to 1.0), and structured step-by-step reasoning.
Respond strictly in valid JSON matching the structured output schema.`;

const MULTIMODAL_RESPONSE_SCHEMA = {
  type: 'OBJECT',
  properties: {
    summary: { type: 'STRING' },
    sentiment: {
      type: 'STRING',
      enum: ['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'MIXED'],
    },
    confidenceScore: { type: 'NUMBER' },
    acousticAnalysis: {
      type: 'OBJECT',
      properties: {
        transcript: { type: 'STRING' },
        audioCharacteristics: { type: 'STRING' },
        detectedAnomalies: { type: 'ARRAY', items: { type: 'STRING' } },
      },
    },
    entities: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          name: { type: 'STRING' },
          category: { type: 'STRING' },
          confidence: { type: 'NUMBER' },
        },
        required: ['name', 'category', 'confidence'],
      },
    },
    actionDirectives: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          priority: {
            type: 'STRING',
            enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
          },
          instruction: { type: 'STRING' },
        },
        required: ['priority', 'instruction'],
      },
    },
    reasoningSteps: {
      type: 'ARRAY',
      items: { type: 'STRING' },
    },
  },
  required: [
    'summary',
    'sentiment',
    'confidenceScore',
    'entities',
    'actionDirectives',
    'reasoningSteps',
  ],
};

export function getModelPriority(envModel = process.env.MODEL_NAME): string[] {
  const candidate = (envModel || '').trim();
  if (candidate && !RETIRED_MODEL_RE.test(candidate)) {
    return [
      candidate,
      ...DEFAULT_VERIFIED_MODELS.filter((model) => model !== candidate),
    ];
  }
  return [...DEFAULT_VERIFIED_MODELS];
}

function resolveGeminiApiKey(): string {
  const envKey =
    process.env.GEMINI_API_KEY || process.env.GOOGLE_GENAI_API_KEY || '';
  const cleanedEnv = envKey.trim().replace(/^["']|["']$/g, '');
  if (cleanedEnv) {
    return cleanedEnv;
  }

  try {
    const keysPath = path.join(os.homedir(), '.lunora', 'keys.json');
    if (fs.existsSync(keysPath)) {
      const parsed = JSON.parse(fs.readFileSync(keysPath, 'utf8'));
      const fileKey = String(
        parsed?.GEMINI_API_KEY || parsed?.gemini_api_key || ''
      )
        .trim()
        .replace(/^["']|["']$/g, '');
      if (fileKey) return fileKey;
    }
  } catch {
    // Fall through cleanly if keys.json is unreadable
  }
  return '';
}

export function normalizeRawInput(rawInput: unknown): MultimodalReasoningInput {
  const payload =
    rawInput && typeof rawInput === 'object'
      ? { ...(rawInput as Record<string, unknown>) }
      : {};

  if (!payload.audioBase64 && typeof payload.audio_b64 === 'string') {
    payload.audioBase64 = payload.audio_b64;
  }
  if (!payload.imageBase64 && typeof payload.image_b64 === 'string') {
    payload.imageBase64 = payload.image_b64;
  }

  const basePrompt =
    typeof payload.prompt === 'string' && payload.prompt.trim().length > 0
      ? payload.prompt.trim()
      : 'Analyze the provided multimodal context.';

  if (payload.context !== undefined && payload.context !== null) {
    const contextText =
      typeof payload.context === 'string'
        ? payload.context.trim()
        : JSON.stringify(payload.context);
    if (contextText && contextText !== '{}') {
      payload.prompt = `${basePrompt}\n\n[GATEWAY CONTEXT]\n${contextText.slice(0, 4000)}`;
      return MultimodalReasoningInputSchema.parse(payload);
    }
  }

  payload.prompt = basePrompt;
  return MultimodalReasoningInputSchema.parse(payload);
}

function normalizeOutput(parsed: any, vaultRef?: VaultGroundingRef): MultimodalReasoningOutput {
  const summary = typeof parsed?.summary === 'string'
    ? parsed.summary
    : (typeof parsed === 'string' ? parsed : JSON.stringify(parsed));

  let acousticAnalysis: AcousticAnalysis | undefined = undefined;
  if (parsed?.acousticAnalysis) {
    acousticAnalysis = {
      transcript: String(parsed.acousticAnalysis.transcript || ''),
      audioCharacteristics: String(parsed.acousticAnalysis.audioCharacteristics || ''),
      detectedAnomalies: Array.isArray(parsed.acousticAnalysis.detectedAnomalies)
        ? parsed.acousticAnalysis.detectedAnomalies.map(String)
        : [],
    };
  }

  const entities: EntityBadge[] = Array.isArray(parsed?.entities)
    ? parsed.entities.map((e: any) => ({
        name: String(e.name || e.entity || e.label || 'Unknown'),
        category: String(e.category || e.type || 'General'),
        confidence: typeof e.confidence === 'number'
          ? e.confidence
          : (parseFloat(String(e.confidence || '0.9')) || 0.9),
      }))
    : [];

  const validPriorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;
  const actionDirectives: ActionDirective[] = Array.isArray(parsed?.actionDirectives)
    ? parsed.actionDirectives.map((d: any) => {
        const rawPri = String(d.priority || 'MEDIUM').toUpperCase();
        const priority = validPriorities.includes(rawPri as any)
          ? (rawPri as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL')
          : 'MEDIUM';
        return {
          priority,
          instruction: String(d.instruction || d.action || ''),
        };
      })
    : [];

  const reasoningSteps: string[] = Array.isArray(parsed?.reasoningSteps)
    ? parsed.reasoningSteps.map(String)
    : (Array.isArray(parsed?.steps) ? parsed.steps.map(String) : []);

  const validSentiments = ['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'MIXED'] as const;
  const rawSent = String(parsed?.sentiment || 'NEUTRAL').toUpperCase();
  const sentiment = validSentiments.includes(rawSent as any) ? (rawSent as any) : 'NEUTRAL';
  const confidenceScore = typeof parsed?.confidenceScore === 'number'
    ? Math.max(0, Math.min(1, parsed.confidenceScore))
    : 0.9;

  return {
    summary,
    sentiment,
    confidenceScore,
    acousticAnalysis,
    vaultGrounding: vaultRef,
    entities,
    actionDirectives,
    reasoningSteps,
  };
}

function requestHttpsJson(
  urlStr: string,
  payload: unknown,
  apiKey: string,
  timeoutMs = 30000
): Promise<any> {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(urlStr);
    const postData = Buffer.from(JSON.stringify(payload), 'utf8');

    const options: https.RequestOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 443,
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length,
        'x-goog-api-key': apiKey,
      },
    };

    const req = https.request(options, (res) => {
      const chunks: Buffer[] = [];
      res.on('data', (d) => chunks.push(d));
      res.on('end', () => {
        const responseBody = Buffer.concat(chunks).toString('utf8');
        if (res.statusCode && (res.statusCode < 200 || res.statusCode >= 300)) {
          reject(new Error(`API HTTP ${res.statusCode}: ${responseBody}`));
        } else {
          try {
            resolve(JSON.parse(responseBody));
          } catch (err) {
            reject(new Error(`Failed to parse response JSON: ${responseBody}`));
          }
        }
      });
    });

    req.setTimeout(timeoutMs, () => {
      req.destroy();
      reject(new Error(`Request timed out after ${timeoutMs}ms`));
    });

    req.on('error', (err) => reject(err));
    req.write(postData);
    req.end();
  });
}

export async function executeMultimodalReasoning(
  rawInput: unknown
): Promise<MultimodalReasoningOutput> {
  const input = normalizeRawInput(rawInput);
  const apiKey = resolveGeminiApiKey();

  if (!apiKey) {
    throw new Error('GEMINI_API_KEY environment variable is not defined.');
  }

  let vaultRef: VaultGroundingRef | undefined = undefined;
  let vaultContextPrompt = '';

  const targetRef = input.driveFileUrl || input.driveFileId || input.vaultFileName;
  if (targetRef) {
    const resolved = await vaultResolveTool({ driveUrlOrId: targetRef });
    const asset = resolved.found ? resolved.asset : null;
    if (asset) {
      vaultRef = {
        fileName: asset.name,
        driveUrl: asset.driveUrl,
        mimeType: asset.mimeType,
        sizeBytes: asset.sizeBytes,
        status: 'GROUNDED_ZERO_LOCAL_IO',
      };
      vaultContextPrompt = `[GOOGLE ONE 5 TB VAULT GROUNDING ASSET]
Asset: ${asset.name}
MIME: ${asset.mimeType}
Size: ${(asset.sizeBytes / 1024 / 1024).toFixed(1)} MB (Direct Cloud Stream, Zero Host Disk IO)
Description: ${asset.description}
Cloud Reference: ${asset.driveUrl}
Directives: Cross-reference telemetry against the structural tolerances and vibration boundaries documented in this asset.`;
    } else {
      const extractedId = parseDriveUrl(targetRef) || targetRef;
      vaultRef = {
        fileName: input.vaultFileName || `Drive_Asset_${extractedId.slice(0, 8)}`,
        driveUrl: input.driveFileUrl || `https://drive.google.com/file/d/${extractedId}/view`,
        mimeType: 'application/octet-stream',
        sizeBytes: 0,
        status: 'DIRECT_DRIVE_REF',
      };
      vaultContextPrompt = `[GOOGLE DRIVE CLOUD ASSET]
Reference: ${vaultRef.driveUrl}
File Name: ${vaultRef.fileName}
Directives: Ground diagnostic inference referencing this cloud asset.`;
    }
  } else {
    const catalog = await vaultCatalogTool({});
    if (catalog.length > 0) {
      const compactLines = catalog
        .slice(0, 8)
        .map((item) => `- ${item.name} (${item.id}): ${item.description}`)
        .join('\n');
      vaultContextPrompt = `[GOOGLE ONE 5 TB VAULT CATALOG INDEX]\n${compactLines}`;
    }
  }

  // Place dynamic vault grounding + user prompt after static systemInstruction
  // so Gemini implicit prefix caching reuses STATIC_SYSTEM_INSTRUCTION across requests.
  const userTextSections: string[] = [];
  if (vaultContextPrompt) {
    userTextSections.push(vaultContextPrompt);
  }
  userTextSections.push(`[USER REQUEST]\n${input.prompt}`);

  const parts: Array<Record<string, unknown>> = [
    { text: userTextSections.join('\n\n') },
  ];

  let audioBypassedReason: string | null = null;
  if (input.audioBase64) {
    const cleanBase64 = input.audioBase64.replace(/\s+/g, '');
    if (cleanBase64.length < 200) {
      audioBypassedReason = 'Zero-byte or empty audio header received (< 200 bytes); bypassed inline ingestion.';
    } else {
      const mime = input.audioMimeType || 'audio/wav';
      parts.push({
        inlineData: {
          mimeType: mime,
          data: cleanBase64,
        },
      });
    }
  }

  if (input.imageBase64) {
    const cleanImgBase64 = input.imageBase64.replace(/\s+/g, '');
    if (cleanImgBase64.length > 200) {
      const mime = input.imageMimeType || 'image/png';
      parts.push({
        inlineData: {
          mimeType: mime,
          data: cleanImgBase64,
        },
      });
    }
  }

  // Single-Pass Structured Output Grounding (1 HTTPS call per model attempt; header-only API auth)
  let lastError: Error | null = null;
  for (const model of getModelPriority()) {
    try {
      const payload = {
        systemInstruction: {
          parts: [{ text: STATIC_SYSTEM_INSTRUCTION }],
        },
        contents: [{ role: 'user', parts }],
        generationConfig: {
          temperature: 0.2,
          responseMimeType: 'application/json',
          responseSchema: MULTIMODAL_RESPONSE_SCHEMA,
        },
      };
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
      const result = await requestHttpsJson(endpoint, payload, apiKey, 25000);
      const rawJsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!rawJsonText) {
        throw new Error(`Model ${model} produced an empty reasoning candidate.`);
      }

      let parsed: any;
      try {
        parsed = JSON.parse(rawJsonText);
      } catch {
        const cleanText = rawJsonText
          .replace(/^```json\s*/i, '')
          .replace(/\s*```$/, '')
          .trim();
        parsed = JSON.parse(cleanText);
      }

      const output = normalizeOutput(parsed, vaultRef);
      if (audioBypassedReason) {
        if (!output.acousticAnalysis) {
          output.acousticAnalysis = {
            transcript: '',
            audioCharacteristics: 'Zero-byte or synthetic test header bypassed.',
            detectedAnomalies: [audioBypassedReason],
          };
        } else {
          output.acousticAnalysis.detectedAnomalies.push(audioBypassedReason);
        }
      }
      return output;
    } catch (err: any) {
      console.warn(`[FAILOVER] ${model} failed: ${err.message}. Trying next candidate...`);
      lastError = err;
    }
  }

  throw lastError || new Error('All verified models exhausted.');
}
