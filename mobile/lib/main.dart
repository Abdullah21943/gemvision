import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'config/app_config.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home/home_shell.dart';
import 'services/auth_service.dart';
import 'state/auth_state.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Must complete before runApp(): every screen assumes Supabase.instance
  // is ready (AuthService, ScanHistoryService construct a client eagerly).
  await Supabase.initialize(
    url: AppConfig.supabaseUrl,
    publishableKey: AppConfig.supabasePublishableKey,
  );

  runApp(const GemVisionApp());
}

/// App root: wraps everything in the one piece of app-wide state
/// (AppAuthState, the Supabase session) and hands routing to AuthGate.
class GemVisionApp extends StatelessWidget {
  const GemVisionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppAuthState(AuthService()),
      child: MaterialApp(
        title: 'GemVision',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: const AuthGate(),
      ),
    );
  }
}

/// Routes between the auth flow and the signed-in app shell based on
/// Supabase session state (Module 1).
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final isSignedIn = context.watch<AppAuthState>().isSignedIn;
    return isSignedIn ? const HomeShell() : const LoginScreen();
  }
}
