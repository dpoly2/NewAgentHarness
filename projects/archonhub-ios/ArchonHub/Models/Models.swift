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

// MARK: - Email Cleanup Models

struct EmailCleanupPlan: Codable, Identifiable, Hashable {
    let id: String
    let accountId: String
    let status: String  // pending, approved, executed, rolled_back
    let totalEmails: Int
    let suggestedCleanupCount: Int
    let estimatedSpaceMb: Int
    let createdAt: String
    let executedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case accountId = "account_id"
        case status
        case totalEmails = "total_emails"
        case suggestedCleanupCount = "suggested_cleanup_count"
        case estimatedSpaceMb = "estimated_space_mb"
        case createdAt = "created_at"
        case executedAt = "executed_at"
    }
}

struct EmailCleanupItem: Codable, Identifiable, Hashable {
    let id: String
    let planId: String
    let emailId: String
    let category: String
    let subject: String
    let fromAddress: String
    let emailDate: String
    let sizeBytes: Int
    let confidence: Double
    let reason: String
    let approved: Bool
    let executed: Bool
    let action: String
    let executedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case planId = "plan_id"
        case emailId = "email_id"
        case category
        case subject
        case fromAddress = "from_address"
        case emailDate = "email_date"
        case sizeBytes = "size_bytes"
        case confidence
        case reason
        case approved
        case executed
        case action
        case executedAt = "executed_at"
    }
    
    var categoryIcon: String {
        switch category {
        case "newsletter": return "envelope.badge"
        case "promotion": return "cart"
        case "social": return "person.2"
        case "old_thread": return "clock"
        case "spam": return "trash"
        default: return "envelope"
        }
    }
    
    var categoryColor: String {
        switch category {
        case "newsletter": return "blue"
        case "promotion": return "purple"
        case "social": return "green"
        case "old_thread": return "orange"
        case "spam": return "red"
        default: return "gray"
        }
    }
}

struct EmailCleanupPlanDetail: Codable {
    let plan: EmailCleanupPlan
    let items: [EmailCleanupItem]
    let categories: [String: [EmailCleanupItem]]
}

struct EmailCleanupSummary: Codable {
    let totalSuggested: Int
    let estimatedSpaceMb: Double
    let breakdown: [String: Int]
    
    enum CodingKeys: String, CodingKey {
        case totalSuggested = "total_suggested"
        case estimatedSpaceMb = "estimated_space_mb"
        case breakdown
    }
}

struct AnalyzeEmailResponse: Codable {
    let success: Bool
    let planId: String
    let summary: EmailCleanupSummary
    
    enum CodingKeys: String, CodingKey {
        case success
        case planId = "plan_id"
        case summary
    }
}

struct EmailCleanupExecuteResponse: Codable {
    let success: Bool
    let results: EmailCleanupResults
    let message: String
}

struct EmailCleanupResults: Codable {
    let total: Int
    let archived: Int
    let deleted: Int
    let errors: Int
    let spaceRecoveredMb: Double
    
    enum CodingKeys: String, CodingKey {
        case total, archived, deleted, errors
        case spaceRecoveredMb = "space_recovered_mb"
    }
}
