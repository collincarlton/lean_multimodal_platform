import { genkit } from 'genkit';
import { googleAI } from '@genkit-ai/googleai';
import * as dotenv from 'dotenv';
import express from 'express';
import cors from 'cors';
import * as path from 'path';
import * as fs from 'fs';

dotenv.config();

export const ai = genkit({
  plugins: [googleAI()],
});

import {
  multimodalAssistantFlow,
  deepResearchSynthesisFlow,
} from './flows';
export {
  multimodalAssistantFlow,
  deepResearchSynthesisFlow,
};
export { notebookQueryTool, cloudAssetVaultTool } from './tools';
export * from './schemas';

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'HEALTHY', model: 'Gemini 3.8 Flash Frontier Reasoning' });
});

app.post('/api/assistant', async (req, res) => {
  try {
    const result = await multimodalAssistantFlow(req.body);
    res.status(200).json(result);
  } catch (error: any) {
    console.error('Error invoking multimodalAssistantFlow:', error);
    res.status(500).json({ error: error.message || 'Internal Flow Error' });
  }
});

app.post('/api/research/synthesize', async (req, res) => {
  try {
    const result = await deepResearchSynthesisFlow(req.body);
    res.status(200).json(result);
  } catch (error: any) {
    console.error('Error invoking deepResearchSynthesisFlow:', error);
    res.status(500).json({ error: error.message || 'Internal Flow Error' });
  }
});

const webDistPath = path.resolve(__dirname, '../../flutter_client/build/web');
if (fs.existsSync(webDistPath)) {
  app.use(express.static(webDistPath));
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api') || req.path === '/health') return next();
    res.sendFile(path.join(webDistPath, 'index.html'));
  });
}

const PORT = parseInt(process.env.PORT || '5050', 10);
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[GENKIT] Sovereign Unified Platform online on port ${PORT}`);
  });
}

export default app;
