import { z } from 'zod';
import { ai } from './index';

export const notebookQueryTool = ai.defineTool(
  {
    name: 'notebookQueryTool',
    description: 'Searches the grounded NotebookLM research vault and knowledge manifest for domain facts and citations.',
    inputSchema: z.object({
      query: z.string().describe('The search query or concept to look up in the knowledge repository'),
      maxResults: z.number().optional().default(3).describe('Maximum number of knowledge fragments to retrieve'),
    }),
    outputSchema: z.object({
      results: z.array(z.object({
        sourceTitle: z.string(),
        sourceUri: z.string(),
        snippet: z.string(),
        relevanceScore: z.number(),
      })),
    }),
  },
  async (input) => {
    return {
      results: [
        {
          sourceTitle: 'Deep Research Synthesis: Lean Local Client Architecture',
          sourceUri: 'vault://research/lean_local_architecture.md',
          snippet: 'Host hardware is an 8 GB Intel Core i5 iMac running macOS Sequoia. All model execution routes to Google AI Studio frontier models.',
          relevanceScore: 0.98,
        },
        {
          sourceTitle: 'Multimodal Routing Topology & Latency Bounds',
          sourceUri: 'vault://research/multimodal_routing_topology.md',
          snippet: 'Multimodal media streams (audio, image, document) are encoded directly on device and passed upstream to Firebase Genkit Cloud Functions.',
          relevanceScore: 0.92,
        },
      ],
    };
  }
);

export const cloudAssetVaultTool = ai.defineTool(
  {
    name: 'cloudAssetVaultTool',
    description: 'Retrieves metadata, download URIs, and structural descriptions of multimedia assets stored in the Google One / Cloud Storage vault.',
    inputSchema: z.object({
      assetId: z.string().describe('Unique identifier or path of the asset in the vault'),
    }),
    outputSchema: z.object({
      assetId: z.string(),
      fileName: z.string(),
      mimeType: z.string(),
      sizeBytes: z.number(),
      downloadUrl: z.string(),
      tags: z.array(z.string()),
    }),
  },
  async (input) => {
    return {
      assetId: input.assetId,
      fileName: `asset_${input.assetId}.bin`,
      mimeType: 'application/octet-stream',
      sizeBytes: 1048576,
      downloadUrl: `https://storage.googleapis.com/cloud-vault-5tb-prod/${encodeURIComponent(input.assetId)}`,
      tags: ['google-one-vault', 'production-asset', 'multimodal'],
    };
  }
);
