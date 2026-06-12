import SwiftUI

private struct TriggerResult: Decodable {
    let runId: String?
    let automationId: String?
    let status: String?
}

struct AutomationsView: View {
    @State private var automations: [Automation] = []
    @State private var isLoading = false
    @State private var triggeringIds: Set<String> = []
    @State private var errorMessage = ""
    @State private var successMessage = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Automations")
                            .font(.largeTitle.bold())
                        Text("\(automations.count) automation\(automations.count == 1 ? "" : "s")")
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    Spacer()
                    Button { Task { await loadAutomations() } } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }

                if !successMessage.isEmpty {
                    Label(successMessage, systemImage: "checkmark.circle.fill")
                        .foregroundStyle(ArchonTheme.success)
                        .font(.subheadline)
                        .archonCard()
                        .transition(.opacity)
                }

                if !errorMessage.isEmpty {
                    Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(ArchonTheme.warning)
                        .font(.subheadline)
                        .archonCard()
                }

                if isLoading && automations.isEmpty {
                    ProgressView()
                        .tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity)
                        .archonCard()
                } else if automations.isEmpty {
                    Text(errorMessage.isEmpty ? "No automations configured." : "")
                        .foregroundStyle(ArchonTheme.muted)
                        .archonCard()
                } else {
                    ForEach(automations) { automation in
                        automationCard(automation)
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Automations")
        .task { if automations.isEmpty { await loadAutomations() } }
        .refreshable { await loadAutomations() }
    }

    private func automationCard(_ automation: Automation) -> some View {
        let isTriggering = triggeringIds.contains(automation.id)
        return VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(automation.name)
                        .font(.headline)
                    if let desc = automation.description, !desc.isEmpty {
                        Text(desc)
                            .font(.subheadline)
                            .foregroundStyle(ArchonTheme.muted)
                            .lineLimit(2)
                    }
                }
                Spacer()
                statusBadge(automation.status)
            }

            Divider().background(Color.white.opacity(0.1))

            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Project")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                    Text(automation.projectSlug ?? "—")
                        .font(.caption.bold())
                        .foregroundStyle(ArchonTheme.accent)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("Trigger")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                    Text(automation.triggerType?.replacingOccurrences(of: "_", with: " ").capitalized ?? "—")
                        .font(.caption.bold())
                }
                Spacer()
                if let lastRun = automation.lastRunAt {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("Last run")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                        Text(ArchonDateFormatter.relativeString(lastRun))
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                }
            }

            // Last run status indicator
            if let runStatus = automation.lastRunStatus {
                HStack(spacing: 6) {
                    Circle()
                        .fill(runStatusColor(runStatus))
                        .frame(width: 7, height: 7)
                    Text("Last run: \(runStatus.capitalized)")
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }

            Button {
                Task { await trigger(automation) }
            } label: {
                HStack {
                    if isTriggering {
                        ProgressView()
                            .tint(.white)
                            .scaleEffect(0.8)
                        Text("Triggering…")
                    } else {
                        Image(systemName: "bolt.fill")
                        Text("Trigger Now")
                    }
                }
                .font(.subheadline.bold())
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(isTriggering
                    ? ArchonTheme.muted.opacity(0.3)
                    : Color(red: 0.49, green: 0.23, blue: 0.93))
                .foregroundStyle(.white)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            }
            .disabled(isTriggering)
        }
        .archonCard()
    }

    @ViewBuilder
    private func statusBadge(_ status: String?) -> some View {
        let s = (status ?? "unknown").lowercased()
        let color: Color = switch s {
            case "active":   ArchonTheme.success
            case "inactive": ArchonTheme.muted
            case "error":    .red
            default:         ArchonTheme.muted
        }
        Text((status ?? "unknown").capitalized)
            .font(.caption2.bold())
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.18))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }

    private func runStatusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "success", "completed": return ArchonTheme.success
        case "running":              return ArchonTheme.warning
        case "failed", "error":      return .red
        default:                     return ArchonTheme.muted
        }
    }

    private func loadAutomations() async {
        isLoading = true
        defer { isLoading = false }
        do {
            automations = try await HubClient.shared.get("/api/automations")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func trigger(_ automation: Automation) async {
        triggeringIds.insert(automation.id)
        successMessage = ""
        defer { triggeringIds.remove(automation.id) }
        do {
            let result: TriggerResult = try await HubClient.shared.post(
                "/api/automations/\(automation.id)/trigger",
                body: EmptyBody()
            )
            withAnimation {
                let runId = result.runId.map { String($0.prefix(8)) } ?? "started"
                successMessage = "\(automation.name) triggered, run \(runId)"
            }
            await loadAutomations()
        } catch {
            errorMessage = "Trigger failed: \(error.localizedDescription)"
        }
    }
}

#Preview {
    NavigationStack { AutomationsView() }
        .preferredColorScheme(.dark)
}
