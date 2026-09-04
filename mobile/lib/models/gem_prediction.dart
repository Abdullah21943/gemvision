class GemPrediction {
  final String label;
  final double confidence;

  const GemPrediction({required this.label, required this.confidence});

  factory GemPrediction.fromJson(Map<String, dynamic> json) {
    return GemPrediction(
      label: json['label'] as String,
      confidence: (json['confidence'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {'label': label, 'confidence': confidence};
}

class PredictResult {
  final GemPrediction topPrediction;
  final List<GemPrediction> topK;

  const PredictResult({required this.topPrediction, required this.topK});

  factory PredictResult.fromJson(Map<String, dynamic> json) {
    return PredictResult(
      topPrediction: GemPrediction.fromJson(json['top_prediction']),
      topK: (json['top_k'] as List)
          .map((e) => GemPrediction.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PriceEstimate {
  final double estimatedPrice;
  final double priceRangeLow;
  final double priceRangeHigh;
  final String currency;

  const PriceEstimate({
    required this.estimatedPrice,
    required this.priceRangeLow,
    required this.priceRangeHigh,
    required this.currency,
  });

  factory PriceEstimate.fromJson(Map<String, dynamic> json) {
    return PriceEstimate(
      estimatedPrice: (json['estimated_price'] as num).toDouble(),
      priceRangeLow: (json['price_range_low'] as num).toDouble(),
      priceRangeHigh: (json['price_range_high'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'USD',
    );
  }
}
