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
                InezView()
            }
            .tabItem {
                Label("Inez", systemImage: "crown.fill")
            }
            
            NavigationStack{
                ReportsView()
            }
            .tabItem{
                
                Label("Reports", systemImage: "newspaper.fill")
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
                NotificationsView()
            }
            .tabItem {
                Label("Notifications", systemImage: "bolt.fill")
            }

            NavigationStack {
                BriefingView()
            }
            .tabItem {
                Label("Briefing", systemImage: "text.badge.star")
            }
            
            NavigationStack {
                DocumentsView()
            }
            .tabItem {
                Label("Documents", systemImage: "doc.text.fill")
            }

            NavigationStack {
                MemoryView()
            }
            .tabItem {
                Label("Memory", systemImage: "brain.head.profile")
            }

            NavigationStack {
                AutomationsView()
            }
            .tabItem {
                Label("Automations", systemImage: "bolt.circle.fill")
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
