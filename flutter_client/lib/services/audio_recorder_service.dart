import 'dart:async';
import 'dart:js_util' as js_util;

class AudioRecordingResult {
  final String base64Data;
  final String mimeType;
  final int durationMs;

  const AudioRecordingResult({
    required this.base64Data,
    required this.mimeType,
    required this.durationMs,
  });
}

class AudioRecorderService {
  Timer? _pollTimer;
  final StreamController<List<double>> _waveformController =
      StreamController<List<double>>.broadcast();

  Stream<List<double>> get waveformStream => _waveformController.stream;
  bool _isRecording = false;
  bool get isRecording => _isRecording;

  dynamic get _engine {
    if (js_util.hasProperty(js_util.globalThis, 'LeanAudioEngine')) {
      return js_util.getProperty(js_util.globalThis, 'LeanAudioEngine');
    }
    return null;
  }

  Future<bool> startRecording() async {
    final engine = _engine;
    if (engine == null) return false;

    try {
      final dynamic promise = js_util.callMethod(engine, 'start', []);
      final dynamic started = await js_util.promiseToFuture(promise);
      if (started == true) {
        _isRecording = true;
        _startWaveformPolling();
        return true;
      }
    } catch (_) {
      _isRecording = false;
    }
    return false;
  }

  void _startWaveformPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(milliseconds: 33), (_) {
      final engine = _engine;
      if (engine != null && _isRecording) {
        try {
          final dynamic rawObj = js_util.callMethod(engine, 'getWaveformString', []);
          final String raw = rawObj?.toString() ?? '';
          if (raw.isNotEmpty) {
            final List<double> values = raw
                .split(',')
                .map((s) => double.tryParse(s) ?? 0.05)
                .toList();
            if (values.length == 32) {
              _waveformController.add(values);
            }
          }
        } catch (_) {}
      }
    });
  }

  Future<AudioRecordingResult?> stopRecording() async {
    _pollTimer?.cancel();
    _isRecording = false;
    final engine = _engine;
    if (engine == null) return null;

    try {
      final dynamic promise = js_util.callMethod(engine, 'stop', []);
      final dynamic result = await js_util.promiseToFuture(promise);
      if (result != null) {
        final base64 = js_util.getProperty(result, 'base64') as String;
        final mimeType = js_util.getProperty(result, 'mimeType') as String;
        final durationMs =
            (js_util.getProperty(result, 'durationMs') as num).toInt();
        return AudioRecordingResult(
          base64Data: base64,
          mimeType: mimeType,
          durationMs: durationMs,
        );
      }
    } catch (_) {}
    return null;
  }

  void cancelRecording() {
    _pollTimer?.cancel();
    _isRecording = false;
    final engine = _engine;
    if (engine != null) {
      try {
        js_util.callMethod(engine, 'cancel', []);
      } catch (_) {}
    }
  }

  void playPreview(String base64Data, String mimeType) {
    final engine = _engine;
    if (engine != null) {
      try {
        js_util.callMethod(engine, 'playPreview', [base64Data, mimeType]);
      } catch (_) {}
    }
  }

  void dispose() {
    cancelRecording();
    _waveformController.close();
  }
}
