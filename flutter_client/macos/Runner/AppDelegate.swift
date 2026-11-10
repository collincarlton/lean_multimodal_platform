import Cocoa
import FlutterMacOS

@main
class AppDelegate: FlutterAppDelegate {
    override func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false
    }

    override func applicationDidFinishLaunching(_ notification: Notification) {
        if let window = mainFlutterWindow,
           let controller = window.contentViewController as? FlutterViewController {
            HUDPlugin.register(with: controller.registrar(forPlugin: "HUDPlugin"))
        }
        super.applicationDidFinishLaunching(notification)
    }
}
