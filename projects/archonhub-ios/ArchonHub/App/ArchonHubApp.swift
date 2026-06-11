import SwiftUI
import WatchConnectivity

@main
struct ArchonHubApp: App {
    @StateObject private var authStore = AuthStore()
    @StateObject private var hubClient = HubClient.shared

    init() {
        _ = WatchSessionCoordinator.shared
    }

    var body: some Scene {
        WindowGroup {
            Group {
                if authStore.isAuthenticated {
                    ContentView()
                        .environmentObject(authStore)
                        .environmentObject(hubClient)
                } else {
                    LoginView()
                        .environmentObject(authStore)
                }
            }
            .preferredColorScheme(.dark)
            .onChange(of: authStore.isAuthenticated) { _, isAuth in
                WatchSessionCoordinator.shared.sendToken(
                    isAuth ? HubClient.shared.currentToken : ""
                )
            }
        }
    }
}

final class WatchSessionCoordinator: NSObject, WCSessionDelegate {
    static let shared = WatchSessionCoordinator()

    private override init() {
        super.init()
        guard WCSession.isSupported() else { return }
        WCSession.default.delegate = self
        WCSession.default.activate()
    }

    func sendToken(_ token: String) {
        guard WCSession.default.activationState == .activated,
              WCSession.default.isPaired,
              WCSession.default.isWatchAppInstalled else { return }
        try? WCSession.default.updateApplicationContext(["authToken": token])
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) { WCSession.default.activate() }
}
