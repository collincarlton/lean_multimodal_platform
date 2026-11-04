import 'multimodal_payload.dart';

class SessionSummary {
  final String id;
  final DateTime timestamp;
  final String prompt;
  final String summarySnippet;
  final bool hasAudio;
  final bool hasVaultGrounding;
  final String? vaultFileName;
  final int latencyMs;
  final int entityCount;
  final int directiveCount;

  const SessionSummary({
    required this.id,
    required this.timestamp,
    required this.prompt,
    required this.summarySnippet,
    required this.hasAudio,
    required this.hasVaultGrounding,
    this.vaultFileName,
    required this.latencyMs,
    required this.entityCount,
    required this.directiveCount,
  });

  factory SessionSummary.fromJson(Map<String, dynamic> json) {
    return SessionSummary(
      id: json['id'] as String? ?? '',
      timestamp: DateTime.tryParse(json['timestamp'] as String? ?? '') ?? DateTime.now(),
      prompt: json['prompt'] as String? ?? '',
      summarySnippet: json['summarySnippet'] as String? ?? '',
      hasAudio: json['hasAudio'] as bool? ?? false,
      hasVaultGrounding: json['hasVaultGrounding'] as bool? ?? false,
      vaultFileName: json['vaultFileName'] as String?,
      latencyMs: (json['latencyMs'] as num?)?.toInt() ?? 0,
      entityCount: (json['entityCount'] as num?)?.toInt() ?? 0,
      directiveCount: (json['directiveCount'] as num?)?.toInt() ?? 0,
    );
  }
}

class SessionDetail {
  final SessionSummary summary;
  final MultimodalInput input;
  final MultimodalOutput output;

  const SessionDetail({
    required this.summary,
    required this.input,
    required this.output,
  });

  factory SessionDetail.fromJson(Map<String, dynamic> json) {
    return SessionDetail(
      summary: SessionSummary.fromJson(json),
      input: MultimodalInput(
        prompt: json['prompt'] as String? ?? '',
        vaultFileName: json['vaultFileName'] as String?,
      ),
      output: MultimodalOutput.fromJson(json['output'] as Map<String, dynamic>? ?? {}),
    );
  }
}
