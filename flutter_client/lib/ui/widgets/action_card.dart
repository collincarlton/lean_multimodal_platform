import 'dart:convert';
import 'package:flutter/material.dart';
import '../../models/multimodal_payload.dart';

class ActionCard extends StatelessWidget {
  final ActionItem action;
  final VoidCallback? onExecute;

  const ActionCard({super.key, required this.action, this.onExecute});

  @override
  Widget build(BuildContext context) {
    final paramStr = const JsonEncoder.withIndent('  ').convert(action.parameters);

    return Card(
      color: const Color(0xFF1E222B),
      elevation: 0,
      margin: const EdgeInsets.symmetric(vertical: 6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.deepPurpleAccent.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: Colors.deepPurpleAccent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    action.actionType,
                    style: const TextStyle(
                      color: Colors.deepPurpleAccent,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    action.target,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (onExecute != null)
                  ElevatedButton(
                    onPressed: onExecute,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent.withValues(alpha: 0.2),
                      foregroundColor: Colors.blueAccent,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: const Text('TRIGGER', style: TextStyle(fontSize: 10)),
                  ),
              ],
            ),
            if (action.parameters.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  paramStr,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 11,
                    color: Colors.white60,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
