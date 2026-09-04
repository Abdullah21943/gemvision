import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../models/scan_record.dart';
import '../../services/scan_history_service.dart';
import '../../theme/app_theme.dart';

/// Module 5: Scan History — list, filter by gem type, delete.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _service = ScanHistoryService();
  late Future<List<ScanRecord>> _future;
  String _filter = 'All';

  @override
  void initState() {
    super.initState();
    _future = _service.fetchHistory();
  }

  void _reload() {
    setState(() => _future = _service.fetchHistory());
  }

  Future<void> _delete(ScanRecord scan) async {
    await _service.deleteScan(scan.id);
    _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan history')),
      body: SafeArea(
        child: FutureBuilder<List<ScanRecord>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text('Could not load history: ${snapshot.error}'));
            }

            final scans = snapshot.data ?? [];
            if (scans.isEmpty) {
              return const Center(child: Text('No scans yet. Identify a gemstone to get started.'));
            }

            final gemTypes = ['All', ...{for (final s in scans) s.gemType}];
            final filtered = _filter == 'All' ? scans : scans.where((s) => s.gemType == _filter).toList();

            return RefreshIndicator(
              onRefresh: () async => _reload(),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: DropdownButton<String>(
                        value: _filter,
                        items: gemTypes.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                        onChanged: (v) => setState(() => _filter = v ?? 'All'),
                      ),
                    ),
                  ),
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: filtered.length,
                      itemBuilder: (context, index) => _ScanTile(scan: filtered[index], onDelete: _delete),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _ScanTile extends StatelessWidget {
  final ScanRecord scan;
  final void Function(ScanRecord) onDelete;

  const _ScanTile({required this.scan, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: scan.imageUrl != null
              ? Image.network(scan.imageUrl!, width: 56, height: 56, fit: BoxFit.cover)
              : Container(
                  width: 56,
                  height: 56,
                  color: AppTheme.primary.withValues(alpha: 0.1),
                  child: const Icon(Icons.diamond_outlined, color: AppTheme.primary),
                ),
        ),
        title: Text(scan.gemType, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          '${(scan.confidence * 100).toStringAsFixed(0)}% confidence'
          '${scan.estimatedPrice != null ? ' · \$${scan.estimatedPrice!.toStringAsFixed(0)}' : ''}\n'
          '${DateFormat.yMMMd().add_jm().format(scan.createdAt)}',
        ),
        isThreeLine: true,
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: AppTheme.danger),
          onPressed: () => onDelete(scan),
        ),
      ),
    );
  }
}
