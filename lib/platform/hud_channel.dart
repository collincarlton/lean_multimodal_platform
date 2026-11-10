import 'package:flutter/services.dart';

class HUDPlatformChannel {
  static const MethodChannel _channel = MethodChannel('com.lunora.desktop/floating_hud');

  static Future<void> showHUD() async {
    try {
      await _channel.invokeMethod('showHUD');
    } on PlatformException {
      // Platform channel not registered or non-macOS environment
    }
  }

  static Future<void> hideHUD() async {
    try {
      await _channel.invokeMethod('hideHUD');
    } on PlatformException {
      // Platform channel not registered or non-macOS environment
    }
  }

  static Future<void> updateHUDState({
    required bool gatewayOnline,
    required double memoryUsageMb,
    required int activeCacheTokens,
    required String activeModel,
    required double rpmRemaining,
  }) async {
    try {
      await _channel.invokeMethod('updateHUDState', {
        'gatewayOnline': gatewayOnline,
        'memoryUsageMb': memoryUsageMb,
        'activeCacheTokens': activeCacheTokens,
        'activeModel': activeModel,
        'rpmRemaining': rpmRemaining,
      });
    } on PlatformException {
      // Platform channel not registered or non-macOS environment
    }
  }
}
