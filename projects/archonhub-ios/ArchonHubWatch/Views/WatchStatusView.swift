import SwiftUI

struct WatchStatusView: View {
    @State private var health = HealthResponse.empty
    @State private var inezAwareness = ""
    @State private var inezUrgent = 0
    @State private var isOnline = false
    @State private var lastRefresh = Date.now
    @State private var errorMessage = ""
    @State private var showInezSheet = false

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let inezLavender = Color(red: 0.77, green: 0.71, blue: 0.99)

    var body: some View {
        ScrollView {
            VStack(spacing: 10) {

                // ── Inez Identity Header ──────────────────────────────
                VStack(spacing: 4) {
                    ZStack {
                        Circle()
                            .fill(inezPurple)
                            .frame(width: 38, height: 38)
                            .shadow(color: inezPurple.opacity(0.4), radius: 4)
                        Text("👑")
                            .font(.subheadline)
                    }
                    Text("INEZ")
                        .font(.caption.weight(.bold))
                        .tracking(1.5)
                        .foregroundStyle(inezLavender)
                    HStack(spacing: 5) {
                        Circle()
                            .fill(isOnline ? ArchonTheme.success : ArchonTheme.error)
                            .frame(width: 6, height: 6)
                        Text(isOnline ? "Active" : "Offline")
                            .font(.system(size: 10))
                            .foregroundStyle(isOnline ? ArchonTheme.success : ArchonTheme.muted)
                    }
                }

                // ── Awareness Line ────────────────────────────────────
                if !inezAwareness.isEmpty {
                    let firstLine = inezAwareness.components(separatedBy: "\n").first ?? inezAwareness
                    Text(firstLine)
                        .font(.system(size: 11))
                        .foregroundStyle(ArchonTheme.text.opacity(0.85))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 6)
                }

                // ── Mission Stats ─────────────────────────────────────
                HStack(spacing: 14) {
                    VStack(spacing: 3) {
                        Text("\(health.activeRuns)")
                            .font(.title3.bold())
                            .foregroundStyle(inezUrgent > 0 ? ArchonTheme.error : ArchonTheme.text)
                        Text("Runs")
                            .font(.system(size: 9))
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    VStack(spacing: 3) {
                        Text("\(health.pendingTodos)")
                            .font(.title3.bold())
                        Text("Todos")
                            .font(.system(size: 9))
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    if inezUrgent > 0 {
                        VStack(spacing: 3) {
                            Text("\(inezUrgent)")
                                .font(.title3.bold())
                                .foregroundStyle(ArchonTheme.error)
                            Text("Urgent")
                                .font(.system(size: 9))
                                .foregroundStyle(ArchonTheme.muted)
                        }
                    }
                }

                // ── Inez Button ───────────────────────────────────────
                Button {
                    showInezSheet = true
                } label: {
                    HStack(spacing: 5) {
                        Text("👑")
                            .font(.system(size: 11))
                        Text("Talk to Inez")
                            .font(.caption.bold())
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(inezPurple)
                .disabled(!isOnline)

                // ── Footer ─────────────────────────────────────────────
                Text(lastRefresh.formatted(date: .omitted, time: .shortened))
                    .font(.system(size: 9))
                    .foregroundStyle(ArchonTheme.muted)

                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(.system(size: 9))
                        .foregroundStyle(ArchonTheme.error)
                        .multilineTextAlignment(.center)
                }

                Button("Refresh") {
                    Task { await refresh() }
                }
                .buttonStyle(.borderedProminent)
                .tint(ArchonTheme.accent)
                .font(.caption2)
            }
            .frame(maxWidth: .infinity)
            .padding()
        }
        .background(ArchonTheme.background)
        .foregroundStyle(ArchonTheme.text)
        .task {
            await refresh()
        }
        .sheet(isPresented: $showInezSheet) {
            WatchInezSheet()
        }
    }

    private func refresh() async {
        do {
            health = try await HubClient.shared.get("/api/health")
            isOnline = true
            lastRefresh = .now
            errorMessage = ""

            UserDefaults.standard.set(health.activeRuns, forKey: "archonhub.complication.activeRuns")
            UserDefaults.standard.set(health.pendingTodos, forKey: "archonhub.complication.pendingTodos")
        } catch {
            isOnline = false
            errorMessage = error.localizedDescription
        }

        // Load Inez awareness — non-fatal
        if let status = try? await HubClient.shared.get("/api/inez/status") as InezStatusResponse {
            inezAwareness = status.awareness
            inezUrgent = status.urgentCount
        }
    }
}

// MARK: - Watch Inez Sheet

struct WatchInezSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var draft = ""
    @State private var response = ""
    @State private var isLoading = false

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let inezLavender = Color(red: 0.77, green: 0.71, blue: 0.99)

    var body: some View {
        ScrollView {
            VStack(spacing: 10) {
                HStack(spacing: 6) {
                    Text("👑")
                    Text("Inez")
                        .font(.headline)
                        .foregroundStyle(inezLavender)
                }

                if response.isEmpty {
                    TextField("Ask Inez...", text: $draft)

                    Button(isLoading ? "Sending..." : "Send") {
                        Task { await send() }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(inezPurple)
                    .disabled(draft.isEmpty || isLoading)
                } else {
                    Text(response)
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.text)
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Button("Done") { dismiss() }
                        .buttonStyle(.bordered)
                }
            }
            .padding()
        }
        .background(ArchonTheme.background)
    }

    private func send() async {
        guard !draft.isEmpty else { return }
        isLoading = true
        do {
            let result: InezChatResponse = try await HubClient.shared.post(
                "/api/inez/chat",
                body: InezChatRequest(message: draft, conversationId: nil)
            )
            response = result.inezMessage
        } catch {
            response = "Error: \(error.localizedDescription)"
        }
        isLoading = false
    }
}
