import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../models/gem_prediction.dart';
import '../../theme/app_theme.dart';
import '../../widgets/primary_button.dart';
import '../price/price_form_screen.dart';

/// Shows the CNN's top prediction + top-3 alternatives (Module 3 output).
class ResultsScreen extends StatelessWidget {
  final Uint8List imageBytes;
  final String imageName;
  final PredictResult result;

  const ResultsScreen({
    super.key,
    required this.imageBytes,
    required this.imageName,
    required this.result,
  });

  @override
  Widget build(BuildContext context) {
    final top = result.topPrediction;

    return Scaffold(
      appBar: AppBar(title: const Text('Result')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.memory(imageBytes, height: 220, width: double.infinity, fit: BoxFit.cover),
              ),
              const SizedBox(height: 20),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Detected gemstone', style: TextStyle(color: Colors.grey)),
                      const SizedBox(height: 4),
                      Text(top.label, style: Theme.of(context).textTheme.headlineMedium),
                      const SizedBox(height: 8),
                      _ConfidenceBar(confidence: top.confidence),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('Other possibilities', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              ...result.topK.skip(1).map(
                    (p) => Card(
                      child: ListTile(
                        title: Text(p.label),
                        trailing: Text('${(p.confidence * 100).toStringAsFixed(1)}%'),
                      ),
                    ),
                  ),
              const SizedBox(height: 20),
              PrimaryButton(
                label: 'Estimate price for this gem',
                icon: Icons.attach_money,
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PriceFormScreen(
                      initialGemType: top.label,
                      imageBytes: imageBytes,
                      imageName: imageName,
                      predictionConfidence: top.confidence,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double confidence;
  const _ConfidenceBar({required this.confidence});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: confidence.clamp(0, 1),
            minHeight: 10,
            backgroundColor: Colors.grey.shade200,
            valueColor: const AlwaysStoppedAnimation(AppTheme.accent),
          ),
        ),
        const SizedBox(height: 4),
        Text('${(confidence * 100).toStringAsFixed(1)}% confidence', style: const TextStyle(color: Colors.grey)),
      ],
    );
  }
}
