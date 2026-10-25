class EntityItem {
  final String name;
  final String category;
  final double confidence;

  const EntityItem({
    required this.name,
    required this.category,
    required this.confidence,
  });

  factory EntityItem.fromJson(Map<String, dynamic> json) {
    return EntityItem(
      name: json['name'] as String? ?? 'UNKNOWN',
      category: json['category'] as String? ?? 'GENERAL',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'category': category,
    'confidence': confidence,
  };
}

class ActionItem {
  final String actionType;
  final String target;
  final Map<String, dynamic> parameters;

  const ActionItem({
    required this.actionType,
    required this.target,
    required this.parameters,
  });

  factory ActionItem.fromJson(Map<String, dynamic> json) {
    return ActionItem(
      actionType: json['actionType'] as String? ?? 'NONE',
      target: json['target'] as String? ?? '',
      parameters: json['parameters'] != null
          ? Map<String, dynamic>.from(json['parameters'] as Map)
          : <String, dynamic>{},
    );
  }

  Map<String, dynamic> toJson() => {
    'actionType': actionType,
    'target': target,
    'parameters': parameters,
  };
}

class GroundingSourceItem {
  final String title;
  final String uri;
  final double relevance;

  const GroundingSourceItem({
    required this.title,
    required this.uri,
    required this.relevance,
  });

  factory GroundingSourceItem.fromJson(Map<String, dynamic> json) {
    return GroundingSourceItem(
      title: json['title'] as String? ?? 'Untitled Source',
      uri: json['uri'] as String? ?? '',
      relevance: (json['relevance'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'title': title,
    'uri': uri,
    'relevance': relevance,
  };
}

class MultimodalOutput {
  final String sessionId;
  final String summary;
  final String sentiment;
  final List<EntityItem> entities;
  final List<ActionItem> actions;
  final double confidenceScore;
  final List<GroundingSourceItem> groundingSources;

  const MultimodalOutput({
    required this.sessionId,
    required this.summary,
    required this.sentiment,
    required this.entities,
    required this.actions,
    required this.confidenceScore,
    required this.groundingSources,
  });

  factory MultimodalOutput.fromJson(Map<String, dynamic> json) {
    return MultimodalOutput(
      sessionId: json['sessionId'] as String? ?? '',
      summary: json['summary'] as String? ?? '',
      sentiment: json['sentiment'] as String? ?? 'NEUTRAL',
      entities: (json['entities'] as List<dynamic>?)
              ?.map((e) => EntityItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const <EntityItem>[],
      actions: (json['actions'] as List<dynamic>?)
              ?.map((a) => ActionItem.fromJson(a as Map<String, dynamic>))
              .toList() ??
          const <ActionItem>[],
      confidenceScore: (json['confidenceScore'] as num?)?.toDouble() ?? 0.0,
      groundingSources: (json['groundingSources'] as List<dynamic>?)
              ?.map((g) =>
                  GroundingSourceItem.fromJson(g as Map<String, dynamic>))
              .toList() ??
          const <GroundingSourceItem>[],
    );
  }

  Map<String, dynamic> toJson() => {
    'sessionId': sessionId,
    'summary': summary,
    'sentiment': sentiment,
    'entities': entities.map((e) => e.toJson()).toList(),
    'actions': actions.map((a) => a.toJson()).toList(),
    'confidenceScore': confidenceScore,
    'groundingSources': groundingSources.map((g) => g.toJson()).toList(),
  };
}

class MediaAttachment {
  final String url;
  final String contentType;
  final String fileName;

  const MediaAttachment({
    required this.url,
    required this.contentType,
    required this.fileName,
  });

  Map<String, dynamic> toJson() => {
    'url': url,
    'contentType': contentType,
  };
}
