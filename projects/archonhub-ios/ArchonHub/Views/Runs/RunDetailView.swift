import SwiftUI

struct RunDetailView: View {
    let run: AgentRun
    let onCancelled: () async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var isCancelling = false
    @State private var errorMessage = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                headerCard
                scoreCard
                detailCard(title: "Task", content: run.task)
                detailCard(title: "Output", content: run.output ?? "No output yet.")
                detailCard(title: "Critique", content: run.critique ?? "No critique available.")

                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(ArchonTheme.error)
                        .archonCard()
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Run Detail")
        .toolbar {
            if run.status.lowercased() == "running" {
                Button(isCancelling ? "Cancelling..." : "Cancel") {
                    Task { await cancelRun() }
                }
                .disabled(isCancelling)
                .tint(ArchonTheme.error)
            }
        }
        .foregroundStyle(ArchonTheme.text)
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(run.agentId)
                    .font(.title3.bold())
                Spacer()
                Text(run.status.capitalized)
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(ArchonTheme.statusColor(run.status).opacity(0.15))
                    .foregroundStyle(ArchonTheme.statusColor(run.status))
                    .clipShape(Capsule())
            }

            Label(run.project, systemImage: "folder.fill")
            Label(ArchonDateFormatter.timestampString(run.createdAt), systemImage: "clock.fill")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .archonCard()
    }

    private var scoreCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Quality Score")
                .font(.headline)
            ProgressView(value: min(max(run.score ?? 0, 0), 100), total: 100)
                .tint(ArchonTheme.accent)
            Text("\(Int(run.score ?? 0))/100")
                .font(.caption)
                .foregroundStyle(ArchonTheme.muted)
        }
        .archonCard()
    }

    private func detailCard(title: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
            Text(content)
                .font(.body)
                .textSelection(.enabled)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .archonCard()
    }

    private func cancelRun() async {
        isCancelling = true
        defer { isCancelling = false }

        do {
            let _: EmptyResponse = try await HubClient.shared.post("/api/runs/\(run.id)/cancel", body: EmptyBody())
            await onCancelled()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
