import Cocoa
import FlutterMacOS

public class FloatingHUDPanel: NSPanel {
    private var visualEffectView: NSVisualEffectView!
    private var titleLabel: NSTextField!
    private var telemetryLabel: NSTextField!

    public init(contentRect: NSRect) {
        super.init(
            contentRect: contentRect,
            styleMask: [.nonactivatingPanel, .titled, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        self.isFloatingPanel = true
        self.level = .floating
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        self.titleVisibility = .hidden
        self.titlebarAppearsTransparent = true
        self.isMovableByWindowBackground = true
        self.backgroundColor = .clear
        self.isOpaque = false
        self.hasShadow = true

        setupViewHierarchy(rect: contentRect)
    }

    private func setupViewHierarchy(rect: NSRect) {
        visualEffectView = NSVisualEffectView(frame: rect)
        visualEffectView.material = .hudWindow
        visualEffectView.state = .active
        visualEffectView.blendingMode = .behindWindow
        visualEffectView.wantsLayer = true
        visualEffectView.layer?.cornerRadius = 12.0
        visualEffectView.layer?.masksToBounds = true

        titleLabel = NSTextField(labelWithString: "LUNORA SOVEREIGN HUD")
        titleLabel.frame = NSRect(x: 16, y: rect.height - 30, width: rect.width - 32, height: 18)
        titleLabel.font = NSFont.monospacedSystemFont(ofSize: 11, weight: .bold)
        titleLabel.textColor = NSColor.systemTeal

        telemetryLabel = NSTextField(labelWithString: "GATEWAY: INITIALIZING\nCACHE: 0 TOKENS\nRPM: 15/15")
        telemetryLabel.frame = NSRect(x: 16, y: 12, width: rect.width - 32, height: rect.height - 48)
        telemetryLabel.font = NSFont.monospacedSystemFont(ofSize: 10, weight: .regular)
        telemetryLabel.textColor = NSColor.white
        telemetryLabel.maximumNumberOfLines = 4

        visualEffectView.addSubview(titleLabel)
        visualEffectView.addSubview(telemetryLabel)
        self.contentView = visualEffectView
    }

    public func updateTelemetry(online: Bool, memoryMb: Double, tokens: Int, model: String, rpm: Double) {
        DispatchQueue.main.async {
            let statusStr = online ? "ONLINE" : "OFFLINE"
            self.telemetryLabel.stringValue = """
STATUS : \(statusStr) (RSS: \(String(format: "%.1f", memoryMb)) MB)
MODEL  : \(model)
CACHE  : \(tokens) Tokens
RATE   : \(String(format: "%.1f", rpm))/15 RPM
"""
        }
    }
}

public class HUDPlugin: NSObject, FlutterPlugin {
    private var hudPanel: FloatingHUDPanel?

    public static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(
            name: "com.lunora.desktop/floating_hud",
            binaryMessenger: registrar.messenger
        )
        let instance = HUDPlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
    }

    public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "showHUD":
            if hudPanel == nil {
                let rect = NSRect(x: 40, y: 40, width: 280, height: 100)
                hudPanel = FloatingHUDPanel(contentRect: rect)
            }
            hudPanel?.orderFront(nil)
            result(nil)

        case "hideHUD":
            hudPanel?.orderOut(nil)
            result(nil)

        case "updateHUDState":
            guard let args = call.arguments as? [String: Any] else {
                result(FlutterError(code: "INVALID_ARGS", message: "Arguments must be a Map", details: nil))
                return
            }
            let online = args["gatewayOnline"] as? Bool ?? false
            let memoryMb = args["memoryUsageMb"] as? Double ?? 0.0
            let tokens = args["activeCacheTokens"] as? Int ?? 0
            let model = args["activeModel"] as? String ?? "unknown"
            let rpm = args["rpmRemaining"] as? Double ?? 15.0

            hudPanel?.updateTelemetry(online: online, memoryMb: memoryMb, tokens: tokens, model: model, rpm: rpm)
            result(nil)

        default:
            result(FlutterMethodNotImplemented)
        }
    }
}
