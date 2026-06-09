import Foundation
import Combine
import Security

final class HubClient: ObservableObject {
    static let shared = HubClient()

    @Published var isOnline: Bool = false
    @Published var serverURL: String {
        didSet {
            UserDefaults.standard.set(serverURL, forKey: Keys.serverURL)
        }
    }

    private var token: String
    private var webSocketTask: URLSessionWebSocketTask?
    private var wsEventSubject = PassthroughSubject<WSEvent, Never>()
    var wsEvents: AnyPublisher<WSEvent, Never> { wsEventSubject.eraseToAnyPublisher() }

    private enum Keys {
        static let serverURL = "archonhub.serverURL"
        static let token = "archonhub.token"
        static let activeRuns = "archonhub.complication.activeRuns"
        static let pendingTodos = "archonhub.complication.pendingTodos"
    }

    private init() {
        self.serverURL = UserDefaults.standard.string(forKey: Keys.serverURL) ?? "http://localhost:8765"
        self.token = KeychainWrapper.read(key: Keys.token) ?? ""

        Task {
            await checkHealth()
            if !token.isEmpty {
                connectWebSocket()
            }
        }
    }

    func login(username: String, password: String) async throws -> LoginResponse {
        let response: LoginResponse = try await request(
            path: "/api/login",
            method: "POST",
            body: LoginRequest(username: username, password: password),
            requiresAuth: false
        )

        setToken(response.accessToken)
        await checkHealth()
        connectWebSocket()
        return response
    }

    func get<T: Decodable>(_ path: String) async throws -> T {
        try await request(path: path, method: "GET", requiresAuth: true)
    }

    func post<T: Decodable, B: Encodable>(_ path: String, body: B) async throws -> T {
        try await request(path: path, method: "POST", body: body, requiresAuth: true)
    }

    func put<T: Decodable, B: Encodable>(_ path: String, body: B) async throws -> T {
        try await request(path: path, method: "PUT", body: body, requiresAuth: true)
    }

    func delete(_ path: String) async throws {
        _ = try await requestData(path: path, method: "DELETE", requiresAuth: true)
    }

    func connectWebSocket() {
        guard webSocketTask == nil else { return }
        guard let url = makeWebSocketURL() else { return }

        var request = URLRequest(url: url)
        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let task = URLSession.shared.webSocketTask(with: request)
        webSocketTask = task
        task.resume()
        receiveWebSocketMessage()
    }

    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
    }

    func setToken(_ value: String, persist: Bool = true) {
        token = value
        if persist {
            KeychainWrapper.save(value, key: Keys.token)
        }
    }

    func clearToken() {
        token = ""
        KeychainWrapper.delete(key: Keys.token)
        disconnectWebSocket()
    }

    func checkHealth() async {
        do {
            let health: HealthResponse = try await request(path: "/api/health", method: "GET", requiresAuth: false)
            await MainActor.run {
                self.isOnline = health.status.lowercased() == "ok" || health.status.lowercased() == "online"
            }
            UserDefaults.standard.set(health.activeRuns, forKey: Keys.activeRuns)
            UserDefaults.standard.set(health.pendingTodos, forKey: Keys.pendingTodos)
        } catch {
            await MainActor.run {
                self.isOnline = false
            }
        }
    }

    private func request<T: Decodable>(
        path: String,
        method: String,
        requiresAuth: Bool
    ) async throws -> T {
        let data = try await requestData(path: path, method: method, requiresAuth: requiresAuth)

        if T.self == EmptyResponse.self, data.isEmpty {
            return EmptyResponse() as! T
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding
        }
    }

    private func request<T: Decodable, B: Encodable>(
        path: String,
        method: String,
        body: B,
        requiresAuth: Bool
    ) async throws -> T {
        let data = try await requestData(path: path, method: method, body: body, requiresAuth: requiresAuth)

        if T.self == EmptyResponse.self, data.isEmpty {
            return EmptyResponse() as! T
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding
        }
    }

    private func requestData<B: Encodable>(
        path: String,
        method: String,
        body: B,
        requiresAuth: Bool
    ) async throws -> Data {
        var request = try buildRequest(path: path, method: method, body: body, requiresAuth: requiresAuth)
        request.timeoutInterval = 20

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if !(200..<300).contains(httpResponse.statusCode) {
            let message = parseServerError(from: data) ?? "Request failed with status \(httpResponse.statusCode)."
            throw APIError.server(message)
        }

        return data
    }

    private func requestData(
        path: String,
        method: String,
        requiresAuth: Bool
    ) async throws -> Data {
        let request = try buildRequest(path: path, method: method, requiresAuth: requiresAuth)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if !(200..<300).contains(httpResponse.statusCode) {
            let message = parseServerError(from: data) ?? "Request failed with status \(httpResponse.statusCode)."
            throw APIError.server(message)
        }

        return data
    }

    private func buildRequest<B: Encodable>(
        path: String,
        method: String,
        body: B,
        requiresAuth: Bool
    ) throws -> URLRequest {
        guard let url = buildURL(for: path) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if requiresAuth, token.isEmpty {
            throw APIError.server("Please log in to continue.")
        }

        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        return request
    }

    private func buildRequest(
        path: String,
        method: String,
        requiresAuth: Bool
    ) throws -> URLRequest {
        guard let url = buildURL(for: path) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if requiresAuth, token.isEmpty {
            throw APIError.server("Please log in to continue.")
        }

        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return request
    }

    private func buildURL(for path: String) -> URL? {
        if let absolute = URL(string: path), absolute.scheme != nil {
            return absolute
        }

        guard var components = URLComponents(string: serverURL) else {
            return nil
        }

        components.path = path.hasPrefix("/") ? path : "/\(path)"
        return components.url
    }

    private func makeWebSocketURL() -> URL? {
        guard var components = URLComponents(string: serverURL) else {
            return nil
        }

        components.scheme = components.scheme == "https" ? "wss" : "ws"
        components.path = "/ws"
        return components.url
    }

    private func receiveWebSocketMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self else { return }

            switch result {
            case .success(let message):
                let payload: String
                switch message {
                case .string(let string):
                    payload = string
                case .data(let data):
                    payload = String(decoding: data, as: UTF8.self)
                @unknown default:
                    payload = ""
                }

                if let data = payload.data(using: .utf8),
                   let event = try? self.decoder.decode(WSEvent.self, from: data) {
                    self.wsEventSubject.send(event)
                } else {
                    self.wsEventSubject.send(WSEvent(type: "message", runId: nil, text: payload, color: nil, data: nil))
                }

                self.receiveWebSocketMessage()
            case .failure:
                DispatchQueue.main.async {
                    self.isOnline = false
                }
                self.webSocketTask = nil
            }
        }
    }

    private func parseServerError(from data: Data) -> String? {
        struct ErrorPayload: Decodable {
            let detail: String?
            let message: String?
        }

        if let payload = try? decoder.decode(ErrorPayload.self, from: data) {
            return payload.detail ?? payload.message
        }

        if let string = String(data: data, encoding: .utf8), !string.isEmpty {
            return string
        }

        return nil
    }

    private var encoder: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }
}

private enum KeychainWrapper {
    static func save(_ value: String, key: String) {
        guard let data = value.data(using: .utf8) else { return }

        delete(key: key)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        SecItemAdd(query as CFDictionary, nil)
    }

    static func read(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess,
              let data = item as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }

        return value
    }

    static func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
