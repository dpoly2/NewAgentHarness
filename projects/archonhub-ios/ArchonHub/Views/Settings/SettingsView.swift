import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var hubClient: HubClient

    @State private var serverURL = HubClient.shared.serverURL
    @State private var statusMessage = ""

    var body: some View {
        Form {
            Section("Connection") {
                TextField("Server URL", text: $serverURL)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .autocorrectionDisabled()

                HStack {
                    Circle()
                        .fill(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.error)
                        .frame(width: 10, height: 10)
                    Text(hubClient.isOnline ? "Hub Online" : "Hub Offline")
                    Spacer()
                    Button("Check") {
                        Task { await saveAndCheck() }
                    }
                }

                if !statusMessage.isEmpty {
                    Text(statusMessage)
                        .font(.footnote)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }

            Section("Account") {
                LabeledContent("Username", value: authStore.username.isEmpty ? "Not set" : authStore.username)
                LabeledContent("Role", value: authStore.role.capitalized)
                Button("Logout", role: .destructive) {
                    authStore.logout()
                }
            }

            Section("About") {
                LabeledContent("Version", value: "ArchonHub v1.0.0")
                LabeledContent("Product", value: "AI Agent Harness")
                NavigationLink("Models & Providers") { ModelsView() }
            }
        }
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Settings")
        .foregroundStyle(ArchonTheme.text)
    }

    private func saveAndCheck() async {
        hubClient.serverURL = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        await hubClient.checkHealth()
        statusMessage = hubClient.isOnline ? "Connected successfully." : "Unable to reach the Hub."
    }
}

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(AuthStore())
            .environmentObject(HubClient.shared)
    }
    .preferredColorScheme(.dark)
}
