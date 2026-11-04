import 'package:flutter/material.dart';
import '../models/session_history.dart';

class HistorySidebar extends StatelessWidget {
  final List<SessionSummary> sessions;
  final String? activeSessionId;
  final bool isLoading;
  final Function(String sessionId) onSelectSession;
  final VoidCallback onNewSession;
  final Function(String sessionId) onDeleteSession;
  final VoidCallback onClearAll;

  const HistorySidebar({
    super.key,
    required this.sessions,
    required this.activeSessionId,
    required this.isLoading,
    required this.onSelectSession,
    required this.onNewSession,
    required this.onDeleteSession,
    required this.onClearAll,
  });

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 280,
      decoration: const BoxDecoration(
        color: Color(0xFF0F172A),
        border: Border(right: BorderSide(color: Color(0xFF1E293B))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            child: Row(
              children: [
                const Icon(Icons.history_rounded,
                    color: Color(0xFF00F5A0), size: 18),
                const SizedBox(width: 8),
                const Text(
                  'REASONING HISTORY',
                  style: TextStyle(
                    color: Color(0xFFF1F5F9),
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.0,
                  ),
                ),
                const Spacer(),
                IconButton(
                  tooltip: 'New Diagnostic Session',
                  icon: const Icon(Icons.add_circle_outline_rounded,
                      color: Color(0xFF00F5A0), size: 20),
                  onPressed: onNewSession,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),
          const Divider(color: Color(0xFF1E293B), height: 1),
          Expanded(
            child: isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor:
                          AlwaysStoppedAnimation<Color>(Color(0xFF00F5A0)),
                    ),
                  )
                : sessions.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.inbox_rounded,
                                color: Colors.grey.shade800, size: 36),
                            const SizedBox(height: 8),
                            Text(
                              'No Saved Sessions',
                              style: TextStyle(
                                  color: Colors.grey.shade600, fontSize: 12),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: sessions.length,
                        itemBuilder: (context, index) {
                          final s = sessions[index];
                          final isSelected = s.id == activeSessionId;
                          return InkWell(
                            onTap: () => onSelectSession(s.id),
                            child: Container(
                              margin: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 4),
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? const Color(0xFF1E293B)
                                    : const Color(0xFF131B2A),
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(
                                  color: isSelected
                                      ? const Color(0xFF00F5A0)
                                          .withValues(alpha: 0.5)
                                      : const Color(0xFF1E293B),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(
                                        _formatTime(s.timestamp),
                                        style: const TextStyle(
                                          color: Color(0xFF64748B),
                                          fontSize: 10,
                                          fontFamily: 'monospace',
                                        ),
                                      ),
                                      const Spacer(),
                                      if (s.hasAudio)
                                        const Padding(
                                          padding: EdgeInsets.only(right: 4),
                                          child: Icon(Icons.graphic_eq_rounded,
                                              color: Color(0xFF00F5A0),
                                              size: 14),
                                        ),
                                      if (s.hasVaultGrounding)
                                        const Padding(
                                          padding: EdgeInsets.only(right: 4),
                                          child: Icon(Icons.cloud_done_rounded,
                                              color: Color(0xFF00D9F5),
                                              size: 14),
                                        ),
                                      InkWell(
                                        onTap: () => onDeleteSession(s.id),
                                        child: const Icon(Icons.close_rounded,
                                            color: Color(0xFF475569), size: 14),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    s.prompt.isNotEmpty
                                        ? s.prompt
                                        : 'Acoustic Diagnostic Telemetry',
                                    style: const TextStyle(
                                      color: Color(0xFFF1F5F9),
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    s.summarySnippet,
                                    style: const TextStyle(
                                        color: Color(0xFF94A3B8), fontSize: 11),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
          if (sessions.isNotEmpty) ...[
            const Divider(color: Color(0xFF1E293B), height: 1),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: const Color(0xFF64748B),
                  padding: EdgeInsets.zero,
                  minimumSize: const Size(0, 28),
                ),
                icon: const Icon(Icons.delete_sweep_rounded, size: 16),
                label: const Text('Clear History Cache',
                    style: TextStyle(fontSize: 11)),
                onPressed: onClearAll,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
