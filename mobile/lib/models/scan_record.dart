/// A single row of `public.scans` — one completed gemstone scan
/// (Module 5: Scan History).
class ScanRecord {
  final String id;
  final String gemType;
  final double confidence;
  final double? carat;
  final String? cut;
  final String? clarity;
  final String? color;
  final double? estimatedPrice;
  final double? priceRangeLow;
  final double? priceRangeHigh;
  final String? imageUrl;
  final DateTime createdAt;

  const ScanRecord({
    required this.id,
    required this.gemType,
    required this.confidence,
    this.carat,
    this.cut,
    this.clarity,
    this.color,
    this.estimatedPrice,
    this.priceRangeLow,
    this.priceRangeHigh,
    this.imageUrl,
    required this.createdAt,
  });

  factory ScanRecord.fromJson(Map<String, dynamic> json) {
    return ScanRecord(
      id: json['id'] as String,
      gemType: json['gem_type'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      carat: (json['carat'] as num?)?.toDouble(),
      cut: json['cut'] as String?,
      clarity: json['clarity'] as String?,
      color: json['color'] as String?,
      estimatedPrice: (json['estimated_price'] as num?)?.toDouble(),
      priceRangeLow: (json['price_range_low'] as num?)?.toDouble(),
      priceRangeHigh: (json['price_range_high'] as num?)?.toDouble(),
      imageUrl: json['image_url'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Shape expected by `scans` table INSERT (see supabase/schema.sql) --
  /// deliberately omits `id`/`created_at`, which Postgres generates itself,
  /// so callers construct a ScanRecord with a placeholder `id: ''` purely
  /// to hold the other fields until the real row (with its real id) comes
  /// back from a subsequent fetchHistory().
  Map<String, dynamic> toInsertJson(String userId) => {
        'user_id': userId,
        'gem_type': gemType,
        'confidence': confidence,
        if (carat != null) 'carat': carat,
        if (cut != null) 'cut': cut,
        if (clarity != null) 'clarity': clarity,
        if (color != null) 'color': color,
        if (estimatedPrice != null) 'estimated_price': estimatedPrice,
        if (priceRangeLow != null) 'price_range_low': priceRangeLow,
        if (priceRangeHigh != null) 'price_range_high': priceRangeHigh,
        if (imageUrl != null) 'image_url': imageUrl,
      };
}
