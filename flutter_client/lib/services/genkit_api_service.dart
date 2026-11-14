import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/multimodal_payload.dart';
import '../models/session_history.dart';

class GenkitApiService {
  final String baseUrl;
  final Duration clientTimeout;

  const GenkitApiService({
    this.baseUrl = '',
    this.clientTimeout = const Duration(seconds: 120),
  });

  Future<Map<String, dynamic>> checkHealth() async {
    final uri = Uri.parse('$baseUrl/api/health');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Gateway health check returned ${response.statusCode}');
  }

  Future<List<VaultAsset>> getVaultManifest() async {
    final uri = Uri.parse('$baseUrl/api/vault/manifest');
    final response = await http.get(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final list = decoded['assets'] as List<dynamic>? ?? [];
      return list.map((e) => VaultAsset.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<List<SessionSummary>> getHistorySessions() async {
    final uri = Uri.parse('$baseUrl/api/history');
    final response = await http.get(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final list = decoded['sessions'] as List<dynamic>? ?? [];
      return list.map((e) => SessionSummary.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  Future<SessionDetail?> getSessionDetail(String id) async {
    final uri = Uri.parse('$baseUrl/api/history/$id');
    final response = await http.get(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return SessionDetail.fromJson(decoded);
    }
    return null;
  }

  Future<bool> deleteSession(String id) async {
    final uri = Uri.parse('$baseUrl/api/history/$id');
    final response = await http.delete(uri).timeout(const Duration(seconds: 5));
    return response.statusCode == 200;
  }

  Future<bool> clearHistory() async {
    final uri = Uri.parse('$baseUrl/api/history');
    final response = await http.delete(uri).timeout(const Duration(seconds: 5));
    return response.statusCode == 200;
  }

  Future<MultimodalOutput> postReasoning(MultimodalInput input) async {
    final uri = Uri.parse('$baseUrl/api/reason');
    final payloadJson = jsonEncode(input.toJson());

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json; charset=utf-8'},
          body: payloadJson,
        )
        .timeout(clientTimeout);

    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes))
          as Map<String, dynamic>;
      return MultimodalOutput.fromJson(decoded);
    } else {
      String errorMessage = 'Reasoning error (${response.statusCode})';
      try {
        final errJson = jsonDecode(response.body);
        if (errJson['error'] != null) errorMessage = errJson['error'];
      } catch (_) {}
      throw Exception(errorMessage);
    }
  }

  Future<MultimodalOutput> queryAssistant({
    required String sessionId,
    required String prompt,
    List<MediaAttachment>? media,
    double temperature = 0.2,
  }) async {
    String? imgB64;
    String? imgMime;
    String? audB64;
    String? audMime;

    if (media != null && media.isNotEmpty) {
      for (final m in media) {
        if (m.mimeType.startsWith('image/')) {
          imgB64 = m.base64Data;
          imgMime = m.mimeType;
        } else if (m.mimeType.startsWith('audio/')) {
          audB64 = m.base64Data;
          audMime = m.mimeType;
        }
      }
    }

    final input = MultimodalInput(
      prompt: prompt,
      imageBase64: imgB64,
      imageMimeType: imgMime,
      audioBase64: audB64,
      audioMimeType: audMime,
    );

    return postReasoning(input);
  }

  void dispose() {}
}
