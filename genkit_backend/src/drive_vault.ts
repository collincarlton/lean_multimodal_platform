import fs from 'fs';
import path from 'path';

export interface VaultAsset {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  description: string;
  driveFileId: string;
  driveUrl: string;
}

const MANIFEST_PATH = path.resolve(__dirname, '../../knowledge_vault/vault_manifest.json');

export function getVaultManifest(): VaultAsset[] {
  try {
    if (fs.existsSync(MANIFEST_PATH)) {
      const raw = fs.readFileSync(MANIFEST_PATH, 'utf-8');
      return JSON.parse(raw);
    }
  } catch (err) {
    console.error('[VAULT] Failed to load manifest:', err);
  }
  return [];
}

export function parseDriveUrl(url: string): string | null {
  if (url.includes('/d/')) {
    const afterD = url.split('/d/')[1];
    if (afterD) return afterD.split('/')[0].split('?')[0];
  }
  if (url.includes('id=')) {
    const afterId = url.split('id=')[1];
    if (afterId) return afterId.split('&')[0];
  }
  return null;
}

export function resolveVaultFile(driveUrlOrId: string): VaultAsset | null {
  const manifest = getVaultManifest();
  const fileId = parseDriveUrl(driveUrlOrId) || driveUrlOrId;

  return (
    manifest.find((a) => a.driveFileId === fileId || a.driveUrl === driveUrlOrId || a.name === driveUrlOrId) ||
    null
  );
}
