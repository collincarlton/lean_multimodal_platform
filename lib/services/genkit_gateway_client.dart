import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

@immutable
class GatewayChunk {
  final String text;
  final bool isComplete;
  final double? latencyMs;
  final Map<String, dynamic>? metadata;

  const GatewayChunk({
    required this.text,
    required this.isComplete,
    this.latencyMs,
    this.metadata,
  });
}

class GenkitGatewayClient {
  final String baseUrl;
  final http.Client _httpClient;

  GenkitGatewayClient({
    this.baseUrl = 'http://127.0.0.1:5050',
    http.Client? httpClient,
  }) : _httpClient = httpClient ?? http.Client();

  Future<bool> probeHealth() async {
    final uri = Uri.parse('$baseUrl/healthz');
    try {
      final response = await _httpClient.get(uri).timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Stream<GatewayChunk> streamPrompt({
    required String prompt,
    Uint8List? audioFrameBytes,
    Uint8List? imageBytes,
    Map<String, dynamic>? sessionContext,
  }) async* {
    final uri = Uri.parse('$baseUrl/gateway/stream');
    final stopwatch = Stopwatch()..start();

    final payload = <String, dynamic>{
      'prompt': prompt,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      if (sessionContext != null) 'context': sessionContext,
      if (audioFrameBytes != null) 'audio_b64': base64Encode(audioFrameBytes),
      if (imageBytes != null) 'image_b64': base64Encode(imageBytes),
    };

    final request = http.Request('POST', uri)
      ..headers['Content-Type'] = 'application/json'
      ..headers['Accept'] = 'text/event-stream'
      ..body = jsonEncode(payload);

    http.StreamedResponse response;
    try {
      response = await _httpClient.send(request);
    } catch (e) {
      yield GatewayChunk(
        text: 'GATEWAY_OFFLINE_FALLBACK: $e',
        isComplete: true,
        latencyMs: stopwatch.elapsedMilliseconds.toDouble(),
      );
      return;
    }

    if (response.statusCode != 200) {
      yield GatewayChunk(
        text: 'GATEWAY_ERROR: HTTP ${response.statusCode}',
        isComplete: true,
        latencyMs: stopwatch.elapsedMilliseconds.toDouble(),
      );
      return;
    }

    final lineStream = response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter());

    await for (final line in lineStream) {
      if (line.isEmpty || line.startsWith(':')) continue;

      if (line.startsWith('data: ')) {
        final dataJson = line.substring(6).trim();
        if (dataJson == '[DONE]') {
          yield GatewayChunk(
            text: '',
            isComplete: true,
            latencyMs: stopwatch.elapsedMilliseconds.toDouble(),
          );
          break;
        }

        try {
          final Map<String, dynamic> parsed = jsonDecode(dataJson);
          yield GatewayChunk(
            text: parsed['content'] ?? parsed['text'] ?? '',
            isComplete: parsed['done'] ?? false,
            latencyMs: stopwatch.elapsedMilliseconds.toDouble(),
            metadata: parsed['metadata'],
          );
        } catch (_) {
          yield GatewayChunk(
            text: dataJson,
            isComplete: false,
            latencyMs: stopwatch.elapsedMilliseconds.toDouble(),
          );
        }
      }
    }
  }

  void dispose() {
    _httpClient.close();
  }
}
