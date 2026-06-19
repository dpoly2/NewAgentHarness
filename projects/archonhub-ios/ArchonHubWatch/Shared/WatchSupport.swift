/// WatchSupport.swift — Shared constants, theme, and utilities for the watchOS target.
///
/// This file mirrors the iOS AppSupport.swift and Models.swift declarations that the
/// Watch views depend on.  It is compiled ONLY into the Watch target (ArchonHubWatch).
/// Do NOT add this file to the iOS target — use the originals in ArchonHub/Shared/ instead.
///
/// When you add a new model, constant, or theme colour to the iOS side, mirror the
/// change here to keep both targets in sync.

import SwiftUI
import Foundation

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Project & Agent constants
// ─────────────────────────────────────────────────────────────────────────────

let ARCHON_PROJECTS = [
    "xftc", "yepc", "pbs-foundation", "s2tdesigns", "smithcap", "smithcap-finance",
    "ministry", "business-law", "social-media", "solar-repair", "sigma-signal",
    "nutrue", "the-elevation", "travel", "holdings", "markets", "nightking"
]

let QUICK_AGENTS = [
    "grants-research-agent", "finance-cfo", "social-project-lead",
    "markets-project-lead", "xftc-project-lead", "business-law-project-lead"
]

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Theme
// ─────────────────────────────────────────────────────────────────────────────

enum ArchonTheme {
    static let accent     = Color(hex: "#00B8FF")
    static let background = Color(hex: "#0B0F17")
    static let card       = Color(hex: "#111827")
    static let text       = Color(hex: "#D9E3F0")
    static let success    = Color(hex: "#22c55e")
    static let warning    = Color(hex: "#f59e0b")
    static let error      = Color(hex: "#ef4444")
    static let muted      = Color.white.opacity(0.55)

    static func statusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "running", "active", "online", "in_progress": return success
        case "queued", "pending":                           return warning
        case "failed", "error", "offline", "cancelled":    return error
        case "done", "completed", "success":                return accent
        default:                                            return muted
        }
    }

    static func priorityColor(_ priority: String) -> Color {
        switch priority.lowercased() {
        case "high", "urgent", "critical": return error
        case "medium", "normal":           return warning
        case "low":                        return accent
        default:                           return muted
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Color hex init
// ─────────────────────────────────────────────────────────────────────────────

extension Color {
    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)
        let a, r, g, b: UInt64
        switch cleaned.count {
        case 8:
            a = (value & 0xFF00_0000) >> 24
            r = (value & 0x00FF_0000) >> 16
            g = (value & 0x0000_FF00) >> 8
            b =  value & 0x0000_00FF
        default:
            a = 255
            r = (value & 0xFF0000) >> 16
            g = (value & 0x00FF00) >> 8
            b =  value & 0x0000FF
        }
        self.init(.sRGB,
                  red:     Double(r) / 255,
                  green:   Double(g) / 255,
                  blue:    Double(b) / 255,
                  opacity: Double(a) / 255)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - View modifier
// ─────────────────────────────────────────────────────────────────────────────

extension View {
    func archonCard(padding: CGFloat = 12) -> some View {
        self
            .padding(padding)
            .background(ArchonTheme.card)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Date formatter
// ─────────────────────────────────────────────────────────────────────────────

enum ArchonDateFormatter {
    private static let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
    private static let isoBasic: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    static func parse(_ string: String?) -> Date? {
        guard let s = string else { return nil }
        return iso.date(from: s) ?? isoBasic.date(from: s)
    }

    static func relativeString(_ string: String?) -> String {
        guard let date = parse(string) else { return "" }
        let delta = Date.now.timeIntervalSince(date)
        switch delta {
        case ..<60:        return "just now"
        case ..<3_600:     return "\(Int(delta / 60))m ago"
        case ..<86_400:    return "\(Int(delta / 3_600))h ago"
        default:           return "\(Int(delta / 86_400))d ago"
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Data models (Watch-side mirror of Models.swift)
// ─────────────────────────────────────────────────────────────────────────────

struct HealthResponse: Codable {
    let status: String
    let app: String
    let version: String
    let uptimeSeconds: Double
    let activeRuns: Int
    let queueDepth: Int
    let wsClients: Int
    let pendingTodos: Int
    let totalRuns: Int
    let llmProvider: String?
    let llmModel: String?

    static let empty = HealthResponse(
        status: "offline", app: "ArchonHub", version: "1.0.0",
        uptimeSeconds: 0, activeRuns: 0, queueDepth: 0,
        wsClients: 0, pendingTodos: 0, totalRuns: 0,
        llmProvider: nil, llmModel: nil
    )
}

struct AgentRun: Codable, Identifiable, Hashable {
    let id: Int
    let runId: String?
    let agentId: String
    let project: String
    let graph: String?
    let task: String
    let score: Double?
    let critique: String?
    let output: String?
    let status: String
    let createdAt: String?
    var stringId: String { "\(id)" }
}

struct Notification: Codable, Identifiable, Hashable {
    let id: Int
    let text: String
    let color: String?
    let category: String?
    let createdAt: String?
    let read: Bool
}

struct RunRequest: Codable {
    let agentId: String
    let project: String
    let graph: String?
    let task: String
    let maxRevisions: Int
    let priority: String
}

struct InezChatRequest: Codable {
    let message: String
    let conversationId: String?
}

struct InezDispatch: Codable, Identifiable, Hashable {
    var id: String { "\(agentId ?? "")|\(project ?? "")" }
    let agentId: String?
    let project: String?
    let graph: String?
    let task: String?
}

struct QueuedRun: Codable, Identifiable, Hashable {
    let runId: String
    let agentId: String
    let project: String
    var id: String { runId }
}

struct InezChatResponse: Codable {
    let conversationId: String?
    let inezMessage: String
    let dispatches: [InezDispatch]
    let needsAgents: Bool
    let queuedRuns: [QueuedRun]?
    let error: String?
}

struct InezMission: Codable, Identifiable, Hashable {
    var id: String { slug }
    let name: String
    let slug: String
    let status: String
}

struct InezStatusResponse: Codable {
    let awareness: String
    let urgentCount: Int
    let missions: [InezMission]
    let generatedAt: String?
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - HubClient (Watch)
// ─────────────────────────────────────────────────────────────────────────────
// Lightweight HubClient for watchOS — no WebSocket, no Combine publishers.
// Authentication tokens are received from the iOS companion via WatchConnectivity
// and stored in the Keychain.  The Watch always dials the Hub server directly.

final class HubClient: ObservableObject {
    static let shared = HubClient()

    @Published var isOnline: Bool = false

    private(set) var serverURL: String {
        didSet { UserDefaults.standard.set(serverURL, forKey: Keys.serverURL) }
    }
    private var token: String

    private enum Keys {
        static let serverURL   = "archonhub.serverURL"
        static let token       = "archonhub.token"
        static let activeRuns  = "archonhub.complication.activeRuns"
        static let pendingTodos = "archonhub.complication.pendingTodos"
    }

    private init() {
        self.serverURL = UserDefaults.standard.string(forKey: Keys.serverURL) ?? "https://app.archonhub.app"
        self.token     = KeychainWrapper.read(key: Keys.token) ?? ""
    }

    // Called by WatchTokenReceiver when the iOS companion sends a fresh token
    func setToken(_ value: String, persist: Bool = true) {
        token = value
        if persist { KeychainWrapper.save(value, key: Keys.token) }
    }

    var currentToken: String { token }

    // MARK: Public API

    func get<T: Decodable>(_ path: String) async throws -> T {
        try await request(path: path, method: "GET")
    }

    func post<T: Decodable, B: Encodable>(_ path: String, body: B) async throws -> T {
        try await request(path: path, method: "POST", body: body)
    }

    func checkHealth() async {
        do {
            let h: HealthResponse = try await get("/api/health")
            await MainActor.run {
                isOnline = h.status.lowercased() == "ok" || h.status.lowercased() == "online"
            }
            UserDefaults.standard.set(h.activeRuns,   forKey: Keys.activeRuns)
            UserDefaults.standard.set(h.pendingTodos, forKey: Keys.pendingTodos)
        } catch {
            await MainActor.run { isOnline = false }
        }
    }

    // MARK: Private

    private func request<T: Decodable>(path: String, method: String) async throws -> T {
        let data = try await requestData(path: path, method: method)
        return try decode(T.self, from: data, path: path)
    }

    private func request<T: Decodable, B: Encodable>(
        path: String, method: String, body: B
    ) async throws -> T {
        let data = try await requestData(path: path, method: method, body: body)
        return try decode(T.self, from: data, path: path)
    }

    private func decode<T: Decodable>(_ type: T.Type, from data: Data, path: String) throws -> T {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        do {
            return try decoder.decode(type, from: data)
        } catch {
            if let str = String(data: data, encoding: .utf8) {
                print("❌ Watch decode error at \(path): \(str.prefix(300))")
            }
            throw APIError.decoding
        }
    }

    private func requestData(path: String, method: String) async throws -> Data {
        let req = try buildRequest(path: path, method: method)
        return try await perform(req)
    }

    private func requestData<B: Encodable>(path: String, method: String, body: B) async throws -> Data {
        var req = try buildRequest(path: path, method: method)
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(body)
        return try await perform(req)
    }

    private func buildRequest(path: String, method: String) throws -> URLRequest {
        guard let url = buildURL(for: path) else { throw APIError.invalidURL }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = 15
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        if !token.isEmpty {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return req
    }

    private func buildURL(for path: String) -> URL? {
        if let abs = URL(string: path), abs.scheme != nil { return abs }
        guard var c = URLComponents(string: serverURL) else { return nil }
        if let q = path.firstIndex(of: "?") {
            c.path  = String(path[..<q])
            c.query = String(path[path.index(after: q)...])
        } else {
            c.path = path.hasPrefix("/") ? path : "/\(path)"
        }
        return c.url
    }

    private func perform(_ req: URLRequest) async throws -> Data {
        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            let msg = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"]
                ?? "HTTP \(http.statusCode)"
            throw APIError.server(msg)
        }
        return data
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - API errors
// ─────────────────────────────────────────────────────────────────────────────

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case decoding
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:      return "Invalid URL"
        case .invalidResponse: return "Invalid server response"
        case .decoding:        return "Failed to decode response"
        case .server(let m):   return m
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - Keychain wrapper (Watch-side)
// ─────────────────────────────────────────────────────────────────────────────

enum KeychainWrapper {
    static func save(_ value: String, key: String) {
        guard let data = value.data(using: .utf8) else { return }
        let query: [CFString: Any] = [
            kSecClass:       kSecClassGenericPassword,
            kSecAttrAccount: key as CFString,
        ]
        SecItemDelete(query as CFDictionary)
        var add = query
        add[kSecValueData] = data as CFData
        SecItemAdd(add as CFDictionary, nil)
    }

    static func read(key: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass:            kSecClassGenericPassword,
            kSecAttrAccount:      key as CFString,
            kSecReturnData:       true,
            kSecMatchLimit:       kSecMatchLimitOne,
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)
        guard let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete(key: String) {
        let query: [CFString: Any] = [
            kSecClass:       kSecClassGenericPassword,
            kSecAttrAccount: key as CFString,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
