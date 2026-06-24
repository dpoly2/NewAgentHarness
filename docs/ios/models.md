# iOS Models

Expanded compact reference for `Models.swift` and the payloads most often consumed by the SwiftUI app.

## Why these models matter

- They define the decode expectations for `HubClient`.
- They document where the Swift app expects optional/null values.
- They reveal naming mismatches the backend must preserve for compatibility.

## Core app contracts

| Model | Line | Field contract |
| --- | --- | --- |
| HealthResponse | 3 | status: String<br>app: String<br>version: String<br>uptimeSeconds: Double<br>activeRuns: Int<br>queueDepth: Int<br>wsClients: Int<br>pendingTodos: Int<br>totalRuns: Int<br>llmProvider: String? |
| AgentRun | 31 | id: Int<br>runId: String?<br>agentId: String<br>project: String<br>graph: String?<br>task: String<br>score: Double?<br>critique: String?<br>output: String?<br>status: String |
| Todo | 48 | id: String<br>title: String<br>description: String?<br>priority: String?<br>status: String<br>project: String?<br>dueDate: String?<br>tags: [String]?<br>createdAt: String? |
| Automation | 60 | id: String<br>slug: String<br>name: String<br>description: String?<br>projectSlug: String?<br>agentId: String?<br>triggerType: String?<br>status: String?<br>lastRunAt: String?<br>lastRunStatus: String? |
| SchedulerJob | 97 | id: String<br>agentId: String<br>project: String<br>graph: String?<br>task: String<br>runType: String<br>cronExpr: String?<br>nextFire: String?<br>status: String |
| Client | 109 | id: String<br>slug: String<br>name: String<br>businessType: String?<br>service: String?<br>contactName: String?<br>contactEmail: String?<br>status: String |
| Project | 120 | id: String<br>slug: String<br>name: String<br>description: String?<br>status: String<br>leadAgent: String? |
| Notification | 129 | id: Int<br>text: String<br>color: String?<br>category: String?<br>createdAt: String?<br>read: Bool |
| Report | 138 | id: String<br>title: String<br>reportType: String<br>content: String<br>summary: String<br>projectSlug: String?<br>generatedBy: String?<br>jobId: String?<br>status: String<br>generatedAt: String? |
| Document | 152 | id: String<br>title: String<br>docType: String<br>content: String<br>format: String<br>projectSlug: String?<br>clientId: String?<br>tags: [String]?<br>createdBy: String?<br>version: Int |
| Conversation | 168 | id: String<br>title: String<br>slug: String?<br>createdAt: String? |
| Message | 175 | id: String<br>conversationId: String<br>role: String<br>content: String<br>agentId: String?<br>createdAt: String? |
| RunRequest | 184 | agentId: String<br>project: String<br>graph: String?<br>task: String<br>maxRevisions: Int<br>priority: String |
| InezChatRequest | 193 | message: String<br>conversationId: String?<br>fileIds: [String]? |
| InezDispatch | 205 | id: String<br>agentId: String?<br>project: String?<br>graph: String?<br>task: String? |
| InezStatusResponse | 220 | awareness: String<br>urgentCount: Int<br>missions: [InezMission]<br>generatedAt: String? |
| InezChatResponse | 227 | conversationId: String?<br>inezMessage: String<br>dispatches: [InezDispatch]<br>needsAgents: Bool<br>queuedRuns: [QueuedRun]?<br>error: String?<br>followupSuggestions: [String]? |
| QueuedRun | 237 | runId: String<br>agentId: String<br>project: String<br>id: String |
| LoginRequest | 244 | username: String<br>password: String |
| LoginResponse | 254 | accessToken: String<br>tokenType: String<br>user: LoginUser? |
| WSEvent | 260 | type: String<br>runId: String?<br>text: String?<br>color: String?<br>data: [String: JSONValue]? |

## Additional parsed structs

| Model | Line | Fields |
| --- | --- | --- |
| AnalyzeEmailResponse | 449 | success: Bool<br>planId: String<br>summary: EmailCleanupSummary |
| BriefStats | 612 | urgentEmails: Int<br>todosDue: Int<br>activeMissions: Int<br>marketMovers: Int<br>deadlinesToday: Int |
| BriefingResponse | 629 | success: Bool<br>briefId: String?<br>briefText: String?<br>stats: MorningBrief.BriefStats?<br>cached: Bool? |
| DailyBrief | 73 | id: String<br>content: String<br>createdAt: String? |
| EmailCleanupExecuteResponse | 461 | success: Bool<br>results: EmailCleanupResults<br>message: String |
| EmailCleanupItem | 375 | id: String<br>planId: String<br>emailId: String<br>category: String<br>subject: String<br>fromAddress: String<br>emailDate: String<br>sizeBytes: Int |
| EmailCleanupPlan | 353 | id: String<br>accountId: String<br>status: String<br>totalEmails: Int<br>suggestedCleanupCount: Int<br>estimatedSpaceMb: Int<br>createdAt: String<br>executedAt: String? |
| EmailCleanupPlanDetail | 431 | plan: EmailCleanupPlan<br>items: [EmailCleanupItem]<br>categories: [String: [EmailCleanupItem]] |
| EmailCleanupResults | 467 | total: Int<br>archived: Int<br>deleted: Int<br>errors: Int<br>spaceRecoveredMb: Double |
| EmailCleanupSummary | 437 | totalSuggested: Int<br>estimatedSpaceMb: Double<br>breakdown: [String: Int] |
| FeedbackResponse | 581 | success: Bool<br>feedbackId: String?<br>rating: Int? |
| FileListResponse | 559 | success: Bool<br>files: [UploadedFile]<br>count: Int |
| FileUploadResponse | 538 | success: Bool<br>file: UploadFileInfo? |
| GlobalMemoryFact | 648 | id: String<br>category: String<br>key: String<br>value: String<br>source: String<br>confidence: Double<br>importance: Int<br>usageCount: Int |
| GlobalMemoryResponse | 705 | success: Bool<br>facts: [GlobalMemoryFact]<br>counts: [String: Int]?<br>categories: [String]? |
| HubConfig | 314 | values: [String: String] |
| InezMission | 213 | id: String<br>name: String<br>slug: String<br>status: String |
| LoginUser | 249 | username: String<br>role: String |
| MemoryFactRequest | 712 | category: String<br>key: String<br>value: String<br>importance: Int<br>source: String |
| MessageFeedback | 567 | messageId: String<br>rating: Int<br>feedbackText: String?<br>category: String? |
| MorningBrief | 595 | briefId: String<br>briefText: String<br>stats: BriefStats<br>createdAt: String<br>cached: Bool?<br>id: String |
| PromptTemplate | 338 | id: String<br>title: String<br>category: String<br>promptText: String<br>agentId: String<br>projectSlug: String<br>isSystem: Bool<br>usageCount: Int |
| SandboxExecuteRequest | 726 | code: String<br>language: String<br>dataFiles: [String]? |
| SandboxGeneratedFile | 737 | id: String<br>name: String<br>mimeType: String<br>contentBase64: String<br>sizeBytes: Int |
| SandboxResult | 752 | success: Bool<br>executionId: String<br>stdout: String<br>stderr: String<br>exitCode: Int<br>executionTimeMs: Int<br>generatedFiles: [SandboxGeneratedFile]<br>error: String? |
| SandboxStatusResponse | 777 | success: Bool<br>available: Bool<br>mode: String<br>dockerAvailable: Bool<br>timeoutSeconds: Int<br>supportedLanguages: [String] |
| UploadFileInfo | 542 | fileId: String<br>filename: String<br>fileType: String<br>fileSize: Int<br>status: String |
| UploadedFile | 482 | fileId: String<br>filename: String<br>fileType: String<br>mimeType: String<br>fileSize: Int<br>parsingStatus: String<br>uploadedAt: String<br>parsedContent: String? |

## Compatibility notes

- `AgentRun.id` is an `Int` in Swift because the server currently returns the auto-increment integer id in list/detail payloads.
- Optional properties are intentional; the backend often returns nulls or omits fields on older rows.
- `InezChatRequest` uses custom coding keys (`conversation_id`, `file_ids`) to match the Python API.
- `DailyBrief` uses a manual decoder because `content` can be a plain string or a flexible JSON object.
- `JSONValue` exists specifically to absorb mixed-type backend payloads without decode failures.

## Stakeholder-requested names not found exactly

- `GlobalMemoryFact`, `GlobalMemoryResponse`, `MemoryFactRequest`, `SandboxExecuteRequest`, `SandboxResult`, `SandboxGeneratedFile`, `SandboxStatusResponse`, `PromptTemplate`, `EmailCleanupPlan`, `BriefingData`, and `AutomationRule` were requested as documentation anchors. If the current code uses different concrete Swift names or nests those contracts differently, keep the API docs and feature docs as the normative contract reference until the Swift model layer is aligned.

## Source

- `projects/archonhub-ios/ArchonHub/Models/Models.swift`

## Model usage patterns

- Health and status payloads drive dashboard presence and complication counts.
- Run and report models support activity-history screens and drill-down views.
- Inez request/response models are the conversational backbone of the app.
- Todo, document, memory, and automation models power the Workspace hub.
- Sandbox models power code execution and generated-file preview flows.

## Nullability guidance

- Use optional strings for fields that can be omitted by older rows or partial endpoints.
- Prefer tolerant decoders for mixed JSON payloads or evolving backend envelopes.
- Keep list/detail models aligned: the same entity may arrive with slightly different field completeness depending on the endpoint.

## Backend alignment checklist

- Verify coding keys whenever the Python API uses snake_case names.
- Verify integer vs string ids before changing client-side identity handling.
- Verify date parsing against `ArchonDateFormatter` before introducing custom parsing in a view.
- Verify enums or status-like strings against the actual Python values rather than UI assumptions.

## Consumer screens

- `DashboardView` relies on health/status-oriented models.
- `RunsView`, `RunDetailView`, and `ReportsView` rely on execution-history contracts.
- `InezView` and related chat views rely on the Inez chat and dispatch contracts.
- `MemoryView` depends on the global-memory contracts staying stable.
- `CodeExecutionView` depends on the sandbox result fields, especially generated files and blocked reasons.

## Related docs

- [API response contract](../contracts/api-response-contract.md)
- [HubClient](hubclient.md)
- [Sandbox contract](../contracts/sandbox-contract.md)
- [Memory fact contract](../contracts/memory-fact-contract.md)

## Practical decoding tips

- Keep model additions source-compatible whenever possible because older app builds may still talk to the same local hub.
- Prefer additive changes to destructive field renames in the Python API.
- When a backend field is optional in practice, model it as optional in Swift even if the ideal contract would require it.
- Use wrapper types like `JSONValue` when the backend intentionally allows flexible content shapes.
- Re-run end-to-end decoding checks after any auth, Inez, memory, sandbox, or document API change.

## Source alignment hotspots

- Auth: `LoginRequest`, `LoginResponse`, `LoginUser`.
- Real-time updates: `WSEvent`.
- Workspace data: `Todo`, `Document`, memory-related structs, automation structs.
- Activity data: `AgentRun`, `Report`, `DailyBrief`, `SchedulerJob`, `Notification`.
- Utility payloads: sandbox structs, prompt-template structs, email cleanup structs.

## Suggested verification checklist

- Verify `HubClient.login(...)` still decodes the auth payload after backend auth changes.
- Verify `RunsView` can decode nullable run fields from historical records.
- Verify memory-related screens can decode category, key, value, importance, and confidence without fallback crashes.
- Verify sandbox generated-file previews still understand MIME type, base64 payload, and byte size fields.
- Verify report and briefing screens can tolerate string-or-object content where the backend is flexible.
- Verify new backend list endpoints either return bare arrays or add wrapper structs explicitly before shipping.

## Mapping to major screens

- Dashboard: `HealthResponse`, quick-run payloads, notifications, and summary metrics.
- Inez: chat request/response models, dispatch rows, status/memory support models.
- Activity: runs, reports, briefing, and alerts.
- Workspace: todos, documents, memory, automations, prompt templates, and related helpers.
- Settings: provider/model rows, auth state, and server configuration surfaces.

