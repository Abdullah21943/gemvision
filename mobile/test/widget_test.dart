import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:gemvision/widgets/primary_button.dart';

/// Screens that touch AuthService (i.e. Supabase.instance) can't be pumped
/// in a widget test without a live Supabase.initialize() call, so this
/// smoke test sticks to a Supabase-independent widget instead.
void main() {
  testWidgets('PrimaryButton shows its label and fires onPressed', (tester) async {
    var tapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PrimaryButton(label: 'Analyze gemstone', onPressed: () => tapped = true),
        ),
      ),
    );

    expect(find.text('Analyze gemstone'), findsOneWidget);

    await tester.tap(find.text('Analyze gemstone'));
    await tester.pump();

    expect(tapped, isTrue);
  });

  testWidgets('PrimaryButton shows a spinner and disables tap while loading', (tester) async {
    var tapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PrimaryButton(label: 'Analyze gemstone', loading: true, onPressed: () => tapped = true),
        ),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Analyze gemstone'), findsNothing);

    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();

    expect(tapped, isFalse);
  });
}
