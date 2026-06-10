import SwiftUI

struct DashboardView: View {
    @StateObject var vm = DashboardViewModel()
    @EnvironmentObject private var hubClient: HubClient

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                statusBanner

                LazyVGrid(columns: columns, spacing: 12) {
                    statCard(title: "Total Runs", value: "\(vm.health.totalRuns)", icon: "chart.bar.fill")
                    statCard(title: "Active Runs", value: "\(vm.health.activeRuns)", icon: "bolt.fill")
                    statCard(title: "Pending Todos", value: "\(vm.health.pendingTodos)", icon: "checklist")
                    statCard(title: "Queue Depth", value: "\(vm.health.queueDepth)", icon: "tray.full.fill")
                    statCard(title: "Online Clients", value: "\(vm.health.wsClients)", icon: "person.3.fill")
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text("Recent Runs")
                        .font(.title3.bold())

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
        .navigationTitle("Dashboard")
        .toolbar {
            NavigationLink {
                ChatView()
            } label: {
                Image(systemName: "message.fill")
                    .foregroundStyle(ArchonTheme.accent)
            }
        }
        .refreshable {
            await vm.refresh()
        }
    }

    private var statusBanner: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.error)
                .frame(width: 12, height: 12)
            VStack(alignment: .leading, spacing: 4) {
                Text(hubClient.isOnline ? "Hub Online" : "Hub Offline")
                    .font(.headline)
                Text("Server \(hubClient.serverURL)")
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.muted)
                    .lineLimit(1)
            }
            Spacer()
            if let model = vm.health.llmModel {
                HStack(spacing: 4) {
                    Text("⬡")
                        .font(.caption)
                    Text("\(vm.health.llmProvider ?? "llm")/\(model)")
                        .font(.caption.weight(.medium))
                        .lineLimit(1)
                }
                .foregroundStyle(ArchonTheme.accent)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(ArchonTheme.accent.opacity(0.12))
                .clipShape(Capsule())
            }
        }
        .archonCard()
    }

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
