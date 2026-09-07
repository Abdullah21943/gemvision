import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../services/gemvision_api.dart';
import '../../widgets/primary_button.dart';
import 'results_screen.dart';

/// Module 2 (Image Capture and Upload) feeding into Module 3
/// (gemstone-type detection via the CNN /predict endpoint).
///
/// Uses image bytes (not dart:io File) throughout so this screen, the API
/// upload, and Supabase Storage upload all work identically on Android,
/// iOS, and Flutter Web -- File/Image.file are not supported on web.
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final _picker = ImagePicker();
  final _api = GemVisionApi();

  Uint8List? _imageBytes;
  String _imageName = 'gem.jpg';
  bool _analyzing = false;
  String? _error;

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 90);
    if (picked == null) return;
    final bytes = await picked.readAsBytes();
    setState(() {
      _imageBytes = bytes;
      _imageName = picked.name;
      _error = null;
    });
  }

  Future<void> _analyze() async {
    final bytes = _imageBytes;
    if (bytes == null) return;

    setState(() {
      _analyzing = true;
      _error = null;
    });

    try {
      final result = await _api.predictGemstone(bytes, _imageName);
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultsScreen(imageBytes: bytes, imageName: _imageName, result: result),
        ),
      );
    } on GemVisionApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Analysis failed: $e');
    } finally {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Identify gemstone')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: _imageBytes == null
                      ? const Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.diamond_outlined, size: 64, color: Colors.grey),
                              SizedBox(height: 12),
                              Text('Take or choose a photo of a gemstone', style: TextStyle(color: Colors.grey)),
                            ],
                          ),
                        )
                      : Image.memory(_imageBytes!, fit: BoxFit.cover),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pickImage(ImageSource.camera),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Camera'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pickImage(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Gallery'),
                    ),
                  ),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 16),
              PrimaryButton(
                label: 'Analyze gemstone',
                icon: Icons.auto_awesome,
                loading: _analyzing,
                onPressed: _imageBytes == null ? null : _analyze,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
