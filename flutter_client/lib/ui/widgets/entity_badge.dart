import 'package:flutter/material.dart';
import '../../models/multimodal_payload.dart';

class EntityBadge extends StatelessWidget {
  final EntityItem entity;

  const EntityBadge({super.key, required this.entity});

  Color _categoryColor(String category) {
    switch (category.toUpperCase()) {
      case 'TECHNOLOGY':
        return Colors.cyanAccent;
      case 'METRIC':
        return Colors.amberAccent;
      case 'ORGANIZATION':
        return Colors.lightGreenAccent;
      case 'PERSON':
        return Colors.purpleAccent;
      case 'TEMPORAL':
        return Colors.orangeAccent;
      default:
        return Colors.blueAccent;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _categoryColor(entity.category);
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.4), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              entity.category,
              style: TextStyle(
                color: color,
                fontSize: 10,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            entity.name,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '${(entity.confidence * 100).toInt()}%',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.6),
              fontSize: 11,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}
