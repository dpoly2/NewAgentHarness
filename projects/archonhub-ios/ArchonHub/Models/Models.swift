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
    let id: Int  // Changed from String - server returns integer
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
    
    // Conform to Identifiable with String id
    var stringId: String { "\(id)" }
}

struct Todo: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let description: String?
    let priority: String?  // Changed to optional - can be null
    let status: String
    let project: String?
    let dueDate: String?
    let tags: [String]?
    let createdAt: String?
}

struct Automation: Codable, Identifiable, Hashable {
    let id: String
    let slug: String
    let name: String
    let description: String?
    let projectSlug: String?
    let agentId: String?
    let triggerType: String?
    let status: String?
    let lastRunAt: String?
    let lastRunStatus: String?
}

struct DailyBrief: Hashable {
    let id: String
    let content: String
    let createdAt: String?
}

extension DailyBrief: Codable {
    private enum CodingKeys: String, CodingKey { case id, content, createdAt }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        // Generate ID if not provided by server
        id = (try? c.decode(String.self, forKey: .id)) ?? UUID().uuidString
        createdAt = try c.decodeIfPresent(String.self, forKey: .createdAt)
        if let str = try? c.decode(String.self, forKey: .content) {
            content = str
        } else if let json = try? c.decode(JSONValue.self, forKey: .content) {
            content = json.displayText
        } else {
            content = ""
        }
    }
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
    let id: Int
    let text: String
    let color: String?
    let category: String?
    let createdAt: String?
    let read: Bool
}

struct Report: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let reportType: String
    let content: String
    let summary: String
    let projectSlug: String?
    let generatedBy: String?
    let jobId: String?
    let status: String
    let generatedAt: String?
    let createdAt: String?
}

struct Document: Codable, Identifiable {
    let id: String
    let title: String
    let docType: String
    let content: String
    let format: String
    let projectSlug: String?
    let clientId: String?
    let tags: [String]?
    let createdBy: String?
    let version: Int
    let status: String
    let createdAt: String
    let updatedAt: String
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
    var id: String { "\(agentId ?? "")|\(project ?? "")" }
    let agentId: String?
    let project: String?
    let graph: String?
    let task: String?
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

struct InezChatResponse: Codable {
    let conversationId: String?
    let inezMessage: String
    let dispatches: [InezDispatch]
    let needsAgents: Bool
    let queuedRuns: [QueuedRun]?
    let error: String?
    let followupSuggestions: [String]?
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

struct LoginUser: Codable {
    let username: String
    let role: String
}

struct LoginResponse: Codable {
    let accessToken: String
    let tokenType: String
    let user: LoginUser?
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

// MARK: - Prompt Templates

struct PromptTemplate: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let category: String
    let promptText: String
    let agentId: String
    let projectSlug: String
    let isSystem: Bool
    let usageCount: Int
    let createdAt: String?
    let updatedAt: String?
}
