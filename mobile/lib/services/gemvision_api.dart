import 'dart:io';

import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../models/gem_prediction.dart';

/// Client for the FastAPI ML backend (Modules 3 & 4: /predict, /price).
class GemVisionApi {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );

  Future<PredictResult> predictGemstone(File imageFile) async {
    final fileName = imageFile.path.split(Platform.pathSeparator).last;
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(imageFile.path, filename: fileName),
    });

    try {
      final response = await _dio.post('/predict', data: formData);
      return PredictResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw GemVisionApiException(_messageFor(e));
    }
  }

  Future<PriceEstimate> estimatePrice({
    required String gemType,
    required double carat,
    required String cut,
    required String clarity,
    String? color,
  }) async {
    try {
      final response = await _dio.post(
        '/price',
        data: {
          'gem_type': gemType,
          'carat': carat,
          'cut': cut,
          'clarity': clarity,
          if (color != null && color.isNotEmpty) 'color': color,
        },
      );
      return PriceEstimate.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw GemVisionApiException(_messageFor(e));
    }
  }

  String _messageFor(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.connectionError) {
      return 'Could not reach the GemVision backend. Check API_BASE_URL in '
          'lib/config/secrets.dart and that the backend is running.';
    }
    return e.message ?? 'Unknown network error';
  }
}

class GemVisionApiException implements Exception {
  final String message;
  GemVisionApiException(this.message);

  @override
  String toString() => message;
}
