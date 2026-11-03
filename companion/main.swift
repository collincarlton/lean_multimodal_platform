import Cocoa
import WebKit
import AVFoundation
import Carbon

// Global Carbon HotKey Handler
func carbonHotKeyHandler(nextHandler: EventHandlerCallRef?, theEvent: EventRef?, userData: UnsafeMutableRawPointer?) -> OSStatus {
    guard let theEvent = theEvent else { return noErr }
    var hotKeyID = EventHotKeyID()
    let status = GetEventParameter(
        theEvent,
        EventParamName(kEventParamDirectObject),
        EventParamType(typeEventHotKeyID),
        nil,
        MemoryLayout<EventHotKeyID>.size,
        nil,
        &hotKeyID
    )
    
    if status == noErr && hotKeyID.signature == OSType(0x4C45414E) { // 'LEAN'
        let eventKind = GetEventKind(theEvent)
        if eventKind == UInt32(kEventHotKeyPressed) {
            DispatchQueue.main.async {
                StatusPopoverController.shared?.handleHotKeyDown()
            }
        } else if eventKind == UInt32(kEventHotKeyReleased) {
            DispatchQueue.main.async {
                StatusPopoverController.shared?.handleHotKeyUp()
            }
        }
    }
    return noErr
}

class FloatingHUDPanel: NSPanel {
    init(contentRect: NSRect) {
        super.init(
            contentRect: contentRect,
            styleMask: [.nonactivatingPanel, .titled, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        self.level = .floating
        self.isOpaque = false
        self.backgroundColor = .clear
        self.hasShadow = true
        self.titleVisibility = .hidden
        self.titlebarAppearsTransparent = true
        self.isMovableByWindowBackground = true
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
    }
}

class StatusPopoverController: NSObject, NSApplicationDelegate, WKUIDelegate, WKNavigationDelegate {
    static var shared: StatusPopoverController?
    var statusItem: NSStatusItem!
    var popover: NSPopover?
    var hudPanel: FloatingHUDPanel!
    var webView: WKWebView!
    var hotKeyRef: EventHotKeyRef?
    var pressHandlerRef: EventHandlerRef?
    var releaseHandlerRef: EventHandlerRef?

    // DUAL-ACTION TIMING & HARDWARE POLLER STATE
    private var pressStartTime: Date?
    private var isRecording = false
    private var holdThresholdTimer: Timer?
    private var hardwarePollerTimer: Timer?
    private let holdThresholdSeconds: TimeInterval = 0.25
    private let popoverWidth: CGFloat = 480
    private let popoverHeight: CGFloat = 680
    private let gatewayURLString = "http://127.0.0.1:5050"

    func applicationDidFinishLaunching(_ notification: Notification) {
        StatusPopoverController.shared = self
        enforceSingleInstance()

        let contentRect = NSRect(x: 0, y: 0, width: popoverWidth, height: popoverHeight)

        // 1. Hardware Accelerated WebKit Configuration
        let config = WKWebViewConfiguration()
        config.mediaTypesRequiringUserActionForPlayback = []
        let prefs = WKWebpagePreferences()
        prefs.allowsContentJavaScript = true
        config.defaultWebpagePreferences = prefs
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")
        config.preferences.setValue(true, forKey: "mediaDevicesEnabled")
        config.preferences.setValue(true, forKey: "mediaStreamEnabled")

        // 2. Instantiate WebView as DIRECT Responder (Unblocked Mouse Hit-Testing)
        webView = WKWebView(frame: contentRect, configuration: config)
        webView.autoresizingMask = [.width, .height]
        webView.uiDelegate = self
        webView.navigationDelegate = self
        if #available(macOS 13.3, *) {
            webView.isInspectable = true
        }

        // 3. Direct View Controller Assignment - Zero Intermediate Hit-Test Blockers
        let viewController = NSViewController()
        viewController.view = webView

        // 4. Build Native Floating HUD Panel (C-01: <20MB RSS)
        hudPanel = FloatingHUDPanel(contentRect: contentRect)
        hudPanel.contentViewController = viewController

        // 5. Mount Menu Bar Status Item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.title = "⚡Lean"
            button.action = #selector(togglePopover(_:))
            button.target = self
        }

        // 6. Install Carbon Chords & Hardware Poller
        installCarbonDualActionHotKey()

        // 7. Assert Hardware Microphone Grants
        verifyMicrophoneHardware()

        // 8. Load Gateway via Direct IPv4
        loadGatewayURL()
    }

    private func enforceSingleInstance() {
        let currentPID = ProcessInfo.processInfo.processIdentifier
        let bundleID = Bundle.main.bundleIdentifier ?? "com.leancloud.companion"
        for app in NSRunningApplication.runningApplications(withBundleIdentifier: bundleID) {
            if app.processIdentifier != currentPID {
                print("[SingleInstance] Terminating duplicate PID \(app.processIdentifier)")
                app.forceTerminate()
            }
        }
    }

    func loadGatewayURL() {
        if let url = URL(string: gatewayURLString) {
            print("[WebKit] Loading: \(url.absoluteString)...")
            let req = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 60.0)
            webView.load(req)
        }
    }

    private func installCarbonDualActionHotKey() {
        let dispatcher = GetEventDispatcherTarget()
        let appTarget = GetApplicationEventTarget()

        var pressSpec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        var releaseSpec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyReleased))

        InstallEventHandler(dispatcher, carbonHotKeyHandler, 1, &pressSpec, nil, &pressHandlerRef)
        InstallEventHandler(dispatcher, carbonHotKeyHandler, 1, &releaseSpec, nil, &releaseHandlerRef)
        InstallEventHandler(appTarget, carbonHotKeyHandler, 1, &pressSpec, nil, nil)
        InstallEventHandler(appTarget, carbonHotKeyHandler, 1, &releaseSpec, nil, nil)

        let hotKeyID = EventHotKeyID(signature: OSType(0x4C45414E), id: 1)
        let modifiers = UInt32(cmdKey | controlKey | optionKey)
        let kVK_Space: UInt32 = 0x31

        let status = RegisterEventHotKey(kVK_Space, modifiers, hotKeyID, dispatcher, 0, &hotKeyRef)
        if status == noErr {
            print("[Carbon] Dual-Action Hotkey registered successfully.")
        } else {
            print("[Carbon] Hotkey registration failed: \(status)")
        }
    }

    // STATE MACHINE: KEY DOWN
    func handleHotKeyDown() {
        guard pressStartTime == nil else { return }
        pressStartTime = Date()
        isRecording = false

        holdThresholdTimer?.invalidate()
        holdThresholdTimer = Timer.scheduledTimer(withTimeInterval: holdThresholdSeconds, repeats: false) { [weak self] _ in
            guard let self = self, self.pressStartTime != nil else { return }
            self.isRecording = true
            print("[DualAction] HOLD boundary reached (250ms). Activating acoustic stream...")
            DispatchQueue.main.async {
                self.statusItem.button?.title = "🔴Rec"
                self.showPopover()
                self.dispatchRecordStart()
            }
        }

        hardwarePollerTimer?.invalidate()
        hardwarePollerTimer = Timer.scheduledTimer(withTimeInterval: 0.025, repeats: true) { [weak self] timer in
            guard let self = self else {
                timer.invalidate()
                return
            }
            let spaceDown = CGEventSource.keyState(.combinedSessionState, key: CGKeyCode(0x31))
            let flags = NSEvent.modifierFlags.intersection(.deviceIndependentFlagsMask)
            let chordHeld = spaceDown && flags.contains(.command) && flags.contains(.control) && flags.contains(.option)

            if !chordHeld {
                timer.invalidate()
                self.hardwarePollerTimer = nil
                self.handleHotKeyUp()
            }
        }
    }

    // STATE MACHINE: KEY UP
    func handleHotKeyUp() {
        guard let start = pressStartTime else { return }
        pressStartTime = nil
        holdThresholdTimer?.invalidate()
        holdThresholdTimer = nil
        hardwarePollerTimer?.invalidate()
        hardwarePollerTimer = nil

        let elapsed = Date().timeIntervalSince(start)

        if isRecording {
            print("[DualAction] RELEASE detected after HOLD (\(String(format: "%.2f", elapsed))s). Stopping stream...")
            isRecording = false
            DispatchQueue.main.async {
                self.statusItem.button?.title = "⚡Lean"
                self.dispatchRecordStop()
            }
        } else {
            print("[DualAction] TAP detected (\(String(format: "%.2f", elapsed))s). Toggling Portal Window...")
            DispatchQueue.main.async {
                self.statusItem.button?.title = "⚡Lean"
                self.togglePopover(nil)
            }
        }
    }

    // Canonical, non-destructive event dispatch (zero semantics tampering, zero fake pointerdown)
    private func dispatchRecordStart() {
        let js = """
        (function() {
            window.dispatchEvent(new CustomEvent('lean:record-start'));
            if (typeof window.leanStartRecording === 'function') {
                window.leanStartRecording();
            }
        })();
        """
        webView.evaluateJavaScript(js, completionHandler: nil)
    }

    private func dispatchRecordStop() {
        let js = """
        (function() {
            window.dispatchEvent(new CustomEvent('lean:record-stop'));
            if (typeof window.leanStopRecording === 'function') {
                window.leanStopRecording();
            }
        })();
        """
        webView.evaluateJavaScript(js, completionHandler: nil)
    }

    func showPopover() {
        showHUD()
    }

    func showHUD() {
        guard let button = statusItem.button else { return }
        if let panel = hudPanel {
            if !panel.isVisible {
                let buttonFrame = button.window?.convertToScreen(button.frame) ?? NSRect.zero
                let panelX = buttonFrame.midX - (popoverWidth / 2)
                let panelY = buttonFrame.minY - popoverHeight - 4
                panel.setFrameOrigin(NSPoint(x: panelX, y: panelY))
                panel.makeKeyAndOrderFront(nil)
            }
        }
    }

    @objc func togglePopover(_ sender: AnyObject?) {
        guard statusItem.button != nil else { return }
        if let panel = hudPanel, panel.isVisible {
            panel.orderOut(sender)
        } else {
            showHUD()
        }
    }

    private func verifyMicrophoneHardware() {
        let status = AVCaptureDevice.authorizationStatus(for: .audio)
        switch status {
        case .authorized:
            NSApp.setActivationPolicy(.accessory)
        case .notDetermined:
            NSApp.setActivationPolicy(.regular)
            NSApp.activate(ignoringOtherApps: true)
            AVCaptureDevice.requestAccess(for: .audio) { [weak self] granted in
                DispatchQueue.main.async {
                    NSApp.setActivationPolicy(.accessory)
                    if granted { self?.loadGatewayURL() }
                }
            }
        case .denied, .restricted:
            NSApp.setActivationPolicy(.accessory)
            // Idempotent TCC repair hook (G-01)
            let resetProcess = Process()
            resetProcess.executableURL = URL(fileURLWithPath: "/usr/bin/tccutil")
            resetProcess.arguments = ["reset", "Microphone", "com.leancloud.companion"]
            try? resetProcess.run()
            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone") {
                NSWorkspace.shared.open(url)
            }
        @unknown default:
            NSApp.setActivationPolicy(.accessory)
            break
        }
    }

    func webView(_ webView: WKWebView,
                 requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo,
                 type: WKMediaCaptureType,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        decisionHandler(.grant)
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        print("[WebKit] didFailProvisionalNavigation: \(error.localizedDescription)")
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("[WebKit] Navigation SUCCESS: Flutter Web surface mounted.")
    }
}

let app = NSApplication.shared
let delegate = StatusPopoverController()
app.delegate = delegate
app.run()
