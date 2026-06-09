import Foundation
import Combine

@MainActor
final class AuthStore: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var username: String = ""
    @Published var role: String = "user"

    private enum Keys {
        static let token = "archonhub.auth.token"
        static let username = "archonhub.auth.username"
        static let role = "archonhub.auth.role"
    }

    init() {
        loadSavedToken()
    }

    func login(username: String, password: String) async throws {
        let response = try await HubClient.shared.login(username: username, password: password)
        self.username = username
        self.role = username.lowercased() == "admin" ? "admin" : "user"
        self.isAuthenticated = !response.accessToken.isEmpty

        UserDefaults.standard.set(response.accessToken, forKey: Keys.token)
        UserDefaults.standard.set(username, forKey: Keys.username)
        UserDefaults.standard.set(role, forKey: Keys.role)
    }

    func logout() {
        isAuthenticated = false
        username = ""
        role = "user"

        UserDefaults.standard.removeObject(forKey: Keys.token)
        UserDefaults.standard.removeObject(forKey: Keys.username)
        UserDefaults.standard.removeObject(forKey: Keys.role)

        HubClient.shared.clearToken()
    }

    func loadSavedToken() {
        let savedToken = UserDefaults.standard.string(forKey: Keys.token) ?? ""
        username = UserDefaults.standard.string(forKey: Keys.username) ?? ""
        role = UserDefaults.standard.string(forKey: Keys.role) ?? "user"
        isAuthenticated = !savedToken.isEmpty

        if !savedToken.isEmpty {
            HubClient.shared.setToken(savedToken)
        }
    }
}
