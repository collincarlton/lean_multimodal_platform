import * as fs from 'fs';
import * as path from 'path';
import { ai } from './index';
import {
  MultimodalInputSchema,
  MultimodalOutputSchema,
  MultimodalInput,
  MultimodalOutput,
  ResearchSynthesisInputSchema,
  ResearchSynthesisOutputSchema,
  ResearchSynthesisInput,
  ResearchSynthesisOutput,
} from './schemas';

// Direct Context Grounding (2M Token Context Window)
let groundingCorpus = '';
try {
  const corpusPath = path.resolve(__dirname, '../../knowledge_vault/domain_grounding_corpus.md');
  if (fs.existsSync(corpusPath)) {
    groundingCorpus = fs.readFileSync(corpusPath, 'utf-8');
  }
} catch (_) {}

export const multimodalAssistantFlow = ai.defineFlow(
  {
    name: 'multimodalAssistantFlow',
    inputSchema: MultimodalInputSchema,
    outputSchema: MultimodalOutputSchema,
  },
  async (input: MultimodalInput): Promise<MultimodalOutput> => {
    const promptParts: any[] = [{ text: input.prompt }];

    if (input.media && input.media.length > 0) {
      for (const m of input.media) {
        promptParts.push({
          media: {
            url: m.url,
            contentType: m.contentType,
          },
        });
      }
    }

    const response = await ai.generate({
      model: 'googleai/gemini-3.8-flash',
      prompt: promptParts,
      system: `You are an elite autonomous multimodal systems architect.
Process all multimodal attachments (images, documents, diagrams, audio).
Ground every claim with rigorous precision using the domain knowledge context below.

DOMAIN GROUNDING CONTEXT (NOTEBOOKLM / KNOWLEDGE VAULT):
${groundingCorpus}

Output must strictly adhere to the requested JSON schema.`,
      config: {
        temperature: input.temperature ?? 0.2,
      },
      output: {
        schema: MultimodalOutputSchema,
      },
    });

    const output = response.output;
    if (!output) {
      throw new Error('Gemini model failed to produce structured JSON matching MultimodalOutputSchema.');
    }

    return output;
  }
);

export const deepResearchSynthesisFlow = ai.defineFlow(
  {
    name: 'deepResearchSynthesisFlow',
    inputSchema: ResearchSynthesisInputSchema,
    outputSchema: ResearchSynthesisOutputSchema,
  },
  async (input: ResearchSynthesisInput): Promise<ResearchSynthesisOutput> => {
    const response = await ai.generate({
      model: 'googleai/gemini-3.8-flash',
      prompt: `Synthesize comprehensive domain research for topic: "${input.topic}".
Formulate strategic takeaways and clear next steps using the domain context below.

DOMAIN GROUNDING CONTEXT:
${groundingCorpus}`,
      config: {
        temperature: 0.1,
      },
      output: {
        schema: ResearchSynthesisOutputSchema,
      },
    });

    const output = response.output;
    if (!output) {
      throw new Error('Research synthesis output failed schema validation.');
    }
    return output;
  }
);
