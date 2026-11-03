import { z } from 'zod';

export const SentimentSchema = z.enum(['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'MIXED']);
export type Sentiment = z.infer<typeof SentimentSchema>;

export const PrioritySchema = z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
export type Priority = z.infer<typeof PrioritySchema>;

export const EntityBadgeSchema = z.object({
  name: z.string().describe('Extracted named entity or key subject'),
  category: z.string().default('General').describe('Entity classification category'),
  confidence: z.number().min(0).max(1).default(0.9).describe('Extraction certainty score'),
});
export type EntityBadge = z.infer<typeof EntityBadgeSchema>;

export const ActionDirectiveSchema = z.object({
  priority: PrioritySchema.default('MEDIUM').describe('Execution priority level'),
  instruction: z.string().describe('Tactical action instruction'),
});
export type ActionDirective = z.infer<typeof ActionDirectiveSchema>;

export const AcousticAnalysisSchema = z.object({
  transcript: z.string().default(''),
  audioCharacteristics: z.string().default(''),
  detectedAnomalies: z.array(z.string()).default([]),
});
export type AcousticAnalysis = z.infer<typeof AcousticAnalysisSchema>;

export const VaultGroundingRefSchema = z.object({
  fileName: z.string(),
  driveUrl: z.string(),
  mimeType: z.string(),
  sizeBytes: z.number(),
  status: z.enum(['GROUNDED_ZERO_LOCAL_IO', 'DIRECT_DRIVE_REF']).default('GROUNDED_ZERO_LOCAL_IO'),
});
export type VaultGroundingRef = z.infer<typeof VaultGroundingRefSchema>;

export const MultimodalReasoningInputSchema = z.object({
  prompt: z.string().default('Analyze the provided multimodal context.'),
  imageBase64: z.string().optional(),
  imageMimeType: z.string().optional(),
  audioBase64: z.string().optional(),
  audioMimeType: z.string().optional(),
  audioDurationMs: z.number().optional(),
  driveFileUrl: z.string().optional(),
  driveFileId: z.string().optional(),
  vaultFileName: z.string().optional(),
});
export type MultimodalReasoningInput = z.infer<typeof MultimodalReasoningInputSchema>;

export const MultimodalReasoningOutputSchema = z.object({
  summary: z.string().describe('High-density executive synthesis'),
  sentiment: SentimentSchema.optional().default('NEUTRAL').describe('Inferred sentiment state'),
  confidenceScore: z.number().min(0).max(1).optional().default(0.9).describe('Overall analytical confidence score'),
  acousticAnalysis: AcousticAnalysisSchema.optional(),
  vaultGrounding: VaultGroundingRefSchema.optional(),
  entities: z.array(EntityBadgeSchema).default([]),
  actionDirectives: z.array(ActionDirectiveSchema).default([]),
  reasoningSteps: z.array(z.string()).default([]),
  sessionId: z.string().optional(),
  latencyMs: z.number().optional(),
});
export type MultimodalReasoningOutput = z.infer<typeof MultimodalReasoningOutputSchema>;

// Backwards compatibility aliases
export const EntitySchema = EntityBadgeSchema;
export const ActionSchema = z.object({
  actionType: z.string(),
  target: z.string(),
  parameters: z.record(z.any()),
});
export const GroundingSourceSchema = z.object({
  title: z.string(),
  uri: z.string(),
  relevance: z.number().min(0).max(1),
});
export const MultimodalOutputSchema = MultimodalReasoningOutputSchema;
export const MultimodalInputSchema = MultimodalReasoningInputSchema;
export type MultimodalInput = MultimodalReasoningInput;
export type MultimodalOutput = MultimodalReasoningOutput;

export const ResearchSynthesisInputSchema = z.object({
  topic: z.string().describe('Research topic to synthesize'),
  maxSources: z.number().optional().default(5),
});

export const ResearchSynthesisOutputSchema = z.object({
  topic: z.string(),
  executiveSummary: z.string(),
  keyInsights: z.array(z.string()),
  citations: z.array(
    z.object({
      sourceTitle: z.string(),
      uri: z.string(),
    })
  ),
  recommendedNextSteps: z.array(z.string()),
});
export type ResearchSynthesisInput = z.infer<typeof ResearchSynthesisInputSchema>;
export type ResearchSynthesisOutput = z.infer<typeof ResearchSynthesisOutputSchema>;
