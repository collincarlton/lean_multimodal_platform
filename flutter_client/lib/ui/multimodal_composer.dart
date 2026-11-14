import 'dart:async';
import 'package:flutter/material.dart';
import '../models/multimodal_payload.dart';
import '../services/audio_recorder_service.dart';
import 'audio_waveform_visualizer.dart';
import 'vault_browser_dialog.dart';

class MultimodalComposer extends StatefulWidget {
  final Function(MultimodalInput) onSubmit;
  final bool isLoading;

  const MultimodalComposer({
    super.key,
    required this.onSubmit,
    required this.isLoading,
  });

  @override
  State<MultimodalComposer> createState() => _MultimodalComposerState();
}

class _MultimodalComposerState extends State<MultimodalComposer> {
  final TextEditingController _textController = TextEditingController();
  final AudioRecorderService _audioService = AudioRecorderService();
  StreamSubscription<List<double>>? _waveformSub;

  List<double> _liveWaveform = List.filled(32, 0.05);
  bool _isRecording = false;
  int _recordingDurationMs = 0;
  Timer? _durationTimer;

  AudioRecordingResult? _attachedAudio;
  String? _attachedVaultFileName;
  String? _attachedVaultUrl;

  bool _isPlayingPreview = false;
  Timer? _previewTimer;

  @override
  void initState() {
    super.initState();
    _waveformSub = _audioService.waveformStream.listen((waveform) {
      if (mounted) {
        setState(() => _liveWaveform = waveform);
      }
    });
    _registerPushToTalkBridge();
  }

  void _registerPushToTalkBridge() {
    // Native macOS desktop push-to-talk is coordinated via LeanPortalCompanion HUD daemon
  }

  @override
  void dispose() {
    _waveformSub?.cancel();
    _durationTimer?.cancel();
    _previewTimer?.cancel();
    _audioService.dispose();
    _textController.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    final started = await _audioService.startRecording();
    if (started && mounted) {
      setState(() {
        _isRecording = true;
        _recordingDurationMs = 0;
        _attachedAudio = null;
        _isPlayingPreview = false;
      });
      _durationTimer?.cancel();
      _durationTimer = Timer.periodic(const Duration(milliseconds: 100), (_) {
        if (mounted && _isRecording) {
          setState(() => _recordingDurationMs += 100);
        }
      });
    }
  }

  Future<void> _stopRecording() async {
    _durationTimer?.cancel();
    final result = await _audioService.stopRecording();
    if (mounted) {
      setState(() {
        _isRecording = false;
        _attachedAudio = result;
      });
    }
  }

  void _cancelRecording() {
    _durationTimer?.cancel();
    _audioService.cancelRecording();
    if (mounted) {
      setState(() {
        _isRecording = false;
        _recordingDurationMs = 0;
        _liveWaveform = List.filled(32, 0.05);
      });
    }
  }

  void _playAttachedAudioPreview() {
    if (_attachedAudio == null) return;

    if (!_isPlayingPreview) {
      setState(() => _isPlayingPreview = true);
      _audioService.playPreview(
          _attachedAudio!.base64Data, _attachedAudio!.mimeType);

      _previewTimer?.cancel();
      final duration =
          Duration(milliseconds: _attachedAudio!.durationMs.clamp(800, 30000));
      _previewTimer = Timer(duration, () {
        if (mounted) {
          setState(() => _isPlayingPreview = false);
        }
      });
    } else {
      _previewTimer?.cancel();
      setState(() => _isPlayingPreview = false);
    }
  }

  void _openVaultBrowser() {
    showDialog(
      context: context,
      builder: (_) => VaultBrowserDialog(
        onSelectAsset: (fileName, driveUrl) {
          setState(() {
            _attachedVaultFileName = fileName;
            _attachedVaultUrl = driveUrl;
          });
        },
      ),
    );
  }

  void _handleSubmit() {
    final text = _textController.text.trim();
    if (text.isEmpty && _attachedAudio == null && _attachedVaultUrl == null) {
      return;
    }

    final input = MultimodalInput(
      prompt: text.isNotEmpty
          ? text
          : 'Analyze this attached multimodal telemetry and ground in cloud vault asset.',
      audioBase64: _attachedAudio?.base64Data,
      audioMimeType: _attachedAudio?.mimeType,
      audioDurationMs: _attachedAudio?.durationMs,
      driveFileUrl: _attachedVaultUrl,
      vaultFileName: _attachedVaultFileName,
    );

    widget.onSubmit(input);
    _textController.clear();
    setState(() {
      _attachedAudio = null;
      _attachedVaultFileName = null;
      _attachedVaultUrl = null;
      _isPlayingPreview = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_attachedVaultFileName != null) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF0F2B48),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: const Color(0xFF00D9F5).withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.cloud_done_rounded,
                      color: Color(0xFF00D9F5), size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '5 TB Vault: $_attachedVaultFileName',
                      style: const TextStyle(
                          color: Color(0xFFE2E8F0),
                          fontSize: 12,
                          fontWeight: FontWeight.w600),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text('[Zero Local I/O]',
                      style: TextStyle(
                          color: Color(0xFF00F5A0),
                          fontSize: 10,
                          fontFamily: 'monospace')),
                  const SizedBox(width: 6),
                  IconButton(
                    icon: const Icon(Icons.close_rounded,
                        size: 16, color: Color(0xFF94A3B8)),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    onPressed: () => setState(() {
                      _attachedVaultFileName = null;
                      _attachedVaultUrl = null;
                    }),
                  ),
                ],
              ),
            ),
          ],
          if (_attachedAudio != null) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: const Color(0xFF00F5A0).withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.graphic_eq_rounded,
                      color: Color(0xFF00F5A0), size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'Audio Note (${(_attachedAudio!.durationMs / 1000).toStringAsFixed(1)}s)',
                    style: const TextStyle(
                        color: Color(0xFFF1F5F9),
                        fontSize: 12,
                        fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(width: 10),
                  InkWell(
                    onTap: _playAttachedAudioPreview,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: _isPlayingPreview
                            ? const Color(0xFF00D9F5).withValues(alpha: 0.25)
                            : const Color(0xFF00F5A0).withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: _isPlayingPreview
                              ? const Color(0xFF00D9F5)
                              : const Color(0xFF00F5A0).withValues(alpha: 0.4),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _isPlayingPreview
                                ? Icons.volume_up_rounded
                                : Icons.play_arrow_rounded,
                            color: _isPlayingPreview
                                ? const Color(0xFF00D9F5)
                                : const Color(0xFF00F5A0),
                            size: 14,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _isPlayingPreview ? 'Playing...' : 'Play Test',
                            style: TextStyle(
                              color: _isPlayingPreview
                                  ? const Color(0xFF00D9F5)
                                  : const Color(0xFF00F5A0),
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close_rounded,
                        size: 16, color: Color(0xFF94A3B8)),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    onPressed: () => setState(() {
                      _attachedAudio = null;
                      _isPlayingPreview = false;
                    }),
                  ),
                ],
              ),
            ),
          ],
          if (_isRecording)
            AudioWaveformVisualizer(
              waveform: _liveWaveform,
              durationMs: _recordingDurationMs,
              onCancel: _cancelRecording,
              onStop: _stopRecording,
            )
          else ...[
            TextField(
              controller: _textController,
              enabled: !widget.isLoading,
              style: const TextStyle(color: Color(0xFFF8FAFC), fontSize: 14),
              maxLines: 3,
              minLines: 1,
              decoration: const InputDecoration(
                hintText:
                    'Enter diagnostic instruction, attach audio, or link 5 TB Google Drive assets...',
                hintStyle: TextStyle(color: Color(0xFF475569), fontSize: 14),
                border: InputBorder.none,
                isDense: true,
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 4, vertical: 6),
              ),
              onSubmitted: (_) => _handleSubmit(),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                IconButton(
                  tooltip: 'Record Audio (or Hold Cmd+Ctrl+Option+Space)',
                  icon: const Icon(Icons.mic_rounded,
                      color: Color(0xFF00F5A0), size: 22),
                  onPressed: widget.isLoading ? null : _startRecording,
                ),
                IconButton(
                  tooltip: 'Browse Google One (5 TB Vault)',
                  icon: const Icon(Icons.cloud_queue_rounded,
                      color: Color(0xFF00D9F5), size: 22),
                  onPressed: widget.isLoading ? null : _openVaultBrowser,
                ),
                const Spacer(),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00F5A0),
                    foregroundColor: const Color(0xFF0A0E17),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 18, vertical: 10),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: widget.isLoading ? null : _handleSubmit,
                  child: widget.isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                                Color(0xFF0A0E17)),
                          ),
                        )
                      : const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('Reason',
                                style: TextStyle(
                                    fontWeight: FontWeight.bold, fontSize: 13)),
                            SizedBox(width: 6),
                            Icon(Icons.bolt_rounded, size: 16),
                          ],
                        ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
