import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart' show User, AuthState;

import '../services/auth_service.dart';

/// Exposes the current Supabase session to the widget tree so
/// AuthGate can decide which screen to show without every screen
/// polling Supabase directly.
///
/// Named AppAuthState (not AuthState) to avoid colliding with
/// supabase_flutter's own AuthState class used by onAuthStateChange.
class AppAuthState extends ChangeNotifier {
  final AuthService _authService;
  late final StreamSubscription<AuthState> _subscription;
  User? user;

  AppAuthState(this._authService) {
    user = _authService.currentUser;
    _subscription = _authService.onAuthStateChange.listen((event) {
      user = event.session?.user;
      notifyListeners();
    });
  }

  bool get isSignedIn => user != null;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
