import 'dart:ui';
import 'package:flutter/material.dart';
import 'models/multimodal_payload.dart';
import 'models/session_history.dart';
import 'services/genkit_api_service.dart';
import 'ui/history_sidebar.dart';
import 'ui/multimodal_composer.dart';
import 'ui/reasoning_view.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LeanPortalApp());
}

class LeanPortalApp extends StatelessWidget {
  const LeanPortalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Lean Sovereign Multimodal Platform',
      debugShowCheckedModeBanner: false,
      scrollBehavior: const MaterialScrollBehavior().copyWith(
        dragDevices: {
          PointerDeviceKind.mouse,
          PointerDeviceKind.touch,
          PointerDeviceKind.trackpad,
          PointerDeviceKind.stylus,
        },
      ),
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0E17),
        fontFamily: 'system-ui',
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00F5A0),
          secondary: Color(0xFF00D9F5),
          surface: Color(0xFF0F172A),
        ),
      ),
      home: const PlatformPortalShell(),
    );
  }
}

class PlatformPortalShell extends StatefulWidget {
  const PlatformPortalShell({super.key});

  @override
  State<PlatformPortalShell> createState() => _PlatformPortalShellState();
}

class _PlatformPortalShellState extends State<PlatformPortalShell> {
  final GenkitApiService _apiService = const GenkitApiService();

  List<SessionSummary> _historySessions = [];
  String? _activeSessionId;
  MultimodalOutput? _currentOutput;

  bool _isLoading = false;
  bool _isLoadingHistory = true;
  String? _errorMessage;
  String _gatewayStatus = 'CONNECTING';

  @override
  void initState() {
    super.initState();
    _checkGateway();
    _loadHistory();
  }

  Future<void> _checkGateway() async {
    try {
      final health = await _apiService.checkHealth();
      if (mounted) {
        setState(
            () => _gatewayStatus = health['status'] as String? ?? 'ONLINE');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _gatewayStatus = 'STANDALONE');
      }
    }
  }

  Future<void> _loadHistory() async {
    try {
      final list = await _apiService.getHistorySessions();
      if (mounted) {
        setState(() {
          _historySessions = list;
          _isLoadingHistory = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoadingHistory = false);
      }
    }
  }

  Future<void> _selectSession(String sessionId) async {
    setState(() {
      _activeSessionId = sessionId;
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final detail = await _apiService.getSessionDetail(sessionId);
      if (mounted) {
        setState(() {
          _currentOutput = detail?.output;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceFirst('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  void _newSession() {
    setState(() {
      _activeSessionId = null;
      _currentOutput = null;
      _errorMessage = null;
    });
  }

  Future<void> _deleteSession(String sessionId) async {
    await _apiService.deleteSession(sessionId);
    if (_activeSessionId == sessionId) {
      _newSession();
    }
    _loadHistory();
  }

  Future<void> _clearAllSessions() async {
    await _apiService.clearHistory();
    _newSession();
    _loadHistory();
  }

  Future<void> _handleReasoningSubmission(MultimodalInput input) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _apiService.postReasoning(input);
      if (mounted) {
        setState(() {
          _currentOutput = result;
          _isLoading = false;
        });
      }
      _loadHistory();
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceFirst('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isWide = width >= 860;
    final isCompact = width < 580;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
        titleSpacing: 10,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0xFF00F5A0).withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                    color: const Color(0xFF00F5A0).withValues(alpha: 0.8)),
              ),
              child: const Text(
                'SOVEREIGN 5.0',
                style: TextStyle(
                  color: Color(0xFF00F5A0),
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                isCompact ? 'Diagnostic Portal' : 'Multimodal Reasoning Engine',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFFF8FAFC),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          Center(
            child: Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      color: _gatewayStatus == 'ONLINE'
                          ? const Color(0xFF00F5A0)
                          : const Color(0xFFFF9900),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    isCompact ? 'gemini-3' : 'gemini-3: $_gatewayStatus',
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 10,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      drawer: isWide
          ? null
          : Drawer(
              backgroundColor: const Color(0xFF0F172A),
              child: HistorySidebar(
                sessions: _historySessions,
                activeSessionId: _activeSessionId,
                isLoading: _isLoadingHistory,
                onSelectSession: (id) {
                  Navigator.of(context).pop();
                  _selectSession(id);
                },
                onNewSession: () {
                  Navigator.of(context).pop();
                  _newSession();
                },
                onDeleteSession: _deleteSession,
                onClearAll: _clearAllSessions,
              ),
            ),
      body: SafeArea(
        child: Row(
          children: [
            if (isWide)
              HistorySidebar(
                sessions: _historySessions,
                activeSessionId: _activeSessionId,
                isLoading: _isLoadingHistory,
                onSelectSession: _selectSession,
                onNewSession: _newSession,
                onDeleteSession: _deleteSession,
                onClearAll: _clearAllSessions,
              ),
            Expanded(
              child: Center(
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 960),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Column(
                    children: [
                      Expanded(
                        child: ReasoningView(
                          output: _currentOutput,
                          isLoading: _isLoading,
                          errorMessage: _errorMessage,
                        ),
                      ),
                      const SizedBox(height: 10),
                      MultimodalComposer(
                        isLoading: _isLoading,
                        onSubmit: _handleReasoningSubmission,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
