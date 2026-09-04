// Copy this file to secrets.dart (already gitignored) and fill in your own
// values. secrets.dart is imported by app_config.dart.
//
// Supabase values: Supabase dashboard -> Project Settings -> API.
class Secrets {
  static const supabaseUrl = 'https://YOUR-PROJECT.supabase.co';
  static const supabasePublishableKey = 'sb_publishable_...';

  // FastAPI backend base URL (see backend/README section in the project
  // README for how to run it).
  //  - Android emulator reaching a backend on your host machine:
  //      http://10.0.2.2:8000
  //  - iOS simulator / Flutter web / physical device on the same Wi-Fi:
  //      http://<your-machine-lan-ip>:8000
  //  - Deployed backend (Render/Railway):
  //      https://your-app.onrender.com
  static const apiBaseUrl = 'http://10.0.2.2:8000';
}
