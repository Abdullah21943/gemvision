import 'secrets.dart';

/// Central place the rest of the app reads config from, so screens/services
/// never import Secrets directly.
class AppConfig {
  static const supabaseUrl = Secrets.supabaseUrl;
  static const supabaseAnonKey = Secrets.supabaseAnonKey;
  static const apiBaseUrl = Secrets.apiBaseUrl;

  static const scanImagesBucket = 'scan-images';
}
