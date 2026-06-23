import SwiftUI

// MARK: - Activity Hub (Runs, Reports, Briefing, Notifications)
struct ActivityHubView: View {
    @State private var selection = 0
    private let tabs = ["Runs", "Reports", "Briefing", "Alerts"]
    private let icons = ["play.circle.fill", "newspaper.fill", "text.badge.star", "bolt.fill"]

    var body: some View {
        VStack(spacing: 0) {
            Picker("Section", selection: $selection) {
                ForEach(tabs.indices, id: \.self) { i in
                    Text(tabs[i]).tag(i)
                }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(ArchonTheme.card)

            Divider()

            Group {
                switch selection {
                case 0: RunsView()
                case 1: ReportsView()
                case 2: BriefingView()
                default: NotificationsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .navigationTitle(tabs[selection])
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Workspace Hub (Todos, Documents, Memory, Automations)
struct WorkspaceHubView: View {
    @State private var selection = 0
    private let tabs = ["Todos", "Docs", "Memory", "Auto"]
    private let icons = ["checklist", "doc.text.fill", "brain.head.profile", "bolt.circle.fill"]

    var body: some View {
        VStack(spacing: 0) {
            Picker("Section", selection: $selection) {
                ForEach(tabs.indices, id: \.self) { i in
                    Text(tabs[i]).tag(i)
                }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(ArchonTheme.card)

            Divider()

            Group {
                switch selection {
                case 0: TodosView()
                case 1: DocumentsView()
                case 2: MemoryView()
                default: AutomationsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .navigationTitle(tabs[selection])
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Root Tab View
struct ContentView: View {
    var body: some View {
        TabView {
            NavigationStack {
                DashboardView()
            }
            .tabItem {
                Label("Dashboard", systemImage: "house.fill")
            }

            NavigationStack {
                InezView()
            }
            .tabItem {
                Label("Inez", systemImage: "crown.fill")
            }

            NavigationStack {
                ActivityHubView()
            }
            .tabItem {
                Label("Activity", systemImage: "chart.xyaxis.line")
            }

            NavigationStack {
                WorkspaceHubView()
            }
            .tabItem {
                Label("Workspace", systemImage: "square.grid.2x2.fill")
            }

            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Settings", systemImage: "gearshape.fill")
            }
        }
        .tint(ArchonTheme.accent)
        .toolbarBackground(ArchonTheme.card, for: .tabBar)
        .toolbarBackground(.visible, for: .tabBar)
        .background(ArchonTheme.background.ignoresSafeArea())
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthStore())
        .environmentObject(HubClient.shared)
        .preferredColorScheme(.dark)
}
