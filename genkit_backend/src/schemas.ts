import { z } from 'zod';

export const EntitySchema = z.object({
  name: z.string().describe('Extracted named entity or key subject'),
  category: z.string().describe('Entity type: PERSON, ORGANIZATION, TECHNOLOGY, METRIC, TEMPORAL'),
  confidence: z.number().min(0).max(1).describe('Extraction certainty score'),
});

export const ActionSchema = z.object({
  actionType: z.string().describe('Action directive: EXECUTE_TOOL, DISPATCH_ALERT, STORE_RECORD, DELEGATE_CLOUD'),
  target: z.string().describe('Target system or endpoint'),
  parameters: z.record(z.any()).describe('Arbitrary key-value payload for tool execution'),
});

export const GroundingSourceSchema = z.object({
  title: z.string().describe('Document title or asset identifier'),
  uri: z.string().describe('GCS URI, NotebookLM note URI, or canonical URL'),
  relevance: z.number().min(0).max(1).describe('Relevance score to user query'),
});

export const MultimodalOutputSchema = z.object({
  sessionId: z.string().describe('Unique UUID tracking the multi-turn session'),
  summary: z.string().describe('High-density executive synthesis of multimodal inputs'),
  sentiment: z.enum(['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'MIXED']).describe('Inferred sentiment state'),
  entities: z.array(EntitySchema).describe('Entities resolved from text and media assets'),
  actions: z.array(ActionSchema).describe('Recommended deterministic action payloads'),
  confidenceScore: z.number().min(0).max(1).describe('Overall analytical confidence score'),
  groundingSources: z.array(GroundingSourceSchema).describe('Citations grounding this response'),
});

export const MultimodalInputSchema = z.object({
  sessionId: z.string().describe('Session identifier'),
  prompt: z.string().describe('User instruction or query'),
  media: z.array(
    z.object({
      url: z.string().describe('Direct data URL (e.g. data:image/png;base64,...) or HTTPS/GCS URL'),
      contentType: z.string().describe('MIME type of the media object'),
    })
  ).optional().describe('Multimodal attachments (images, PDFs, audio clips)'),
  temperature: z.number().optional().default(0.2),
});

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

export type MultimodalInput = z.infer<typeof MultimodalInputSchema>;
export type MultimodalOutput = z.infer<typeof MultimodalOutputSchema>;
export type ResearchSynthesisInput = z.infer<typeof ResearchSynthesisInputSchema>;
export type ResearchSynthesisOutput = z.infer<typeof ResearchSynthesisOutputSchema>;
