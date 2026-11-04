import fs from 'fs';
import path from 'path';
import { MultimodalReasoningInput, MultimodalReasoningOutput } from './flows';

export interface HistorySessionSummary {
  id: string;
  timestamp: string;
  prompt: string;
  summarySnippet: string;
  hasAudio: boolean;
  hasVaultGrounding: boolean;
  vaultFileName?: string;
  latencyMs: number;
  entityCount: number;
  directiveCount: number;
}

export interface HistorySessionDetail extends HistorySessionSummary {
  input: MultimodalReasoningInput;
  output: MultimodalReasoningOutput;
}

const HISTORY_DIR = path.resolve(__dirname, '../../knowledge_vault/history');
const MAX_SESSIONS = 100;

function ensureHistoryDir(): void {
  if (!fs.existsSync(HISTORY_DIR)) {
    fs.mkdirSync(HISTORY_DIR, { recursive: true });
  }
}

export function saveSession(
  input: MultimodalReasoningInput,
  output: MultimodalReasoningOutput,
  latencyMs: number
): HistorySessionSummary {
  ensureHistoryDir();

  const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  const timestamp = new Date().toISOString();
  const summarySnippet = output.summary.length > 120
    ? output.summary.substring(0, 117) + '...'
    : output.summary;

  const summary: HistorySessionSummary = {
    id,
    timestamp,
    prompt: input.prompt,
    summarySnippet,
    hasAudio: !!input.audioBase64,
    hasVaultGrounding: !!output.vaultGrounding,
    vaultFileName: output.vaultGrounding?.fileName || input.vaultFileName,
    latencyMs,
    entityCount: output.entities.length,
    directiveCount: output.actionDirectives.length,
  };

  const detail: HistorySessionDetail = {
    ...summary,
    input,
    output,
  };

  const filePath = path.join(HISTORY_DIR, `${id}.json`);
  fs.writeFileSync(filePath, JSON.stringify(detail, null, 2), 'utf-8');

  // Enforce FIFO ceiling (prune sessions older than MAX_SESSIONS)
  pruneHistory();

  return summary;
}

export function listSessions(): HistorySessionSummary[] {
  ensureHistoryDir();
  const files = fs.readdirSync(HISTORY_DIR).filter((f) => f.endsWith('.json'));

  const summaries: HistorySessionSummary[] = [];
  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(HISTORY_DIR, file), 'utf-8');
      const detail = JSON.parse(content) as HistorySessionDetail;
      summaries.push({
        id: detail.id,
        timestamp: detail.timestamp,
        prompt: detail.prompt,
        summarySnippet: detail.summarySnippet,
        hasAudio: detail.hasAudio,
        hasVaultGrounding: detail.hasVaultGrounding,
        vaultFileName: detail.vaultFileName,
        latencyMs: detail.latencyMs,
        entityCount: detail.entityCount,
        directiveCount: detail.directiveCount,
      });
    } catch {
      // Ignore corrupt session files
    }
  }

  // Sort descending by timestamp
  return summaries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export function getSession(id: string): HistorySessionDetail | null {
  ensureHistoryDir();
  const filePath = path.join(HISTORY_DIR, `${id}.json`);
  if (!fs.existsSync(filePath)) return null;

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content) as HistorySessionDetail;
  } catch {
    return null;
  }
}

export function deleteSession(id: string): boolean {
  ensureHistoryDir();
  const filePath = path.join(HISTORY_DIR, `${id}.json`);
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
    return true;
  }
  return false;
}

export function clearHistory(): void {
  ensureHistoryDir();
  const files = fs.readdirSync(HISTORY_DIR).filter((f) => f.endsWith('.json'));
  for (const file of files) {
    fs.unlinkSync(path.join(HISTORY_DIR, file));
  }
}

function pruneHistory(): void {
  try {
    const files = fs.readdirSync(HISTORY_DIR).filter((f) => f.endsWith('.json'));
    if (files.length <= MAX_SESSIONS) return;

    const fileStats = files.map((file) => ({
      file,
      mtime: fs.statSync(path.join(HISTORY_DIR, file)).mtimeMs,
    }));

    fileStats.sort((a, b) => a.mtime - b.mtime);
    const toRemove = fileStats.slice(0, files.length - MAX_SESSIONS);
    for (const item of toRemove) {
      fs.unlinkSync(path.join(HISTORY_DIR, item.file));
    }
  } catch (err) {
    console.error('[HISTORY] Pruning error:', err);
  }
}
