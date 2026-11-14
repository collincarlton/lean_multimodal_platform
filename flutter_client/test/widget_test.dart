import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_client/main.dart';

void main() {
  testWidgets('LeanPortalApp bootstrap smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LeanPortalApp());
    expect(find.text('SOVEREIGN 5.0'), findsOneWidget);
  });
}
