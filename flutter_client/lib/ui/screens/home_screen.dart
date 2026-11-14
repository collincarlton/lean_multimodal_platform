import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/multimodal_payload.dart' hide EntityBadge;
import '../../providers/assistant_provider.dart';
import '../widgets/action_card.dart';
import '../widgets/entity_badge.dart';
import '../widgets/grounding_chip.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _promptController = TextEditingController();
  bool _showRawJson = false;

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  void _applyPreset(String text) {
    _promptController.text = text;
  }

  Color _sentimentColor(String sentiment) {
    switch (sentiment.toUpperCase()) {
      case 'POSITIVE':
        return Colors.greenAccent;
      case 'NEGATIVE':
        return Colors.redAccent;
      case 'MIXED':
        return Colors.amberAccent;
      default:
        return Colors.blueGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AssistantProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        title: Row(
          children: [
            const Icon(Icons.hub_outlined, color: Colors.cyanAccent, size: 20),
            const SizedBox(width: 8),
            const Text(
              'LEAN MULTIMODAL PLATFORM',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: provider.backendHealthy
                    ? Colors.greenAccent.withValues(alpha: 0.15)
                    : Colors.redAccent.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: provider.backendHealthy
                      ? Colors.greenAccent.withValues(alpha: 0.4)
                      : Colors.redAccent.withValues(alpha: 0.4),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.circle,
                    size: 8,
                    color: provider.backendHealthy
                        ? Colors.greenAccent
                        : Colors.redAccent,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    provider.backendHealthy ? 'GENKIT CONNECTED' : 'BACKEND OFFLINE',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: provider.backendHealthy
                          ? Colors.greenAccent
                          : Colors.redAccent,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            IconButton(
              icon: const Icon(Icons.refresh, size: 18),
              tooltip: 'New Session',
              onPressed: () => provider.resetSession(),
            ),
          ],
        ),
      ),
      body: Row(
        children: [
          SizedBox(
            width: 380,
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                border: Border(
                  right: BorderSide(color: Colors.white.withValues(alpha: 0.06)),
                ),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'MULTIMODAL PROMPT COMPOSER',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Colors.white54,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      ActionChip(
                        label: const Text('Host Audit', style: TextStyle(fontSize: 11)),
                        backgroundColor: const Color(0xFF21262D),
                        onPressed: () => _applyPreset('Audit host system metrics: CPU 82%, Memory 7.4 GB DDR4, Swap active on Fusion Drive.'),
                      ),
                      ActionChip(
                        label: const Text('Vault Query', style: TextStyle(fontSize: 11)),
                        backgroundColor: const Color(0xFF21262D),
                        onPressed: () => _applyPreset('Query NotebookLM research vault for edge latency benchmarks and architectural specs.'),
                      ),
                      ActionChip(
                        label: const Text('Asset Lookup', style: TextStyle(fontSize: 11)),
                        backgroundColor: const Color(0xFF21262D),
                        onPressed: () => _applyPreset('Locate and resolve asset descriptor for blueprint schematic_v2.pdf in Google One vault.'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: TextField(
                      controller: _promptController,
                      maxLines: null,
                      expands: true,
                      textAlignVertical: TextAlignVertical.top,
                      style: const TextStyle(fontSize: 13, color: Colors.white),
                      decoration: InputDecoration(
                        hintText: 'Enter multimodal instruction or request...',
                        hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3)),
                        filled: true,
                        fillColor: const Color(0xFF0D1117),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Colors.cyanAccent),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (provider.stagedMedia.isNotEmpty) ...[
                    Text(
                      'ATTACHMENTS (${provider.stagedMedia.length})',
                      style: const TextStyle(fontSize: 10, color: Colors.white54, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 48,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: provider.stagedMedia.length,
                        itemBuilder: (context, idx) {
                          final m = provider.stagedMedia[idx];
                          return Container(
                            margin: const EdgeInsets.only(right: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 8),
                            decoration: BoxDecoration(
                              color: const Color(0xFF21262D),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.attachment, size: 14, color: Colors.cyanAccent),
                                const SizedBox(width: 4),
                                Text(m.fileName, style: const TextStyle(fontSize: 11)),
                                IconButton(
                                  icon: const Icon(Icons.close, size: 12),
                                  onPressed: () => provider.removeMediaAttachment(idx),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 10),
                  ],
                  Row(
                    children: [
                      const Text('Temperature', style: TextStyle(fontSize: 11, color: Colors.white60)),
                      const Spacer(),
                      Text(provider.temperature.toStringAsFixed(2), style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                    ],
                  ),
                  Slider(
                    value: provider.temperature,
                    min: 0.0,
                    max: 1.0,
                    divisions: 10,
                    activeColor: Colors.cyanAccent,
                    onChanged: (v) => provider.setTemperature(v),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    height: 42,
                    child: ElevatedButton.icon(
                      onPressed: provider.isLoading
                          ? null
                          : () {
                              provider.sendPrompt(_promptController.text);
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.cyanAccent.shade700,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      ),
                      icon: provider.isLoading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.send_rounded, size: 16),
                      label: Text(
                        provider.isLoading ? 'STREAMING...' : 'DISPATCH TO GENKIT',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Expanded(
            child: Container(
              color: const Color(0xFF0D1117),
              padding: const EdgeInsets.all(20),
              child: provider.errorMessage != null
                  ? Center(
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.redAccent.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.redAccent.withValues(alpha: 0.3)),
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.error_outline, color: Colors.redAccent, size: 36),
                            const SizedBox(height: 12),
                            Text(
                              provider.errorMessage!,
                              style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    )
                  : provider.currentOutput == null
                      ? _buildEmptyState()
                      : _buildOutputView(provider.currentOutput!),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.terminal_outlined, size: 54, color: Colors.white.withValues(alpha: 0.1)),
          const SizedBox(height: 16),
          const Text(
            'AWAITING MULTIMODAL INSTRUCTION',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Colors.white38,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Lean Local Client (8 GB RAM Host) -> Firebase Genkit -> Gemini 2.0 Flash (2M Context)',
            style: TextStyle(fontSize: 12, color: Colors.white24),
          ),
        ],
      ),
    );
  }

  Widget _buildOutputView(MultimodalOutput output) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: _sentimentColor(output.sentiment ?? 'NEUTRAL').withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: _sentimentColor(output.sentiment ?? 'NEUTRAL').withValues(alpha: 0.4)),
                      ),
                      child: Text(
                        output.sentiment ?? 'NEUTRAL',
                        style: TextStyle(
                          color: _sentimentColor(output.sentiment ?? 'NEUTRAL'),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Confidence: ${((output.confidenceScore ?? 1.0) * 100).toInt()}%',
                      style: const TextStyle(fontSize: 11, color: Colors.white60, fontFamily: 'monospace'),
                    ),
                    const Spacer(),
                    Consumer<AssistantProvider>(
                      builder: (context, provider, _) => Text(
                        'Session: ${provider.sessionId.length >= 8 ? provider.sessionId.substring(0, 8) : provider.sessionId}...',
                        style: const TextStyle(fontSize: 11, color: Colors.white38, fontFamily: 'monospace'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: Icon(
                        _showRawJson ? Icons.code_off : Icons.code,
                        size: 16,
                        color: Colors.white54,
                      ),
                      tooltip: 'Toggle Raw JSON',
                      onPressed: () => setState(() => _showRawJson = !_showRawJson),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  output.summary,
                  style: const TextStyle(fontSize: 14, height: 1.5, color: Colors.white),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_showRawJson) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.3)),
              ),
              child: Text(
                const JsonEncoder.withIndent('  ').convert(output.toJson()),
                style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: Colors.cyanAccent),
              ),
            ),
            const SizedBox(height: 16),
          ],
          if (output.entities.isNotEmpty) ...[
            const Text(
              'RESOLVED ENTITIES',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white54, letterSpacing: 1),
            ),
            const SizedBox(height: 8),
            Wrap(
              children: output.entities.map((e) => EntityBadge(entity: e)).toList(),
            ),
            const SizedBox(height: 16),
          ],
          if (output.actionDirectives.isNotEmpty) ...[
            const Text(
              'RECOMMENDED ACTION DIRECTIVES',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white54, letterSpacing: 1),
            ),
            const SizedBox(height: 8),
            Column(
              children: output.actionDirectives.map((a) => ActionCard(action: a)).toList(),
            ),
            const SizedBox(height: 16),
          ],
          if (output.vaultGrounding != null) ...[
            const Text(
              'GROUNDING CITATIONS & KNOWLEDGE VAULT',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white54, letterSpacing: 1),
            ),
            const SizedBox(height: 8),
            GroundingChip(source: output.vaultGrounding!),
          ],
        ],
      ),
    );
  }
}
