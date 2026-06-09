import SwiftUI

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
                RunsView()
            }
            .tabItem {
                Label("Runs", systemImage: "play.circle.fill")
            }

            NavigationStack {
                TodosView()
            }
            .tabItem {
                Label("Todos", systemImage: "checklist")
            }

            NavigationStack {
                BriefingView()
            }
            .tabItem {
                Label("Briefing", systemImage: "newspaper.fill")
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
