import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../state/auth_state.dart';
import '../../widgets/dashboard_action_card.dart';
import '../capture/capture_screen.dart';
import '../price/price_form_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final email = context.watch<AppAuthState>().user?.email ?? '';

    return Scaffold(
      appBar: AppBar(title: const Text('GemVision')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Welcome back', style: Theme.of(context).textTheme.bodyMedium),
              Text(
                email,
                style: Theme.of(context).textTheme.headlineMedium,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 28),
              DashboardActionCard(
                icon: Icons.camera_alt_outlined,
                title: 'Identify a gemstone',
                subtitle: 'Snap or upload a photo to detect its type',
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const CaptureScreen()),
                ),
              ),
              const SizedBox(height: 16),
              DashboardActionCard(
                icon: Icons.attach_money,
                title: 'Estimate price',
                subtitle: 'Enter carat, cut and clarity for a price estimate',
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const PriceFormScreen()),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
