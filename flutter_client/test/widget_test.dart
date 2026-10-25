import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_client/main.dart';

void main() {
  testWidgets('LeanMultimodalApp bootstrap smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LeanMultimodalApp());
    expect(find.text('LEAN MULTIMODAL PLATFORM'), findsOneWidget);
  });
}
