import 'package:flutter/material.dart';

/// GemVision brand theme — deep amethyst + gold accent, evoking gemstones.
class AppTheme {
  static const Color primary = Color(0xFF5B2A86); // amethyst
  static const Color accent = Color(0xFFD4AF37); // gold
  static const Color background = Color(0xFFF7F5FA);
  static const Color surface = Colors.white;
  static const Color danger = Color(0xFFB3261E);

  /// The single ThemeData applied via MaterialApp(theme:) in main.dart --
  /// every screen in the app inherits these component styles (buttons,
  /// inputs, cards, app bars) rather than styling itself individually, so
  /// changing the brand look is a one-file change.
  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: primary,
      secondary: accent,
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: background,
      appBarTheme: const AppBarTheme(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 2,
        shadowColor: primary.withValues(alpha: 0.15),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(fontWeight: FontWeight.bold),
        titleLarge: TextStyle(fontWeight: FontWeight.w600),
      ),
    );
  }
}
