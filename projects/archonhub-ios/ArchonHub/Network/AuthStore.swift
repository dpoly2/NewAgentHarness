import Foundation
import Combine

@MainActor
final class AuthStore: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var username: String = ""
    @Published var role: String = "user"

    private enum Keys {
        static let username = "archonhub.auth.username"
        static let role = "archonhub.auth.role"
    }

    init() {
        loadSavedSession()
    }

    func login(username: String, password: String) async throws {
        let response = try await HubClient.shared.login(username: username, password: password)
        self.username = username
        self.role = response.user?.role ?? "user"
        self.isAuthenticated = true
        UserDefaults.standard.set(username, forKey: Keys.username)
        UserDefaults.standard.set(self.role, forKey: Keys.role)
    }

    func logout() {
        isAuthenticated = false
        username = ""
        role = "user"
        UserDefaults.standard.removeObject(forKey: Keys.username)
        UserDefaults.standard.removeObject(forKey: Keys.role)
        HubClient.shared.clearToken()
    }

    private func loadSavedSession() {
        // Token is already loaded from Keychain by HubClient.init()
        isAuthenticated = !HubClient.shared.currentToken.isEmpty
        if isAuthenticated {
            username = UserDefaults.standard.string(forKey: Keys.username) ?? ""
            role = UserDefaults.standard.string(forKey: Keys.role) ?? "user"
        }
    }
}
