import SwiftUI

struct RunsView: View {
    @State private var runs: [AgentRun] = []
    @State private var filter = "all"
    @State private var selectedRun: AgentRun?
    @State private var errorMessage = ""
    @State private var isLoading = false

    private let filters = ["all", "running", "completed", "failed"]

    private var filteredRuns: [AgentRun] {
        guard filter != "all" else { return runs }
        return runs.filter { $0.status.lowercased() == filter }
    }

    var body: some View {
        List {
            Picker("Status", selection: $filter) {
                ForEach(filters, id: \.self) { value in
                    Text(value.replacingOccurrences(of: "_", with: " ").capitalized).tag(value)
                }
            }
            .pickerStyle(.segmented)
            .listRowBackground(ArchonTheme.card)

            if filteredRuns.isEmpty && !isLoading {
                Text(errorMessage.isEmpty ? "No runs available." : errorMessage)
                    .foregroundStyle(ArchonTheme.muted)
                    .listRowBackground(ArchonTheme.card)
            } else {
                ForEach(filteredRuns) { run in
                    Button {
                        selectedRun = run
                    } label: {
                        HStack(alignment: .top, spacing: 12) {
                            Circle()
                                .fill(ArchonTheme.statusColor(run.status))
                                .frame(width: 10, height: 10)
                                .padding(.top, 5)

                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text(run.agentId)
                                        .font(.headline)
                                    Spacer()
                                    Text(run.status.capitalized)
                                        .font(.caption.weight(.semibold))
                                        .foregroundStyle(ArchonTheme.statusColor(run.status))
                                }

                                Text(run.task)
                                    .font(.subheadline)
                                    .foregroundStyle(ArchonTheme.text)
                                    .lineLimit(2)

                                HStack {
                                    Text(run.project)
                                    Spacer()
                                    if let score = run.score {
                                        Text("Score \(Int(score))")
                                    }
                                    Text(ArchonDateFormatter.relativeString(run.createdAt))
                                }
                                .font(.caption)
                                .foregroundStyle(ArchonTheme.muted)
                            }
                        }
                        .padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                    .listRowBackground(ArchonTheme.card)
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Runs")
        .foregroundStyle(ArchonTheme.text)
        .task {
            if runs.isEmpty {
                await loadRuns()
            }
        }
        .refreshable {
            await loadRuns()
        }
        .sheet(item: $selectedRun) { run in
            NavigationStack {
                RunDetailView(run: run) {
                    await loadRuns()
                }
            }
            .preferredColorScheme(.dark)
        }
    }

    private func loadRuns() async {
        isLoading = true
        defer { isLoading = false }

        do {
            runs = try await HubClient.shared.get("/api/runs")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
            runs = []
        }
    }
}

#Preview {
    NavigationStack { RunsView() }
        .preferredColorScheme(.dark)
}
