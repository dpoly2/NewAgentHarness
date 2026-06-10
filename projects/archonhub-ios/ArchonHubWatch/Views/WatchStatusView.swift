import SwiftUI

struct WatchStatusView: View {
    @State private var health = HealthResponse.empty
    @State private var isOnline = false
    @State private var lastRefresh = Date.now
    @State private var errorMessage = ""
    @State private var showInezSheet = false

    var body: some View {
        ScrollView {
            VStack(spacing: 10) {
                Text("ArchonHub")
                    .font(.headline)
                    .foregroundStyle(ArchonTheme.accent)

                HStack(spacing: 6) {
                    Circle()
                        .fill(isOnline ? ArchonTheme.success : ArchonTheme.error)
                        .frame(width: 10, height: 10)
                    Text(isOnline ? "Hub Online" : "Hub Offline")
                        .font(.caption)
                }

                Text("▶ \(health.activeRuns) Runs")
                    .font(.title3.bold())
                Text("✓ \(health.pendingTodos) Todos")
                    .font(.title3.bold())
                if let model = health.llmModel {
                    Text("⬡ \(model)")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.accent)
                }

                // Ask Inez button
                Button {
                    showInezSheet = true
                } label: {
                    HStack(spacing: 6) {
                        Text("👑")
                            .font(.caption)
                        Text("Ask Inez")
                            .font(.caption.bold())
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(red: 0.49, green: 0.23, blue: 0.93))
                .disabled(!isOnline)

                Text("Updated \(lastRefresh.formatted(date: .omitted, time: .shortened))")
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)

                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.error)
                        .multilineTextAlignment(.center)
                }

                Button("Refresh") {
                    Task { await refresh() }
                }
                .buttonStyle(.borderedProminent)
                .tint(ArchonTheme.accent)
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
    }
}

// MARK: - Watch Inez Sheet

struct WatchInezSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var draft = ""
    @State private var response = ""
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(spacing: 10) {
                HStack(spacing: 6) {
                    Text("👑")
                    Text("Inez")
                        .font(.headline)
                        .foregroundStyle(Color(red: 0.77, green: 0.71, blue: 0.99))
                }

                if response.isEmpty {
                    TextField("Ask Inez...", text: $draft)
                        .textFieldStyle(.roundedBorder)

                    Button(isLoading ? "Sending..." : "Send") {
                        Task { await send() }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(Color(red: 0.49, green: 0.23, blue: 0.93))
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
