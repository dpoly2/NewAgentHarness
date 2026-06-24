# iOS Views

Expanded compact inventory of SwiftUI view files, feature groupings, and the primary state each file owns.

## Root navigation surfaces

| View | File | Line | State / props |
| --- | --- | --- | --- |
| ActivityHubView | projects/archonhub-ios/ArchonHub/App/ContentView.swift | 4 | @State private var selection = 0<br>@State private var selection = 0 |
| WorkspaceHubView | projects/archonhub-ios/ArchonHub/App/ContentView.swift | 39 | @State private var selection = 0<br>@State private var selection = 0 |
| ContentView | projects/archonhub-ios/ArchonHub/App/ContentView.swift | 74 | @State private var selection = 0<br>@State private var selection = 0 |
| InezView | projects/archonhub-ios/ArchonHub/Views/Chat/InezView.swift | 108 | @EnvironmentObject var hubClient: HubClient<br>@State private var messages: [InezMessage] = []<br>@State private var draft = ""<br>@State private var conversationId: String?<br>@State private var isThinking = false<br>@State private var thinkingStep = ""<br>@State private var errorMessage = ""<br>@State private var showMemory = false<br>@State private var inezStatus: InezStatusResponse?<br>@State private var showStatusHUD = true |
| DashboardView | projects/archonhub-ios/ArchonHub/Views/Dashboard/DashboardView.swift | 3 | @StateObject var vm = DashboardViewModel()<br>@EnvironmentObject private var hubClient: HubClient |
| SettingsView | projects/archonhub-ios/ArchonHub/Views/Settings/SettingsView.swift | 3 | @EnvironmentObject private var authStore: AuthStore<br>@EnvironmentObject private var hubClient: HubClient<br>@State private var serverURL = HubClient.shared.serverURL<br>@State private var serpApiKey = ""<br>@State private var statusMessage = ""<br>@State private var isSavingSerpApi = false |
| WatchMainView | projects/archonhub-ios/ArchonHubWatch/App/WatchMainView.swift | 3 | — |
| WatchNotificationsView | projects/archonhub-ios/ArchonHubWatch/Views/WatchNotificationsView.swift | 3 | @State private var notifications: [Notification] = []<br>@State private var errorMessage = "" |
| WatchQuickRunView | projects/archonhub-ios/ArchonHubWatch/Views/WatchQuickRunView.swift | 3 | @State private var selectedAgent = QUICK_AGENTS.first ?? "grants-research-agent"<br>@State private var selectedProject = ARCHON_PROJECTS.first ?? "xftc"<br>@State private var taskText = "Check project status"<br>@State private var statusMessage = ""<br>@State private var isRunning = false |
| WatchStatusView | projects/archonhub-ios/ArchonHubWatch/Views/WatchStatusView.swift | 3 | @State private var health = HealthResponse.empty<br>@State private var inezAwareness = ""<br>@State private var inezUrgent = 0<br>@State private var isOnline = false<br>@State private var lastRefresh = Date.now<br>@State private var errorMessage = ""<br>@State private var showInezSheet = false<br>@Environment(\.dismiss) private var dismiss<br>@State private var draft = ""<br>@State private var response = "" |

## Feature view inventory

| File | View structs | State / props |
| --- | --- | --- |
| projects/archonhub-ios/ArchonHub/App/ContentView.swift | ActivityHubView@4<br>WorkspaceHubView@39<br>ContentView@74 | @State private var selection = 0<br>@State private var selection = 0 |
| projects/archonhub-ios/ArchonHub/Views/Auth/LoginView.swift | LoginView@3 | @EnvironmentObject private var authStore: AuthStore<br>@State private var username = ""<br>@State private var password = ""<br>@State private var isLoading = false<br>@State private var errorMessage = "" |
| projects/archonhub-ios/ArchonHub/Views/Automations/AutomationsView.swift | AutomationsView@9 | @State private var automations: [Automation] = []<br>@State private var isLoading = false<br>@State private var triggeringIds: Set<String> = []<br>@State private var errorMessage = ""<br>@State private var successMessage = ""<br>@ViewBuilder |
| projects/archonhub-ios/ArchonHub/Views/Briefing/BriefingView.swift | BriefingView@3 | @State private var briefs: [DailyBrief] = []<br>@State private var isLoading = false<br>@State private var isGenerating = false<br>@State private var errorMessage = ""<br>@State private var expandedId: String? |
| projects/archonhub-ios/ArchonHub/Views/Chat/ChatView.swift | ChatView@23 | @EnvironmentObject var hubClient: HubClient<br>@State private var conversations: [Conversation] = []<br>@State private var selectedConversation: Conversation?<br>@State private var messages: [Message] = []<br>@State private var draft = ""<br>@State private var errorMessage = ""<br>@State private var isLoadingMessages = false<br>@State private var searchText = ""<br>@State private var searchResults: [SearchResult] = []<br>@State private var isSearching = false |
| projects/archonhub-ios/ArchonHub/Views/Chat/InezMemoryView.swift | InezMemoryView@41 | @EnvironmentObject var hubClient: HubClient<br>@State private var memory: InezMemoryResponse?<br>@State private var isLoading = false<br>@State private var errorMessage = ""<br>@State private var selectedDate: String?<br>@State private var deletingKey: String?<br>@ViewBuilder<br>@ViewBuilder<br>@ViewBuilder<br>@unknown default: |
| projects/archonhub-ios/ArchonHub/Views/Chat/InezView.swift | FileAttachmentChip@41<br>InezView@108 | @EnvironmentObject var hubClient: HubClient<br>@State private var messages: [InezMessage] = []<br>@State private var draft = ""<br>@State private var conversationId: String?<br>@State private var isThinking = false<br>@State private var thinkingStep = ""<br>@State private var errorMessage = ""<br>@State private var showMemory = false<br>@State private var inezStatus: InezStatusResponse?<br>@State private var showStatusHUD = true |
| projects/archonhub-ios/ArchonHub/Views/Dashboard/DashboardView.swift | DashboardView@3 | @StateObject var vm = DashboardViewModel()<br>@EnvironmentObject private var hubClient: HubClient |
| projects/archonhub-ios/ArchonHub/Views/Documents/DocumentsView.swift | DocumentsView@43<br>AddDocumentView@299<br>DocumentDetailView@378 | @State private var documents: [Document] = []<br>@State private var isLoading = false<br>@State private var errorMessage = ""<br>@State private var searchText = ""<br>@State private var filterType: String = "all"<br>@State private var showingAddSheet = false<br>@State private var selectedDocument: Document?<br>@ViewBuilder<br>@Environment(\.dismiss) var dismiss<br>@State private var title = "" |
| projects/archonhub-ios/ArchonHub/Views/Email/EmailCleanupView.swift | EmailCleanupView@3 | @EnvironmentObject var client: HubClient<br>@State private var plan: EmailCleanupPlan?<br>@State private var items: [EmailCleanupItem] = []<br>@State private var categorizedItems: [String: [EmailCleanupItem]] = [:]<br>@State private var selectedItems: Set<String> = []<br>@State private var isLoading = true<br>@State private var isExecuting = false<br>@State private var error: String?<br>@State private var executionResults: EmailCleanupResults?<br>@State private var expandedCategories: Set<String> = Set(["newsletter", "promotion", "social", "old_thread"]) |
| projects/archonhub-ios/ArchonHub/Views/Memory/MemoryView.swift | MemoryView@5<br>FactRowView@256<br>MemoryFactEditorView@319 | @EnvironmentObject var hubClient: HubClient<br>@State private var facts: [GlobalMemoryFact] = []<br>@State private var counts: [String: Int] = [:]<br>@State private var categories: [String] = []<br>@State private var selectedCategory: String? = nil<br>@State private var searchText = ""<br>@State private var isLoading = false<br>@State private var showAddFact = false<br>@State private var editingFact: GlobalMemoryFact? = nil<br>@State private var errorMessage = "" |
| projects/archonhub-ios/ArchonHub/Views/Models/ModelsView.swift | ModelsView@39 | @State private var models: [LLMModel] = []<br>@State private var providers: [LLMProvider] = []<br>@State private var isLoading = false<br>@State private var errorMessage = ""<br>@State private var selectedProvider: String = "all"<br>@State private var showRouteSheet = false<br>@State private var routeTaskType = ""<br>@State private var routeResult: ModelRoute?<br>@State private var isRouting = false<br>@ViewBuilder |
| projects/archonhub-ios/ArchonHub/Views/Notifications/NotificationsView.swift | NotificationsView@3 | @State private var notifications: [Notification] = []<br>@State private var inezAwareness = ""<br>@State private var isLoading = false<br>@State private var errorMessage = ""<br>@State private var filter = "all" |
| projects/archonhub-ios/ArchonHub/Views/Reports/ReportsView.swift | ReportsView@3 | @State private var reports: [Report] = []<br>@State private var isLoading = false<br>@State private var errorMessage = ""<br>@State private var expandedId: String?<br>@State private var selectedType = "all" |
| projects/archonhub-ios/ArchonHub/Views/Runs/RunDetailView.swift | RunDetailView@3 | @Environment(\.dismiss) private var dismiss<br>@State private var isCancelling = false<br>@State private var errorMessage = "" |
| projects/archonhub-ios/ArchonHub/Views/Runs/RunsView.swift | RunsView@3 | @State private var runs: [AgentRun] = []<br>@State private var filter = "all"<br>@State private var selectedRun: AgentRun?<br>@State private var errorMessage = ""<br>@State private var isLoading = false |
| projects/archonhub-ios/ArchonHub/Views/Sandbox/CodeExecutionView.swift | RunCodeButton@4<br>CodeExecutionView@27<br>GeneratedFilePreview@300 | @State private var showSheet = false<br>@State var initialCode: String<br>@State private var code: String<br>@State private var result: SandboxResult?<br>@State private var isRunning = false<br>@State private var error: String?<br>@State private var selectedFile: SandboxGeneratedFile?<br>@Environment(\.dismiss) private var dismiss<br>@Environment(\.dismiss) private var dismiss |
| projects/archonhub-ios/ArchonHub/Views/Settings/SettingsView.swift | SettingsView@3 | @EnvironmentObject private var authStore: AuthStore<br>@EnvironmentObject private var hubClient: HubClient<br>@State private var serverURL = HubClient.shared.serverURL<br>@State private var serpApiKey = ""<br>@State private var statusMessage = ""<br>@State private var isSavingSerpApi = false |
| projects/archonhub-ios/ArchonHub/Views/Todos/AddTodoView.swift | AddTodoView@3 | @Environment(\.dismiss) private var dismiss<br>@State private var title = ""<br>@State private var description = ""<br>@State private var priority = "medium"<br>@State private var project = ARCHON_PROJECTS.first ?? "xftc"<br>@State private var dueDate = Date()<br>@State private var includeDueDate = false<br>@State private var isSaving = false<br>@State private var errorMessage = "" |
| projects/archonhub-ios/ArchonHub/Views/Todos/TodosView.swift | TodosView@3<br>TodoDetailSheet@165 | @State private var todos: [Todo] = []<br>@State private var filter = "all"<br>@State private var showAddTodo = false<br>@State private var selectedTodo: Todo?<br>@State private var errorMessage = ""<br>@ViewBuilder<br>@Environment(\.dismiss) private var dismiss |
| projects/archonhub-ios/ArchonHubWatch/App/WatchMainView.swift | WatchMainView@3 | — |
| projects/archonhub-ios/ArchonHubWatch/Views/WatchNotificationsView.swift | WatchNotificationsView@3 | @State private var notifications: [Notification] = []<br>@State private var errorMessage = "" |
| projects/archonhub-ios/ArchonHubWatch/Views/WatchQuickRunView.swift | WatchQuickRunView@3 | @State private var selectedAgent = QUICK_AGENTS.first ?? "grants-research-agent"<br>@State private var selectedProject = ARCHON_PROJECTS.first ?? "xftc"<br>@State private var taskText = "Check project status"<br>@State private var statusMessage = ""<br>@State private var isRunning = false |
| projects/archonhub-ios/ArchonHubWatch/Views/WatchStatusView.swift | WatchStatusView@3<br>WatchInezSheet@153 | @State private var health = HealthResponse.empty<br>@State private var inezAwareness = ""<br>@State private var inezUrgent = 0<br>@State private var isOnline = false<br>@State private var lastRefresh = Date.now<br>@State private var errorMessage = ""<br>@State private var showInezSheet = false<br>@Environment(\.dismiss) private var dismiss<br>@State private var draft = ""<br>@State private var response = "" |

## Grouping notes

- `App/ContentView.swift` owns the 5-tab shell plus segmented Activity and Workspace hubs.
- `Views/Auth` handles login and session entry.
- `Views/Chat` holds Inez chat and memory-focused screens.
- `Views/Dashboard`, `Runs`, `Reports`, `Briefing`, and `Notifications` form the operational activity surface.
- `Views/Todos`, `Documents`, `Memory`, and `Automations` form the workspace surface.
- `Views/Sandbox` exposes code execution.
- `ArchonHubWatch/Views/**` mirrors a subset of the mobile experience in glanceable watch-friendly form.

## State management notes

- `@State` wrappers usually track picker selection, loading flags, local forms, and sheet presentation.
- Shared backend access normally comes from `HubClient.shared` or environment objects rather than large local stores in each view file.
- Auth-sensitive screens should assume the JWT may be missing or expired and surface retry/login actions accordingly.

## Source

- `projects/archonhub-ios/ArchonHub/App/ContentView.swift`
- `projects/archonhub-ios/ArchonHub/Views/**`
- `projects/archonhub-ios/ArchonHubWatch/Views/**`

## Primary user journeys

1. Launch app → authenticate in `LoginView` → land on `ContentView`.
2. Open Dashboard for system health and quick launches.
3. Open Inez for conversation, dispatches, and context-aware assistance.
4. Use Activity hub for runs, reports, briefings, and alerts.
5. Use Workspace hub for todos, documents, memory, and automations.
6. Use Settings to adjust server URL, auth state, and integration-adjacent options.

## View-level implementation notes

- Segmented hub views reduce tab-bar pressure while keeping the app within Apple tab-count norms.
- Many screens are async-data views that fetch on appear and refresh on pull or task triggers.
- Error presentation should remain concise because the app already exposes verbose debugging at the network layer.
- Reusable theme helpers in `AppSupport.swift` keep cards, colors, and status indicators consistent.

## Watch complement

- The watch app intentionally focuses on glanceable status and one-tap actions instead of full CRUD.
- Shared summary counts like active runs and pending todos bridge the phone/watch experience.

## Related docs

- [iOS overview](overview.md)
- [iOS models](models.md)
- [HubClient](hubclient.md)
- [watchOS](watchos.md)

## File-by-file reading order

- Start with `App/ArchonHubApp.swift` to see app bootstrap and shared dependencies.
- Read `App/ContentView.swift` next to understand the high-level navigation shell.
- Read `Views/Dashboard/*` and `Views/Chat/*` for the most operator-visible surfaces.
- Read `Views/Documents/*`, `Views/Memory/*`, and `Views/Sandbox/*` for data-heavy flows.
- Finish with watch views and complication files for glanceable experience details.

## UI consistency notes

- Status and priority coloring come from `ArchonTheme` helpers in `AppSupport.swift`.
- Shared date rendering flows through `ArchonDateFormatter`.
- Many views rely on reusable cards and segmented pickers instead of bespoke layout systems.
- Server errors should usually map back to `APIError` messages rather than custom per-screen error enums.

## Screen ownership summary

- Dashboard screens own status polling and quick-action affordances.
- Chat screens own conversational message lists, composer state, and dispatch rendering.
- Workspace screens own CRUD-style list/detail editing for todos, documents, memory facts, and automations.
- Activity screens own historical browsing for runs, reports, briefings, and notifications.
- Settings screens own server URL, login/logout, and provider/agent preference surfaces.

## Debugging checklist

- If a screen appears empty, confirm the matching endpoint exists in the API docs and returns decodable JSON.
- If a list fails to refresh, inspect async task triggers and `HubClient` error handling before changing UI state code.
- If a view shows stale timestamps, trace through `ArchonDateFormatter` rather than adding ad-hoc formatting.
- If the watch app shows stale counts, verify the shared summary values are being written by the phone client.
- If navigation feels inconsistent, compare the screen to the root tab + segmented-hub conventions already used in `ContentView`.

## Common interaction patterns

- Segmented pickers switch sub-sections inside hub views instead of pushing a new top-level tab.
- Lists usually navigate into lightweight detail views rather than complex nested coordinators.
- Sheets and alerts are commonly driven by small `@State` booleans near the top of each feature file.
- Async refresh usually happens on appear, on task, or after a successful mutation call through `HubClient`.
- Read-only views still inherit theme and status-color conventions from shared support code.

## Related source anchors

- `projects/archonhub-ios/ArchonHub/App/ContentView.swift`
- `projects/archonhub-ios/ArchonHub/Views/Dashboard/DashboardView.swift`
- `projects/archonhub-ios/ArchonHub/Views/Chat/InezView.swift`
- `projects/archonhub-ios/ArchonHub/Views/Documents/DocumentsView.swift`
- `projects/archonhub-ios/ArchonHubWatch/Views/WatchStatusView.swift`
## Final note

- Use this inventory as a navigation aid, then open the concrete Swift file for render logic and async behavior.
- The table above is intentionally compact to stay in sync with the live codebase.


- Generated from the current file tree; re-run docs generation after major UI refactors.
