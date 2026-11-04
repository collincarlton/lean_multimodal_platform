import 'package:flutter/material.dart';

class AudioWaveformVisualizer extends StatelessWidget {
  final List<double> waveform;
  final int durationMs;
  final VoidCallback onCancel;
  final VoidCallback onStop;

  const AudioWaveformVisualizer({
    super.key,
    required this.waveform,
    required this.durationMs,
    required this.onCancel,
    required this.onStop,
  });

  String _formatDuration(int ms) {
    final totalSeconds = ms ~/ 1000;
    final minutes = totalSeconds ~/ 60;
    final seconds = totalSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  bool get _isVoiceActive {
    if (waveform.isEmpty) return false;
    return waveform.any((v) => v > 0.12);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF131B2A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _isVoiceActive
              ? const Color(0xFF00F5A0).withValues(alpha: 0.8)
              : const Color(0xFF00F5A0).withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _isVoiceActive
                  ? const Color(0xFF00F5A0).withValues(alpha: 0.2)
                  : const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              _isVoiceActive ? 'VOICE 🎙️' : 'REC',
              style: TextStyle(
                color: _isVoiceActive
                    ? const Color(0xFF00F5A0)
                    : const Color(0xFFFF4D4D),
                fontSize: 10,
                fontWeight: FontWeight.bold,
                fontFamily: 'monospace',
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            _formatDuration(durationMs),
            style: const TextStyle(
              color: Color(0xFFE2E8F0),
              fontFamily: 'monospace',
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: SizedBox(
              height: 36,
              child: CustomPaint(
                painter: _WaveformPainter(
                  values: waveform,
                  primaryColor: const Color(0xFF00F5A0),
                  secondaryColor: const Color(0xFF00D9F5),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.close_rounded,
                color: Color(0xFF94A3B8), size: 18),
            tooltip: 'Cancel',
            onPressed: onCancel,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
          const SizedBox(width: 8),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00F5A0),
              foregroundColor: const Color(0xFF0A0E17),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              minimumSize: const Size(0, 30),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8)),
            ),
            icon: const Icon(Icons.check_rounded, size: 15),
            label: const Text('Attach',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
            onPressed: onStop,
          ),
        ],
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  final List<double> values;
  final Color primaryColor;
  final Color secondaryColor;

  _WaveformPainter({
    required this.values,
    required this.primaryColor,
    required this.secondaryColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;

    final barCount = values.length;
    const spacing = 2.5;
    final totalSpacing = spacing * (barCount - 1);
    final barWidth = (size.width - totalSpacing) / barCount;

    final paint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.bottomCenter,
        end: Alignment.topCenter,
        colors: [primaryColor, secondaryColor],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    for (int i = 0; i < barCount; i++) {
      final double normalized = values[i].clamp(0.06, 1.0);
      final double barHeight =
          (normalized * size.height).clamp(4.0, size.height);
      final double x = i * (barWidth + spacing);
      final double y = (size.height - barHeight) / 2.0;

      final rrect = RRect.fromRectAndRadius(
        Rect.fromLTWH(x, y, barWidth, barHeight),
        const Radius.circular(2),
      );
      canvas.drawRRect(rrect, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) => true;
}
