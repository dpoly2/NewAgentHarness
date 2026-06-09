import SwiftUI

struct WatchStatusView: View {
    @State private var health = HealthResponse.empty
    @State private var isOnline = false
    @State private var lastRefresh = Date.now
    @State private var errorMessage = ""

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
