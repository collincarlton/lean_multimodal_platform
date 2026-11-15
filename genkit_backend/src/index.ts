import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import path from 'path';
import dotenv from 'dotenv';
import { getVaultManifest, resolveVaultFile } from './drive_vault';
import {
  saveSession,
  listSessions,
  getSession,
  deleteSession,
  clearHistory,
} from './history_service';

dotenv.config({ path: path.resolve(__dirname, '../.env') });

import { ai } from './ai';
export { ai };

import {
  executeMultimodalReasoning,
  getModelPriority,
  normalizeRawInput,
} from './flows';
import { SlidingWindowRpmLimiter } from './rate_limiter';
import './tools';

const app = express();
const PORT = process.env.PORT || 5050;
const HOST = process.env.HOST || '127.0.0.1';
const LOOPBACK_ORIGIN_RE = /^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:\d+)?$/i;
const rpmLimiter = new SlidingWindowRpmLimiter(
  Number(process.env.MAX_RPM || 15),
  60_000
);

function enforceLoopbackCors(req: Request, res: Response, next: NextFunction): void {
  const origin = req.headers.origin;
  if (origin && !LOOPBACK_ORIGIN_RE.test(origin)) {
    res.status(403).json({
      error: 'CORS policy: non-loopback origin rejected.',
    });
    return;
  }
  next();
}

function enforceRpmLimit(req: Request, res: Response, next: NextFunction): void {
  const decision = rpmLimiter.tryAcquire();
  res.setHeader('X-RateLimit-Limit', String(decision.limit));
  res.setHeader('X-RateLimit-Remaining', String(decision.remaining));
  if (!decision.allowed) {
    res.setHeader('Retry-After', String(decision.retryAfterSeconds));
    res.status(429).json({
      error: `FinOps RPM ceiling (${decision.limit} RPM) reached. Retry after ${decision.retryAfterSeconds}s.`,
      retryAfterSeconds: decision.retryAfterSeconds,
    });
    return;
  }
  next();
}

app.use(enforceLoopbackCors);
app.use(
  cors({
    origin(origin, callback) {
      if (!origin || LOOPBACK_ORIGIN_RE.test(origin)) {
        callback(null, true);
        return;
      }
      callback(null, false);
    },
  })
);
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

const webBuildPath = path.resolve(__dirname, '../../flutter_client/build/web');
app.use(express.static(webBuildPath));

app.get('/api/health', (_req, res) => {
  const mem = process.memoryUsage();
  const models = getModelPriority();
  res.json({
    status: 'ONLINE',
    mode: 'ZERO_COST_SOVEREIGN',
    activeModel: models[0],
    fallbackModels: models.slice(1),
    rpmRemaining: rpmLimiter.peekRemaining(),
    uptimeSeconds: Math.floor(process.uptime()),
    memoryRssMb: (mem.rss / 1024 / 1024).toFixed(2),
    heapUsedMb: (mem.heapUsed / 1024 / 1024).toFixed(2),
    port: PORT,
  });
});

app.get('/healthz', (_req, res) => {
  const models = getModelPriority();
  res.status(200).json({
    status: 'ok',
    activeModel: models[0],
    rpmRemaining: rpmLimiter.peekRemaining(),
    port: PORT,
  });
});

// Vault Catalog Endpoints
app.get('/api/vault/manifest', (_req, res) => {
  try {
    const catalog = getVaultManifest();
    res.json({
      status: 'OK',
      source: 'Google One (5 TB Vault)',
      count: catalog.length,
      assets: catalog,
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/vault/resolve', (req, res) => {
  const { driveUrlOrId } = req.body;
  if (!driveUrlOrId) {
    res.status(400).json({ error: 'driveUrlOrId required' });
    return;
  }
  const asset = resolveVaultFile(driveUrlOrId);
  res.json({ found: asset !== null, asset });
});

// Session History Endpoints
app.get('/api/history', (_req, res) => {
  try {
    const sessions = listSessions();
    res.json({ status: 'OK', count: sessions.length, sessions });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/history/:id', (req, res) => {
  const detail = getSession(req.params.id);
  if (!detail) {
    res.status(404).json({ error: 'Session not found' });
    return;
  }
  res.json(detail);
});

app.delete('/api/history/:id', (req, res) => {
  const deleted = deleteSession(req.params.id);
  res.json({ success: deleted });
});

app.delete('/api/history', (_req, res) => {
  clearHistory();
  res.json({ success: true });
});

// Reasoning API (with Auto-Persistence & FinOps RPM Governor)
app.post('/api/reason', enforceRpmLimit, async (req, res) => {
  const start = Date.now();
  try {
    const normalizedInput = normalizeRawInput(req.body);
    const output = await executeMultimodalReasoning(normalizedInput);
    const latencyMs = Date.now() - start;

    // Automatically persist to zero-overhead local JSON vault
    const saved = saveSession(normalizedInput, output, latencyMs);

    res.json({
      ...output,
      sessionId: saved.id,
      latencyMs,
    });
  } catch (err: any) {
    console.error('[API REASONING FAULT]', err);
    res.status(500).json({
      error: err.message || 'Internal reasoning pipeline exception',
      timestamp: new Date().toISOString(),
    });
  }
});

// Gateway SSE Streaming API matching Dart GenkitGatewayClient contract
app.post('/gateway/stream', enforceRpmLimit, async (req, res) => {
  const start = Date.now();
  try {
    const normalizedInput = normalizeRawInput(req.body);
    const output = await executeMultimodalReasoning(normalizedInput);
    const latencyMs = Date.now() - start;
    const saved = saveSession(normalizedInput, output, latencyMs);

    res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders?.();

    const contentFrame = {
      content: output.summary,
      done: false,
      metadata: {
        sessionId: saved.id,
        latencyMs,
        model: getModelPriority()[0],
        sentiment: output.sentiment,
        confidenceScore: output.confidenceScore,
        entities: output.entities,
        actionDirectives: output.actionDirectives,
        reasoningSteps: output.reasoningSteps,
        vaultGrounding: output.vaultGrounding,
        acousticAnalysis: output.acousticAnalysis,
      },
    };
    const finalFrame = {
      content: '',
      done: true,
      metadata: {
        sessionId: saved.id,
        latencyMs,
        model: getModelPriority()[0],
      },
    };

    res.write(`data: ${JSON.stringify(contentFrame)}\n\n`);
    res.write(`data: ${JSON.stringify(finalFrame)}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  } catch (err: any) {
    console.error('[GATEWAY STREAM FAULT]', err);
    if (!res.headersSent) {
      res.status(500).json({
        error: err.message || 'Gateway stream pipeline exception',
        timestamp: new Date().toISOString(),
      });
    } else {
      res.write(
        `data: ${JSON.stringify({ content: `GATEWAY_ERROR: ${err.message || 'unknown'}`, done: true })}\n\n`
      );
      res.write('data: [DONE]\n\n');
      res.end();
    }
  }
});

app.get('*', (_req, res) => {
  const indexPath = path.join(webBuildPath, 'index.html');
  res.sendFile(indexPath, (err) => {
    if (err) {
      res.status(404).send('Compiled Flutter Web release bundle not found on host.');
    }
  });
});

app.listen(Number(PORT), HOST, () => {
  console.log(`[SOVEREIGN GATEWAY] Daemon operational at http://${HOST}:${PORT}`);
  console.log(`[STATIC ASSETS] Serving bundle from ${webBuildPath}`);
});
