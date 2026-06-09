import SwiftUI

@main
struct ArchonHubApp: App {
    @StateObject private var authStore = AuthStore()
    @StateObject private var hubClient = HubClient.shared

    var body: some Scene {
        WindowGroup {
            if authStore.isAuthenticated {
                ContentView()
                    .environmentObject(authStore)
                    .environmentObject(hubClient)
                    .preferredColorScheme(.dark)
            } else {
                LoginView()
                    .environmentObject(authStore)
                    .preferredColorScheme(.dark)
            }
        }
    }
}
