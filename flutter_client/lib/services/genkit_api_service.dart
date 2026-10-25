import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/multimodal_payload.dart';

class GenkitApiService {
  final String baseUrl;
  final http.Client _client;

  GenkitApiService({
    String? baseUrl,
    http.Client? client,
  })  : baseUrl = baseUrl ?? const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:5050'),
        _client = client ?? http.Client();

  Future<bool> checkHealth() async {
    try {
      final response = await _client
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 120));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<MultimodalOutput> queryAssistant({
    required String sessionId,
    required String prompt,
    List<MediaAttachment>? media,
    double temperature = 0.2,
  }) async {
    final uri = Uri.parse('$baseUrl/api/assistant');
    final payload = <String, dynamic>{
      'sessionId': sessionId,
      'prompt': prompt,
      'temperature': temperature,
      if (media != null && media.isNotEmpty)
        'media': media.map((m) => m.toJson()).toList(),
    };

    final response = await _client
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) {
      final Map<String, dynamic> decoded =
          jsonDecode(response.body) as Map<String, dynamic>;
      return MultimodalOutput.fromJson(decoded);
    } else {
      throw Exception(
        'Genkit backend error (${response.statusCode}): ${response.body}',
      );
    }
  }

  void dispose() {
    _client.close();
  }
}
