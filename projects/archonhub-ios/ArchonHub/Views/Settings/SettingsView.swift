import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var hubClient: HubClient

    @State private var serverURL = HubClient.shared.serverURL
    @State private var serpApiKey = ""
    @State private var statusMessage = ""
    @State private var isSavingSerpApi = false

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

            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label("SerpAPI Key", systemImage: "key.fill")
                        .font(.headline)
                    
                    Text("Enable web search with Google-powered results")
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.muted)
                    
                    SecureField("API Key", text: $serpApiKey)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)
                    
                    HStack {
                        Button(action: { Task { await saveSerpApiKey() } }) {
                            HStack {
                                if isSavingSerpApi {
                                    ProgressView()
                                        .progressViewStyle(.circular)
                                        .scaleEffect(0.8)
                                }
                                Text(isSavingSerpApi ? "Saving..." : "Save Key")
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                        }
                        .buttonStyle(.bordered)
                        .disabled(serpApiKey.isEmpty || isSavingSerpApi)
                        
                        if !serpApiKey.isEmpty {
                            Button(action: { serpApiKey = "" }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(ArchonTheme.muted)
                            }
                        }
                    }
                    
                    Link(destination: URL(string: "https://serpapi.com/")!) {
                        HStack {
                            Text("Get free API key →")
                            Spacer()
                            Image(systemName: "arrow.up.forward.square")
                        }
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.accent)
                    }
                }
            } header: {
                Text("Web Search")
            } footer: {
                Text("Free tier: 100 searches/month. Enables Inez to search the web for real-time information.")
                    .font(.caption)
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
        .task {
            await loadSerpApiKey()
        }
    }

    private func saveAndCheck() async {
        hubClient.serverURL = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        await hubClient.checkHealth()
        statusMessage = hubClient.isOnline ? "Connected successfully." : "Unable to reach the Hub."
    }
    
    private func loadSerpApiKey() async {
        do {
            struct ConfigResponse: Codable {
                let serpapi_api_key: String?
                
                enum CodingKeys: String, CodingKey {
                    case serpapi_api_key
                }
            }
            
            let config: ConfigResponse = try await hubClient.get("/api/config")
            if let key = config.serpapi_api_key, !key.isEmpty {
                serpApiKey = key
            }
        } catch {
            // Silently fail - key not set yet
        }
    }
    
    private func saveSerpApiKey() async {
        isSavingSerpApi = true
        defer { isSavingSerpApi = false }
        
        do {
            struct ConfigUpdate: Encodable {
                let data: [String: String]
            }
            
            struct ConfigResponse: Decodable {
                let success: Bool?
            }
            
            let _: ConfigResponse = try await hubClient.put(
                "/api/config",
                body: ConfigUpdate(data: ["serpapi_api_key": serpApiKey])
            )
            
            statusMessage = "✅ SerpAPI key saved successfully"
            
            // Clear message after 3 seconds
            Task {
                try? await Task.sleep(for: .seconds(3))
                statusMessage = ""
            }
        } catch {
            statusMessage = "❌ Failed to save key: \(error.localizedDescription)"
        }
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
