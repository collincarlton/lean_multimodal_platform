import { z } from 'zod';
import { ai } from './ai';
import { getVaultManifest, resolveVaultFile } from './drive_vault';

export const vaultCatalogTool = ai.defineTool(
  {
    name: 'vaultCatalogTool',
    description: 'Lists all available blueprints, schematics, and technical manuals indexed in the Google One 5 TB Vault.',
    inputSchema: z.object({
      filterKeyword: z.string().optional(),
    }),
    outputSchema: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        mimeType: z.string(),
        sizeBytes: z.number(),
        description: z.string(),
        driveUrl: z.string(),
      })
    ),
  },
  async ({ filterKeyword }) => {
    const catalog = getVaultManifest();
    if (!filterKeyword) return catalog;
    const lower = filterKeyword.toLowerCase();
    return catalog.filter(
      (item) =>
        item.name.toLowerCase().includes(lower) || item.description.toLowerCase().includes(lower)
    );
  }
);

export const vaultResolveTool = ai.defineTool(
  {
    name: 'vaultResolveTool',
    description: 'Resolves metadata for a specific Google Drive asset stored in the 5 TB Vault by URL or File ID.',
    inputSchema: z.object({
      driveUrlOrId: z.string(),
    }),
    outputSchema: z.object({
      found: z.boolean(),
      asset: z
        .object({
          id: z.string(),
          name: z.string(),
          mimeType: z.string(),
          sizeBytes: z.number(),
          description: z.string(),
          driveUrl: z.string(),
        })
        .nullable(),
    }),
  },
  async ({ driveUrlOrId }) => {
    const asset = resolveVaultFile(driveUrlOrId);
    return {
      found: asset !== null,
      asset,
    };
  }
);
