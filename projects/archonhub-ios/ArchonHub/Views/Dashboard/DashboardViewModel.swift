import Foundation
import Combine

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var health: HealthResponse = .empty
    @Published var recentRuns: [AgentRun] = []
    @Published var isLoading = false
    @Published var errorMessage = ""

    private var timerCancellable: AnyCancellable?

    init() {
        timerCancellable = Timer.publish(every: 30, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                Task { await self?.refresh() }
            }

        Task {
            await refresh()
        }
    }

    deinit {
        timerCancellable?.cancel()
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }

        do {
            async let healthResponse: HealthResponse = HubClient.shared.get("/api/health")
            async let runResponse: [AgentRun] = HubClient.shared.get("/api/runs?limit=5")

            health = try await healthResponse
            recentRuns = try await runResponse
            errorMessage = ""
            HubClient.shared.applyHealthResponse(health)
        } catch {
            errorMessage = error.localizedDescription
            recentRuns = []
        }
    }
}
