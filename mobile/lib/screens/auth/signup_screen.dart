import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../services/auth_service.dart';
import '../../widgets/primary_button.dart';

/// Module 1 (Authentication): email/password registration via Supabase Auth.
/// AuthGate (main.dart) automatically routes to the signed-in HomeShell once
/// a session exists, so this screen only needs to handle the signed-up-but-
/// not-yet-confirmed case (response.session == null when email confirmation
/// is required) -- everything else is left to the auth-state listener.
class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _authService = AuthService();

  bool _loading = false;
  String? _error;
  String? _info;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
      _info = null;
    });

    try {
      final response = await _authService.signUp(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
      if (response.session == null && mounted) {
        setState(() => _info = 'Check your email to confirm your account, then log in.');
      }
    } on AuthException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Something went wrong. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
                  validator: (value) =>
                      (value == null || !value.contains('@')) ? 'Enter a valid email' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline)),
                  validator: (value) =>
                      (value == null || value.length < 6) ? 'Password must be 6+ characters' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _confirmController,
                  obscureText: true,
                  decoration:
                      const InputDecoration(labelText: 'Confirm password', prefixIcon: Icon(Icons.lock_outline)),
                  validator: (value) =>
                      (value != _passwordController.text) ? 'Passwords do not match' : null,
                ),
                const SizedBox(height: 20),
                if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
                if (_info != null) Text(_info!, style: const TextStyle(color: Colors.green)),
                const SizedBox(height: 8),
                PrimaryButton(label: 'Sign up', onPressed: _submit, loading: _loading),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
