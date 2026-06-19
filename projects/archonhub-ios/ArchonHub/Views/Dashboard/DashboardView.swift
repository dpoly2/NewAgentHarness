import SwiftUI

struct DashboardView: View {
    @StateObject var vm = DashboardViewModel()
    @EnvironmentObject private var hubClient: HubClient

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let inezLavender = Color(red: 0.77, green: 0.71, blue: 0.99)

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {

                // ── Inez Status Banner ────────────────────────────────────
                inezStatusBanner

                // ── Mission Grid ─────────────────────────────────────────
                if let status = vm.inezStatus, !status.missions.isEmpty {
                    missionGrid(status)
                }

                // ── Operational Stats ─────────────────────────────────────
                LazyVGrid(columns: columns, spacing: 12) {
                    statCard(title: "Total Runs", value: "\(vm.health.totalRuns)", icon: "chart.bar.fill")
                    statCard(title: "Active Runs", value: "\(vm.health.activeRuns)", icon: "bolt.fill")
                    statCard(title: "Pending Todos", value: "\(vm.health.pendingTodos)", icon: "checklist")
                    statCard(title: "Queue Depth", value: "\(vm.health.queueDepth)", icon: "tray.full.fill")
                }

                // ── Recent Runs ───────────────────────────────────────────
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Recent Runs")
                            .font(.title3.bold())
                        Spacer()
                        if vm.health.activeRuns > 0 {
                            Text("\(vm.health.activeRuns) active")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(ArchonTheme.success)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(ArchonTheme.success.opacity(0.12))
                                .clipShape(Capsule())
                        }
                    }

                    if vm.recentRuns.isEmpty {
                        Text(vm.errorMessage.isEmpty ? "No recent runs." : vm.errorMessage)
                            .foregroundStyle(ArchonTheme.muted)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .archonCard()
                    } else {
                        ForEach(vm.recentRuns.prefix(5)) { run in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(run.agentId)
                                        .font(.headline)
                                    Spacer()
                                    Text(run.status.capitalized)
                                        .font(.caption.weight(.semibold))
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 4)
                                        .background(ArchonTheme.statusColor(run.status).opacity(0.16))
                                        .foregroundStyle(ArchonTheme.statusColor(run.status))
                                        .clipShape(Capsule())
                                }
                                Text(run.task)
                                    .font(.subheadline)
                                    .foregroundStyle(ArchonTheme.text)
                                    .lineLimit(2)
                                HStack {
                                    Text(run.project)
                                    Spacer()
                                    Text(ArchonDateFormatter.relativeString(run.createdAt))
                                }
                                .font(.caption)
                                .foregroundStyle(ArchonTheme.muted)
                            }
                            .archonCard()
                        }
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Mission Control")
        .toolbar {
            NavigationLink {
                InezView()
            } label: {
                HStack(spacing: 4) {
                    Text("👑")
                        .font(.caption)
                    Text("Inez")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(inezLavender)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(inezPurple.opacity(0.15))
                .clipShape(Capsule())
            }
        }
        .refreshable {
            await vm.refresh()
        }
    }

    // MARK: - Inez Status Banner

    private var inezStatusBanner: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header row
            HStack(spacing: 10) {
                ZStack {
                    Circle()
                        .fill(inezPurple)
                        .frame(width: 36, height: 36)
                        .shadow(color: inezPurple.opacity(0.4), radius: 4)
                    Text("👑")
                        .font(.subheadline)
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 6) {
                        Text("INEZ")
                            .font(.subheadline.weight(.bold))
                            .tracking(1.2)
                            .foregroundStyle(inezLavender)
                        Text("·")
                            .foregroundStyle(ArchonTheme.muted)
                        Text("Chief of Staff")
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    Text(hubClient.isOnline ? "Active — ArchonHub connected" : "Hub offline")
                        .font(.caption2)
                        .foregroundStyle(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.error)
                }

                Spacer()

                if let status = vm.inezStatus, status.urgentCount > 0 {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(status.urgentCount)")
                            .font(.title3.bold())
                            .foregroundStyle(ArchonTheme.error)
                        Text("need attention")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                } else if let model = vm.health.llmModel {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("⬡ \(model)")
                            .font(.caption.weight(.medium))
                            .foregroundStyle(inezLavender)
                        Text(vm.health.llmProvider ?? "AI")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                }
            }

            // Awareness line
            if let status = vm.inezStatus, !status.awareness.isEmpty {
                let firstLine = status.awareness.components(separatedBy: "\n").first ?? status.awareness
                if firstLine != "All systems nominal." || status.urgentCount > 0 {
                    Text(firstLine)
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.text.opacity(0.85))
                        .lineLimit(2)
                        .padding(.top, 2)
                }
            }

            // Ask Inez CTA
            NavigationLink(destination: InezView()) {
                HStack(spacing: 6) {
                    Image(systemName: "message.fill")
                        .font(.caption2)
                    Text("Ask Inez")
                        .font(.caption.weight(.semibold))
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.caption2)
                }
                .foregroundStyle(inezLavender)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(inezPurple.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .stroke(inezPurple.opacity(0.25), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
        .padding(14)
        .background(ArchonTheme.card)
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(inezPurple.opacity(0.3), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Mission Grid

    private func missionGrid(_ status: InezStatusResponse) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("ACTIVE MISSIONS")
                .font(.caption.weight(.semibold))
                .tracking(1)
                .foregroundStyle(ArchonTheme.muted)

            LazyVGrid(columns: columns, spacing: 8) {
                ForEach(status.missions) { mission in
                    missionCard(mission)
                }
            }
        }
    }

    private func missionCard(_ mission: InezMission) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(missionIcon(mission.slug))
                    .font(.subheadline)
                Spacer()
                Circle()
                    .fill(missionStatusColor(mission.status))
                    .frame(width: 7, height: 7)
            }
            Text(mission.name)
                .font(.caption.weight(.semibold))
                .foregroundStyle(ArchonTheme.text)
                .lineLimit(2)
            Text(mission.status.capitalized)
                .font(.system(size: 10))
                .foregroundStyle(ArchonTheme.muted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(ArchonTheme.card)
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(ArchonTheme.muted.opacity(0.15), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func missionIcon(_ slug: String) -> String {
        let icons: [String: String] = [
            "archonhub": "🧠", "xftc": "🏃", "s2tdesigns": "🎨",
            "pbs-foundation": "🏛️", "ministry": "✝️", "smithcap-finance": "💰",
            "markets": "📈", "nutrue": "👕", "sigma-signal": "Σ",
            "yepc": "📋", "holdings": "🏢", "nightking": "👑",
        ]
        return icons[slug] ?? "⚙️"
    }

    private func missionStatusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "active": return ArchonTheme.success
        case "paused": return ArchonTheme.warning
        case "complete": return ArchonTheme.muted
        default: return ArchonTheme.accent
        }
    }

    // MARK: - Stat Cards

    private func statCard(title: String, value: String, icon: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: icon)
                .foregroundStyle(ArchonTheme.accent)
            Text(value)
                .font(.title.bold())
            Text(title)
                .font(.footnote)
                .foregroundStyle(ArchonTheme.muted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .archonCard()
    }
}

#Preview {
    NavigationStack {
        DashboardView()
            .environmentObject(HubClient.shared)
    }
    .preferredColorScheme(.dark)
}
