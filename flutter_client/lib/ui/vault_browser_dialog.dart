import 'package:flutter/material.dart';
import '../models/multimodal_payload.dart';
import '../services/genkit_api_service.dart';

class VaultBrowserDialog extends StatefulWidget {
  final Function(String fileName, String driveUrl) onSelectAsset;

  const VaultBrowserDialog({super.key, required this.onSelectAsset});

  @override
  State<VaultBrowserDialog> createState() => _VaultBrowserDialogState();
}

class _VaultBrowserDialogState extends State<VaultBrowserDialog> {
  final GenkitApiService _api = const GenkitApiService();
  final TextEditingController _customUrlController = TextEditingController();

  List<VaultAsset> _assets = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadManifest();
  }

  Future<void> _loadManifest() async {
    final list = await _api.getVaultManifest();
    if (mounted) {
      setState(() {
        _assets = list;
        _isLoading = false;
      });
    }
  }

  void _attachCustomUrl() {
    final url = _customUrlController.text.trim();
    if (url.isEmpty) return;
    widget.onSelectAsset('Direct_Drive_Asset', url);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF0F172A),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: 600,
        height: 520,
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00D9F5).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.cloud_done_rounded,
                      color: Color(0xFF00D9F5), size: 20),
                ),
                const SizedBox(width: 12),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Google One (5 TB Vault) Catalog',
                      style: TextStyle(
                          color: Color(0xFFF8FAFC),
                          fontSize: 16,
                          fontWeight: FontWeight.bold),
                    ),
                    Text(
                      'Direct cloud stream without downloading to Fusion Drive',
                      style: TextStyle(color: Color(0xFF64748B), fontSize: 11),
                    ),
                  ],
                ),
                const Spacer(),
                IconButton(
                  icon:
                      const Icon(Icons.close_rounded, color: Color(0xFF94A3B8)),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const Divider(color: Color(0xFF1E293B), height: 24),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF131B2A),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.link_rounded,
                      color: Color(0xFF94A3B8), size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _customUrlController,
                      style: const TextStyle(
                          color: Color(0xFFF1F5F9), fontSize: 13),
                      decoration: const InputDecoration(
                        hintText:
                            'Paste Google Drive file URL (PDF, 4K Image, CAD)...',
                        hintStyle:
                            TextStyle(color: Color(0xFF475569), fontSize: 12),
                        border: InputBorder.none,
                        isDense: true,
                      ),
                      onSubmitted: (_) => _attachCustomUrl(),
                    ),
                  ),
                  TextButton(
                    onPressed: _attachCustomUrl,
                    child: const Text('Attach',
                        style: TextStyle(
                            color: Color(0xFF00D9F5),
                            fontWeight: FontWeight.bold,
                            fontSize: 12)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'INDEXED VAULT ASSETS',
              style: TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.0),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: _isLoading
                  ? const Center(
                      child: CircularProgressIndicator(
                          valueColor:
                              AlwaysStoppedAnimation<Color>(Color(0xFF00D9F5))),
                    )
                  : ListView.separated(
                      itemCount: _assets.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        final a = _assets[index];
                        final sizeMb =
                            (a.sizeBytes / 1024 / 1024).toStringAsFixed(1);
                        return InkWell(
                          onTap: () {
                            widget.onSelectAsset(a.name, a.driveUrl);
                            Navigator.of(context).pop();
                          },
                          borderRadius: BorderRadius.circular(10),
                          child: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF131B2A),
                              borderRadius: BorderRadius.circular(10),
                              border:
                                  Border.all(color: const Color(0xFF1E293B)),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  a.mimeType.contains('pdf')
                                      ? Icons.picture_as_pdf_rounded
                                      : Icons.image_rounded,
                                  color: a.mimeType.contains('pdf')
                                      ? const Color(0xFFFF4D4D)
                                      : const Color(0xFF00F5A0),
                                  size: 24,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        a.name,
                                        style: const TextStyle(
                                            color: Color(0xFFF1F5F9),
                                            fontSize: 13,
                                            fontWeight: FontWeight.w600),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        a.description,
                                        style: const TextStyle(
                                            color: Color(0xFF64748B),
                                            fontSize: 11),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF1E293B),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    '$sizeMb MB',
                                    style: const TextStyle(
                                        color: Color(0xFF94A3B8),
                                        fontSize: 11,
                                        fontFamily: 'monospace'),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
