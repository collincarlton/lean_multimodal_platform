import { z } from 'zod';
import https from 'https';
import { URL } from 'url';
import dotenv from 'dotenv';
import path from 'path';
import { resolveVaultFile, parseDriveUrl } from './drive_vault';

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

const VERIFIED_MODELS: string[] = [
  'gemini-2.0-flash',
  'gemini-2.0-flash-lite',
  'gemini-1.5-pro',
];

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
  const input = MultimodalReasoningInputSchema.parse(rawInput);
  const rawKey = process.env.GEMINI_API_KEY || '';
  const apiKey = rawKey.trim().replace(/^["']|["']$/g, '');

  if (!apiKey) {
    throw new Error('GEMINI_API_KEY environment variable is not defined.');
  }

  let vaultRef: VaultGroundingRef | undefined = undefined;
  let vaultContextPrompt = '';

  const targetRef = input.driveFileUrl || input.driveFileId || input.vaultFileName;
  if (targetRef) {
    const asset = resolveVaultFile(targetRef);
    if (asset) {
      vaultRef = {
        fileName: asset.name,
        driveUrl: asset.driveUrl,
        mimeType: asset.mimeType,
        sizeBytes: asset.sizeBytes,
        status: 'GROUNDED_ZERO_LOCAL_IO',
      };
      vaultContextPrompt = `
[GOOGLE ONE 5 TB VAULT GROUNDING ASSET]
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
      vaultContextPrompt = `
[GOOGLE DRIVE CLOUD ASSET]
Reference: ${vaultRef.driveUrl}
File Name: ${vaultRef.fileName}
Directives: Ground diagnostic inference referencing this cloud asset.`;
    }
  }

  const systemInstructionText = `[SYSTEM INSTRUCTION]
You are the Sovereign Lean Multimodal Reasoning Engine powered by Frontier Gemini.
Analyze the user instruction along with all audio, visual, and Google One 5 TB Vault telemetry.
If an audio recording is present:
1. Transcribe speech into acousticAnalysis.transcript.
2. Characterize pitch, tone, frequency patterns, and noise into acousticAnalysis.audioCharacteristics.
3. Isolate discrepancies or anomalies into acousticAnalysis.detectedAnomalies.
If a Google One Vault asset is referenced, correlate acoustic anomalies against its documented engineering tolerances.
Always extract typed entities with confidence ratings, prioritized action directives (LOW, MEDIUM, HIGH, CRITICAL), and structured step-by-step reasoning.
Output strictly in valid JSON matching this schema:
{
  "summary": "Diagnostic synthesis",
  "acousticAnalysis": {
    "transcript": "Transcribed speech",
    "audioCharacteristics": "Acoustic observations",
    "detectedAnomalies": ["Anomaly 1"]
  },
  "entities": [{"name": "Entity Name", "category": "Hardware", "confidence": 0.95}],
  "actionDirectives": [{"priority": "HIGH", "instruction": "Action instruction"}],
  "reasoningSteps": ["Step 1", "Step 2"]
}

${vaultContextPrompt}

[USER REQUEST]
${input.prompt}`;

  const parts: Array<Record<string, unknown>> = [
    { text: systemInstructionText }
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

  // Two-Pass Grounding Engine (G-02): Pass 1 Multimodal Analysis -> Pass 2 Structured JSON
  let lastError: Error | null = null;
  for (const model of VERIFIED_MODELS) {
    try {
      // Pass 1: Unstructured Grounded Multimodal Reasoning
      const pass1Payload = {
        contents: [{ role: 'user', parts }],
        generationConfig: { temperature: 0.2 },
      };
      const pass1Endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      const pass1Result = await requestHttpsJson(pass1Endpoint, pass1Payload, apiKey, 25000);
      const pass1Text = pass1Result.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!pass1Text) {
        throw new Error(`Model ${model} produced an empty reasoning candidate.`);
      }

      // Pass 2: Strict Structured JSON Schema Extraction
      const pass2Prompt = `Extract the multimodal reasoning and diagnostic analysis into exact JSON matching this schema:
{
  "summary": "High-density synthesis",
  "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "MIXED",
  "confidenceScore": 0.95,
  "acousticAnalysis": {"transcript": "...", "audioCharacteristics": "...", "detectedAnomalies": []},
  "entities": [{"name": "...", "category": "...", "confidence": 0.9}],
  "actionDirectives": [{"priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL", "instruction": "..."}],
  "reasoningSteps": ["Step 1", "Step 2"]
}

Reasoning Analysis:
${pass1Text}`;

      const pass2Payload = {
        contents: [{ role: 'user', parts: [{ text: pass2Prompt }] }],
        generationConfig: {
          temperature: 0.1,
          responseMimeType: 'application/json',
        },
      };
      const pass2Endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      const pass2Result = await requestHttpsJson(pass2Endpoint, pass2Payload, apiKey, 25000);
      const rawJsonText = pass2Result.candidates?.[0]?.content?.parts?.[0]?.text || '{}';

      let parsed: any;
      try {
        parsed = JSON.parse(rawJsonText);
      } catch {
        const cleanText = rawJsonText.replace(/^```json\n?/, '').replace(/\n?```$/, '');
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
