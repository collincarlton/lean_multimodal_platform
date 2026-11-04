import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/multimodal_payload.dart';

class ReasoningView extends StatelessWidget {
  final MultimodalOutput? output;
  final bool isLoading;
  final String? errorMessage;

  const ReasoningView({
    super.key,
    required this.output,
    required this.isLoading,
    this.errorMessage,
  });

  Color _priorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'CRITICAL':
        return const Color(0xFFFF3366);
      case 'HIGH':
        return const Color(0xFFFF9900);
      case 'MEDIUM':
        return const Color(0xFF00D9F5);
      default:
        return const Color(0xFF64748B);
    }
  }

  void _copyJsonExport(BuildContext context) {
    if (output == null) return;
    final jsonStr =
        const JsonEncoder.withIndent('  ').convert(output!.toJson());
    Clipboard.setData(ClipboardData(text: jsonStr));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Row(
          children: [
            Icon(Icons.check_circle_rounded,
                color: Color(0xFF00F5A0), size: 18),
            SizedBox(width: 8),
            Text('Session Telemetry copied to Clipboard as JSON',
                style: TextStyle(fontSize: 12)),
          ],
        ),
        backgroundColor: Color(0xFF0F172A),
        behavior: SnackBarBehavior.floating,
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00F5A0)),
            ),
            const SizedBox(height: 16),
            Text(
              'Multimodal Cloud Reasoning Active...',
              style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
            ),
            const SizedBox(height: 4),
            const Text(
              'Grounded in Google One 5 TB Vault & Frontier Audio Pipeline',
              style: TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 11,
                  fontFamily: 'monospace'),
            ),
          ],
        ),
      );
    }

    if (errorMessage != null) {
      return Center(
        child: Container(
          padding: const EdgeInsets.all(16),
          constraints: const BoxConstraints(maxWidth: 480),
          decoration: BoxDecoration(
            color: const Color(0xFF1A1117),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: const Color(0xFFFF3366).withValues(alpha: 0.4)),
          ),
          child: Row(
            children: [
              const Icon(Icons.error_outline_rounded,
                  color: Color(0xFFFF3366), size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  errorMessage!,
                  style:
                      const TextStyle(color: Color(0xFFFF99AA), fontSize: 13),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (output == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.all_inclusive_rounded,
                size: 48, color: Colors.grey.shade800),
            const SizedBox(height: 12),
            Text(
              'Sovereign Multimodal Gateway Ready',
              style: TextStyle(
                  color: Colors.grey.shade500,
                  fontSize: 14,
                  fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 4),
            Text(
              'Select a session from the history browser or compose a new diagnostic inquiry.',
              style: TextStyle(color: Colors.grey.shade700, fontSize: 12),
            ),
          ],
        ),
      );
    }

    final res = output!;
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                'DIAGNOSTIC SYNTHESIS',
                style: TextStyle(
                  color: Color(0xFF00F5A0),
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                ),
              ),
              const Spacer(),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1E293B),
                  foregroundColor: const Color(0xFF00F5A0),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  minimumSize: const Size(0, 26),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(6)),
                ),
                icon: const Icon(Icons.file_download_outlined, size: 14),
                label: const Text('Export JSON',
                    style:
                        TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                onPressed: () => _copyJsonExport(context),
              ),
              const SizedBox(width: 8),
              if (res.latencyMs > 0)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '${res.latencyMs} ms',
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF131B2A),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF1E293B)),
            ),
            child: Text(
              res.summary,
              style: const TextStyle(
                  color: Color(0xFFF1F5F9), fontSize: 14, height: 1.5),
            ),
          ),
          if (res.vaultGrounding != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF0B2138),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                    color: const Color(0xFF00D9F5).withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.cloud_done_rounded,
                      color: Color(0xFF00D9F5), size: 18),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Grounded in 5 TB Vault: ${res.vaultGrounding!.fileName}',
                          style: const TextStyle(
                              color: Color(0xFFF1F5F9),
                              fontSize: 12,
                              fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Direct Cloud Stream • 0 Bytes Written to Local Fusion Drive',
                          style: TextStyle(
                              color: Colors.cyan.shade200, fontSize: 10),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (res.acousticAnalysis != null) ...[
            const SizedBox(height: 20),
            const Text(
              'ACOUSTIC & VOICE TELEMETRY',
              style: TextStyle(
                color: Color(0xFF00D9F5),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1C2E),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: const Color(0xFF00D9F5).withValues(alpha: 0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (res.acousticAnalysis!.transcript.isNotEmpty) ...[
                    const Text('Spoken Transcript:',
                        style:
                            TextStyle(color: Color(0xFF64748B), fontSize: 11)),
                    const SizedBox(height: 4),
                    Text(
                      '"${res.acousticAnalysis!.transcript}"',
                      style: const TextStyle(
                          color: Color(0xFFE2E8F0),
                          fontSize: 13,
                          fontStyle: FontStyle.italic),
                    ),
                    const SizedBox(height: 12),
                  ],
                  if (res
                      .acousticAnalysis!.audioCharacteristics.isNotEmpty) ...[
                    const Text('Acoustic Spectrum & Tone:',
                        style:
                            TextStyle(color: Color(0xFF64748B), fontSize: 11)),
                    const SizedBox(height: 4),
                    Text(
                      res.acousticAnalysis!.audioCharacteristics,
                      style: const TextStyle(
                          color: Color(0xFFCBD5E1), fontSize: 13),
                    ),
                    const SizedBox(height: 12),
                  ],
                  if (res.acousticAnalysis!.detectedAnomalies.isNotEmpty) ...[
                    const Text('Detected Anomalies:',
                        style:
                            TextStyle(color: Color(0xFF64748B), fontSize: 11)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children:
                          res.acousticAnalysis!.detectedAnomalies.map((anom) {
                        return Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color:
                                const Color(0xFFFF3366).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                                color: const Color(0xFFFF3366)
                                    .withValues(alpha: 0.4)),
                          ),
                          child: Text(
                            anom,
                            style: const TextStyle(
                                color: Color(0xFFFF99AA),
                                fontSize: 11,
                                fontWeight: FontWeight.bold),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ],
              ),
            ),
          ],
          if (res.actionDirectives.isNotEmpty) ...[
            const SizedBox(height: 20),
            const Text(
              'ACTION DIRECTIVES',
              style: TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            ...res.actionDirectives.map((directive) {
              final color = _priorityColor(directive.priority);
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFF131B2A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: color.withValues(alpha: 0.35)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        directive.priority,
                        style: TextStyle(
                            color: color,
                            fontSize: 10,
                            fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        directive.instruction,
                        style: const TextStyle(
                            color: Color(0xFFF1F5F9), fontSize: 13),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
          if (res.entities.isNotEmpty) ...[
            const SizedBox(height: 20),
            const Text(
              'IDENTIFIED ENTITIES & TELEMETRY BADGES',
              style: TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: res.entities.map((entity) {
                return Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A2234),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF334155)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        entity.name,
                        style: const TextStyle(
                            color: Color(0xFFF8FAFC),
                            fontSize: 12,
                            fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '(${entity.category})',
                        style: const TextStyle(
                            color: Color(0xFF64748B), fontSize: 10),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '${(entity.confidence * 100).toInt()}%',
                        style: const TextStyle(
                          color: Color(0xFF00F5A0),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
          if (res.reasoningSteps.isNotEmpty) ...[
            const SizedBox(height: 20),
            const Text(
              'MULTI-TURN REASONING CHAIN',
              style: TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF0B101B),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1E293B)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: res.reasoningSteps.asMap().entries.map((entry) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${entry.key + 1}. ',
                          style: const TextStyle(
                            color: Color(0xFF00F5A0),
                            fontSize: 12,
                            fontFamily: 'monospace',
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Expanded(
                          child: Text(
                            entry.value,
                            style: const TextStyle(
                                color: Color(0xFF94A3B8),
                                fontSize: 12,
                                height: 1.4),
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
