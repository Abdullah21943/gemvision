import 'dart:io';

import 'package:flutter/material.dart';

import '../../models/gem_prediction.dart';
import '../../models/scan_record.dart';
import '../../services/gemvision_api.dart';
import '../../services/scan_history_service.dart';
import '../../widgets/primary_button.dart';

const _cutOptions = ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair'];
const _clarityOptions = ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1'];
const _colorOptions = ['D', 'E', 'F', 'G', 'H', 'I', 'J'];

/// Module 4 (Price Estimation). Reached either directly from the dashboard
/// (standalone estimate) or after Module 3's Results screen, in which case
/// the image + confidence are carried along so the full scan can be saved
/// to history (Module 5) once a price estimate exists.
class PriceFormScreen extends StatefulWidget {
  final String? initialGemType;
  final File? imageFile;
  final double? predictionConfidence;

  const PriceFormScreen({
    super.key,
    this.initialGemType,
    this.imageFile,
    this.predictionConfidence,
  });

  @override
  State<PriceFormScreen> createState() => _PriceFormScreenState();
}

class _PriceFormScreenState extends State<PriceFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _gemTypeController = TextEditingController();
  final _caratController = TextEditingController();
  final _api = GemVisionApi();
  final _historyService = ScanHistoryService();

  String _cut = _cutOptions.first;
  String _clarity = _clarityOptions.first;
  String? _color;

  bool _loading = false;
  bool _saving = false;
  bool _saved = false;
  String? _error;
  PriceEstimate? _estimate;

  @override
  void initState() {
    super.initState();
    _gemTypeController.text = widget.initialGemType ?? '';
  }

  @override
  void dispose() {
    _gemTypeController.dispose();
    _caratController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
      _estimate = null;
      _saved = false;
    });

    try {
      final estimate = await _api.estimatePrice(
        gemType: _gemTypeController.text.trim(),
        carat: double.parse(_caratController.text),
        cut: _cut,
        clarity: _clarity,
        color: _color,
      );
      setState(() => _estimate = estimate);
    } on GemVisionApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Price estimation failed: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  bool get _canSaveToHistory =>
      _estimate != null && widget.imageFile != null && widget.predictionConfidence != null;

  Future<void> _saveToHistory() async {
    if (!_canSaveToHistory) return;
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final imageUrl = await _historyService.uploadScanImage(widget.imageFile!);
      await _historyService.saveScan(
        ScanRecord(
          id: '',
          gemType: _gemTypeController.text.trim(),
          confidence: widget.predictionConfidence!,
          carat: double.parse(_caratController.text),
          cut: _cut,
          clarity: _clarity,
          color: _color,
          estimatedPrice: _estimate!.estimatedPrice,
          priceRangeLow: _estimate!.priceRangeLow,
          priceRangeHigh: _estimate!.priceRangeHigh,
          imageUrl: imageUrl,
          createdAt: DateTime.now(),
        ),
      );
      setState(() => _saved = true);
    } catch (e) {
      setState(() => _error = 'Could not save to history: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Estimate price')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _gemTypeController,
                  decoration: const InputDecoration(labelText: 'Gemstone type', prefixIcon: Icon(Icons.diamond_outlined)),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter a gemstone type' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _caratController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Carat', prefixIcon: Icon(Icons.scale_outlined)),
                  validator: (v) {
                    final parsed = double.tryParse(v ?? '');
                    if (parsed == null || parsed <= 0) return 'Enter a valid carat weight';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: _cut,
                  decoration: const InputDecoration(labelText: 'Cut'),
                  items: _cutOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) => setState(() => _cut = v!),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: _clarity,
                  decoration: const InputDecoration(labelText: 'Clarity'),
                  items: _clarityOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) => setState(() => _clarity = v!),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: _color,
                  decoration: const InputDecoration(labelText: 'Color (optional)'),
                  items: _colorOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) => setState(() => _color = v),
                ),
                const SizedBox(height: 24),
                if (_error != null) ...[
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                  const SizedBox(height: 12),
                ],
                PrimaryButton(label: 'Get estimate', icon: Icons.calculate_outlined, loading: _loading, onPressed: _submit),
                if (_estimate != null) ...[
                  const SizedBox(height: 20),
                  _PriceEstimateCard(estimate: _estimate!),
                  const SizedBox(height: 16),
                  if (_canSaveToHistory)
                    PrimaryButton(
                      label: _saved ? 'Saved to history' : 'Save to history',
                      icon: _saved ? Icons.check : Icons.save_outlined,
                      loading: _saving,
                      onPressed: _saved ? null : _saveToHistory,
                    ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _PriceEstimateCard extends StatelessWidget {
  final PriceEstimate estimate;
  const _PriceEstimateCard({required this.estimate});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Estimated price', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 4),
            Text(
              '${estimate.currency} ${estimate.estimatedPrice.toStringAsFixed(2)}',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Range: ${estimate.currency} ${estimate.priceRangeLow.toStringAsFixed(2)} '
              '– ${estimate.priceRangeHigh.toStringAsFixed(2)}',
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
