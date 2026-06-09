import SwiftUI

struct WatchQuickRunView: View {
    @State private var selectedAgent = QUICK_AGENTS.first ?? "grants-research-agent"
    @State private var selectedProject = ARCHON_PROJECTS.first ?? "xftc"
    @State private var taskText = "Check project status"
    @State private var statusMessage = ""
    @State private var isRunning = false

    private let quickTasks = ["Morning sync", "Queue review", "Client update"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                Picker("Agent", selection: $selectedAgent) {
                    ForEach(QUICK_AGENTS, id: \.self, content: Text.init)
                }

                Picker("Project", selection: $selectedProject) {
                    ForEach(ARCHON_PROJECTS.prefix(5), id: \.self, content: Text.init)
                }

                TextField("Task", text: $taskText)

                VStack(alignment: .leading, spacing: 6) {
                    ForEach(quickTasks, id: \.self) { quickTask in
                        Button(quickTask) {
                            taskText = quickTask
                        }
                        .font(.caption)
                    }
                }

                Button(isRunning ? "Running..." : "▶ Run") {
                    Task { await runAgent() }
                }
                .buttonStyle(.borderedProminent)
                .tint(ArchonTheme.accent)
                .disabled(isRunning || taskText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                if !statusMessage.isEmpty {
                    Text(statusMessage)
                        .font(.caption2)
                        .foregroundStyle(statusMessage.lowercased().contains("failed") ? ArchonTheme.error : ArchonTheme.success)
                }
            }
            .padding()
        }
        .background(ArchonTheme.background)
        .foregroundStyle(ArchonTheme.text)
    }

    private func runAgent() async {
        isRunning = true
        defer { isRunning = false }

        do {
            let request = RunRequest(
                agentId: selectedAgent,
                project: selectedProject,
                graph: nil,
                task: taskText,
                maxRevisions: 1,
                priority: "normal"
            )

            let _: AgentRun = try await HubClient.shared.post("/api/runs", body: request)
            statusMessage = "Run queued."
        } catch {
            statusMessage = "Run failed: \(error.localizedDescription)"
        }
    }
}
