import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/assistant_provider.dart';
import 'ui/screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LeanMultimodalApp());
}

class LeanMultimodalApp extends StatelessWidget {
  const LeanMultimodalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AssistantProvider()),
      ],
      child: MaterialApp(
        title: 'Lean Multimodal Client',
        debugShowCheckedModeBanner: false,
        scrollBehavior: const MaterialScrollBehavior().copyWith(
          dragDevices: {
            PointerDeviceKind.mouse,
            PointerDeviceKind.touch,
            PointerDeviceKind.trackpad,
            PointerDeviceKind.stylus,
          },
        ),
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF0D1117),
          primaryColor: Colors.cyanAccent,
          colorScheme: const ColorScheme.dark(
            primary: Colors.cyanAccent,
            secondary: Colors.tealAccent,
            surface: Color(0xFF161B22),
          ),
          useMaterial3: true,
          fontFamily: '-apple-system',
        ),
        home: const HomeScreen(),
      ),
    );
  }
}
