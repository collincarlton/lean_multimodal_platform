class MultimodalInput {
  final String prompt;
  final String? imageBase64;
  final String? imageMimeType;
  final String? audioBase64;
  final String? audioMimeType;
  final int? audioDurationMs;
  final String? driveFileUrl;
  final String? driveFileId;
  final String? vaultFileName;

  const MultimodalInput({
    required this.prompt,
    this.imageBase64,
    this.imageMimeType,
    this.audioBase64,
    this.audioMimeType,
    this.audioDurationMs,
    this.driveFileUrl,
    this.driveFileId,
    this.vaultFileName,
  });

  Map<String, dynamic> toJson() => {
    'prompt': prompt,
    if (imageBase64 != null) 'imageBase64': imageBase64,
    if (imageMimeType != null) 'imageMimeType': imageMimeType,
    if (audioBase64 != null) 'audioBase64': audioBase64,
    if (audioMimeType != null) 'audioMimeType': audioMimeType,
    if (audioDurationMs != null) 'audioDurationMs': audioDurationMs,
    if (driveFileUrl != null) 'driveFileUrl': driveFileUrl,
    if (driveFileId != null) 'driveFileId': driveFileId,
    if (vaultFileName != null) 'vaultFileName': vaultFileName,
  };
}

class VaultAsset {
  final String id;
  final String name;
  final String mimeType;
  final int sizeBytes;
  final String description;
  final String driveFileId;
  final String driveUrl;

  const VaultAsset({
    required this.id,
    required this.name,
    required this.mimeType,
    required this.sizeBytes,
    required this.description,
    required this.driveFileId,
    required this.driveUrl,
  });

  factory VaultAsset.fromJson(Map<String, dynamic> json) {
    return VaultAsset(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? 'Untitled Asset',
      mimeType: json['mimeType'] as String? ?? 'application/octet-stream',
      sizeBytes: (json['sizeBytes'] as num?)?.toInt() ?? 0,
      description: json['description'] as String? ?? '',
      driveFileId: json['driveFileId'] as String? ?? '',
      driveUrl: json['driveUrl'] as String? ?? '',
    );
  }
}

class VaultGroundingRef {
  final String fileName;
  final String driveUrl;
  final String mimeType;
  final int sizeBytes;
  final String status;

  const VaultGroundingRef({
    required this.fileName,
    required this.driveUrl,
    required this.mimeType,
    required this.sizeBytes,
    required this.status,
  });

  factory VaultGroundingRef.fromJson(Map<String, dynamic> json) {
    return VaultGroundingRef(
      fileName: json['fileName'] as String? ?? 'Cloud Asset',
      driveUrl: json['driveUrl'] as String? ?? '',
      mimeType: json['mimeType'] as String? ?? '',
      sizeBytes: (json['sizeBytes'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? 'GROUNDED_ZERO_LOCAL_IO',
    );
  }

  Map<String, dynamic> toJson() => {
    'fileName': fileName,
    'driveUrl': driveUrl,
    'mimeType': mimeType,
    'sizeBytes': sizeBytes,
    'status': status,
  };
}

class AcousticAnalysis {
  final String transcript;
  final String audioCharacteristics;
  final List<String> detectedAnomalies;

  const AcousticAnalysis({
    this.transcript = '',
    this.audioCharacteristics = '',
    this.detectedAnomalies = const [],
  });

  factory AcousticAnalysis.fromJson(Map<String, dynamic> json) {
    return AcousticAnalysis(
      transcript: json['transcript'] as String? ?? '',
      audioCharacteristics: json['audioCharacteristics'] as String? ?? '',
      detectedAnomalies: (json['detectedAnomalies'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() => {
    'transcript': transcript,
    'audioCharacteristics': audioCharacteristics,
    'detectedAnomalies': detectedAnomalies,
  };
}

class EntityBadge {
  final String name;
  final String category;
  final double confidence;

  const EntityBadge({
    required this.name,
    required this.category,
    required this.confidence,
  });

  factory EntityBadge.fromJson(Map<String, dynamic> json) {
    return EntityBadge(
      name: json['name'] as String? ?? 'Unknown',
      category: json['category'] as String? ?? 'General',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'category': category,
    'confidence': confidence,
  };
}

class ActionDirective {
  final String priority;
  final String instruction;

  const ActionDirective({
    required this.priority,
    required this.instruction,
  });

  factory ActionDirective.fromJson(Map<String, dynamic> json) {
    return ActionDirective(
      priority: json['priority'] as String? ?? 'MEDIUM',
      instruction: json['instruction'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'priority': priority,
    'instruction': instruction,
  };
}

class MultimodalOutput {
  final String summary;
  final String? sentiment;
  final double? confidenceScore;
  final AcousticAnalysis? acousticAnalysis;
  final VaultGroundingRef? vaultGrounding;
  final List<EntityBadge> entities;
  final List<ActionDirective> actionDirectives;
  final List<String> reasoningSteps;
  final int latencyMs;

  const MultimodalOutput({
    required this.summary,
    this.sentiment,
    this.confidenceScore,
    this.acousticAnalysis,
    this.vaultGrounding,
    this.entities = const [],
    this.actionDirectives = const [],
    this.reasoningSteps = const [],
    this.latencyMs = 0,
  });

  factory MultimodalOutput.fromJson(Map<String, dynamic> json) {
    return MultimodalOutput(
      summary: json['summary'] as String? ?? 'No reasoning summary provided.',
      sentiment: json['sentiment'] as String? ?? 'NEUTRAL',
      confidenceScore: (json['confidenceScore'] as num?)?.toDouble() ?? 0.9,
      acousticAnalysis: json['acousticAnalysis'] != null
          ? AcousticAnalysis.fromJson(
              json['acousticAnalysis'] as Map<String, dynamic>)
          : null,
      vaultGrounding: json['vaultGrounding'] != null
          ? VaultGroundingRef.fromJson(
              json['vaultGrounding'] as Map<String, dynamic>)
          : null,
      entities: (json['entities'] as List<dynamic>?)
              ?.map((e) => EntityBadge.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      actionDirectives: (json['actionDirectives'] as List<dynamic>?)
              ?.map((e) => ActionDirective.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      reasoningSteps: (json['reasoningSteps'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      latencyMs: (json['latencyMs'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'summary': summary,
    if (sentiment != null) 'sentiment': sentiment,
    if (confidenceScore != null) 'confidenceScore': confidenceScore,
    if (acousticAnalysis != null) 'acousticAnalysis': acousticAnalysis!.toJson(),
    if (vaultGrounding != null) 'vaultGrounding': vaultGrounding!.toJson(),
    'entities': entities.map((e) => e.toJson()).toList(),
    'actionDirectives': actionDirectives.map((e) => e.toJson()).toList(),
    'reasoningSteps': reasoningSteps,
    'latencyMs': latencyMs,
  };
}

class MediaAttachment {
  final String fileName;
  final String mimeType;
  final String? base64Data;
  final int? sizeBytes;

  const MediaAttachment({
    required this.fileName,
    required this.mimeType,
    this.base64Data,
    this.sizeBytes,
  });
}
