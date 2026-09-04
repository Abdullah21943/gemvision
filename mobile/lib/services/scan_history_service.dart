import 'dart:io';

import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/app_config.dart';
import '../models/scan_record.dart';

/// Scan history persistence (Module 5): upload the image to Supabase
/// Storage, then insert/list/delete rows in public.scans.
class ScanHistoryService {
  final SupabaseClient _client = Supabase.instance.client;

  String get _userId {
    final user = _client.auth.currentUser;
    if (user == null) throw StateError('Not signed in');
    return user.id;
  }

  Future<String> uploadScanImage(File imageFile) async {
    final fileName = '${DateTime.now().millisecondsSinceEpoch}.jpg';
    final storagePath = '$_userId/$fileName';

    await _client.storage.from(AppConfig.scanImagesBucket).upload(
          storagePath,
          imageFile,
          fileOptions: const FileOptions(upsert: false),
        );

    return _client.storage.from(AppConfig.scanImagesBucket).getPublicUrl(storagePath);
  }

  Future<void> saveScan(ScanRecord scan) async {
    await _client.from('scans').insert(scan.toInsertJson(_userId));
  }

  Future<List<ScanRecord>> fetchHistory() async {
    final rows = await _client
        .from('scans')
        .select()
        .eq('user_id', _userId)
        .order('created_at', ascending: false);

    return (rows as List)
        .map((row) => ScanRecord.fromJson(row as Map<String, dynamic>))
        .toList();
  }

  Future<void> deleteScan(String scanId) async {
    await _client.from('scans').delete().eq('id', scanId);
  }
}
