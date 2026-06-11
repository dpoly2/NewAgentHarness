import SwiftUI
import WatchKit
import WatchConnectivity

@main
struct ArchonHubWatchApp: App {
    init() {
        _ = WatchTokenReceiver.shared
    }

    var body: some Scene {
        WindowGroup {
            WatchMainView()
        }
    }
}

final class WatchTokenReceiver: NSObject, WCSessionDelegate {
    static let shared = WatchTokenReceiver()

    private override init() {
        super.init()
        guard WCSession.isSupported() else { return }
        WCSession.default.delegate = self
        WCSession.default.activate()
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        // Apply any token that was already in context before this activation
        if let token = session.receivedApplicationContext["authToken"] as? String {
            DispatchQueue.main.async { HubClient.shared.setToken(token, persist: false) }
        }
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        if let token = applicationContext["authToken"] as? String {
            DispatchQueue.main.async { HubClient.shared.setToken(token, persist: false) }
        }
    }
}
