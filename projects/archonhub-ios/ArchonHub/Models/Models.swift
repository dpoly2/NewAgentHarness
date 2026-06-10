import Foundation

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
        status: "offline",
        app: "ArchonHub",
        version: "1.0.0",
        uptimeSeconds: 0,
        activeRuns: 0,
        queueDepth: 0,
        wsClients: 0,
        pendingTodos: 0,
        totalRuns: 0,
        llmProvider: nil,
        llmModel: nil
    )
}

struct AgentRun: Codable, Identifiable, Hashable {
    let id: String
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
}

struct Todo: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let description: String?
    let priority: String
    let status: String
    let project: String?
    let dueDate: String?
    let tags: [String]?
    let createdAt: String?
}

struct DailyBrief: Codable, Hashable {
    let id: String
    let content: String
    let createdAt: String?
}

struct SchedulerJob: Codable, Identifiable, Hashable {
    let id: String
    let agentId: String
    let project: String
    let graph: String?
    let task: String
    let runType: String
    let cronExpr: String?
    let nextFire: String?
    let status: String
}

struct Client: Codable, Identifiable, Hashable {
    let id: String
    let slug: String
    let name: String
    let businessType: String?
    let service: String?
    let contactName: String?
    let contactEmail: String?
    let status: String
}

struct Project: Codable, Identifiable, Hashable {
    let id: String
    let slug: String
    let name: String
    let description: String?
    let status: String
    let leadAgent: String?
}

struct Notification: Codable, Identifiable, Hashable {
    let id: String
    let text: String
    let color: String?
    let category: String?
    let createdAt: String?
    let read: Bool
}

struct Conversation: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let slug: String?
    let createdAt: String?
}

struct Message: Codable, Identifiable, Hashable {
    let id: String
    let conversationId: String
    let role: String
    let content: String
    let agentId: String?
    let createdAt: String?
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
    var id: String { (agentId ?? "") + (project ?? "") }
    let agentId: String?
    let project: String?
    let graph: String?
    let task: String?
}

struct InezChatResponse: Codable {
    let conversationId: String?
    let inezMessage: String
    let dispatches: [InezDispatch]
    let needsAgents: Bool
    let queuedRuns: [QueuedRun]?
    let error: String?
}

struct QueuedRun: Codable, Identifiable, Hashable {
    let runId: String
    let agentId: String
    let project: String
    var id: String { runId }
}

struct LoginRequest: Codable {
    let username: String
    let password: String
}

struct LoginResponse: Codable {
    let accessToken: String
    let tokenType: String
}

struct WSEvent: Codable, Hashable {
    let type: String
    let runId: String?
    let text: String?
    let color: String?
    let data: [String: JSONValue]?
}

enum JSONValue: Codable, Hashable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            throw APIError.decoding
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .number(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        case .object(let value):
            try container.encode(value)
        case .array(let value):
            try container.encode(value)
        case .null:
            try container.encodeNil()
        }
    }
}

struct HubConfig: Codable, Hashable {
    let values: [String: String]

    init(values: [String: String]) {
        self.values = values
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        self.values = try container.decode([String: String].self)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(values)
    }

    subscript(key: String) -> String? {
        values[key]
    }
}
