import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../models/multimodal_payload.dart';
import '../services/genkit_api_service.dart';

class AssistantProvider extends ChangeNotifier {
  final GenkitApiService _apiService;
  final Uuid _uuid = const Uuid();

  String _sessionId = '';
  bool _isLoading = false;
  String? _errorMessage;
  bool _backendHealthy = false;
  MultimodalOutput? _currentOutput;
  final List<MultimodalOutput> _history = [];
  final List<MediaAttachment> _stagedMedia = [];
  double _temperature = 0.2;

  AssistantProvider({GenkitApiService? apiService})
      : _apiService = apiService ?? const GenkitApiService() {
    _sessionId = _uuid.v4();
    verifyBackendHealth();
  }

  String get sessionId => _sessionId;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get backendHealthy => _backendHealthy;
  MultimodalOutput? get currentOutput => _currentOutput;
  List<MultimodalOutput> get history => List.unmodifiable(_history);
  List<MediaAttachment> get stagedMedia => List.unmodifiable(_stagedMedia);
  double get temperature => _temperature;

  void setTemperature(double val) {
    _temperature = val;
    notifyListeners();
  }

  Future<void> verifyBackendHealth() async {
    try {
      final res = await _apiService.checkHealth();
      _backendHealthy = (res['status'] == 'ONLINE' || res['status'] == 'OK');
    } catch (_) {
      _backendHealthy = false;
    }
    notifyListeners();
  }

  void addMediaAttachment(MediaAttachment attachment) {
    _stagedMedia.add(attachment);
    notifyListeners();
  }

  void removeMediaAttachment(int index) {
    if (index >= 0 && index < _stagedMedia.length) {
      _stagedMedia.removeAt(index);
      notifyListeners();
    }
  }

  void clearStagedMedia() {
    _stagedMedia.clear();
    notifyListeners();
  }

  void resetSession() {
    _sessionId = _uuid.v4();
    _currentOutput = null;
    _errorMessage = null;
    _stagedMedia.clear();
    notifyListeners();
  }

  Future<void> sendPrompt(String prompt) async {
    if (prompt.trim().isEmpty && _stagedMedia.isEmpty) return;

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await _apiService.queryAssistant(
        sessionId: _sessionId,
        prompt: prompt,
        media: _stagedMedia.isNotEmpty ? List.of(_stagedMedia) : null,
        temperature: _temperature,
      );

      _currentOutput = result;
      _history.add(result);
      _stagedMedia.clear();
      _backendHealthy = true;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _apiService.dispose();
    super.dispose();
  }
}
