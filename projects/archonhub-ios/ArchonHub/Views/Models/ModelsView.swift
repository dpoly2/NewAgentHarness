import SwiftUI

// MARK: - Data Models

struct LLMModel: Codable, Identifiable {
    let provider: String
    let modelId: String
    let display: String
    let capabilities: [String]
    let contextK: Int
    let tier: String
    let key: String
    var keyConfigured: Bool
    var enabled: Bool

    var id: String { key }
}

struct LLMProvider: Codable, Identifiable {
    let provider: String
    let keyConfigured: Bool
    let envKey: String
    let totalModels: Int
    let enabledModels: Int

    var id: String { provider }
}

struct ModelRoute: Codable {
    let provider: String
    let modelId: String
    let display: String
    let capability: String
    let reason: String
}

// MARK: - Models View

struct ModelsView: View {
    @State private var models: [LLMModel] = []
    @State private var providers: [LLMProvider] = []
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var selectedProvider: String = "all"
    @State private var showRouteSheet = false
    @State private var routeTaskType = ""
    @State private var routeResult: ModelRoute?
    @State private var isRouting = false

    private var providerFilters: [String] {
        ["all"] + providers.map(\.provider)
    }

    private var filteredModels: [LLMModel] {
        selectedProvider == "all" ? models : models.filter { $0.provider == selectedProvider }
    }

    // Group filtered models by provider
    private var groupedModels: [(String, [LLMModel])] {
        var dict: [(String, [LLMModel])] = []
        var seen: [String: Int] = [:]
        for m in filteredModels {
            if let idx = seen[m.provider] {
                dict[idx].1.append(m)
            } else {
                seen[m.provider] = dict.count
                dict.append((m.provider, [m]))
            }
        }
        return dict
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Models")
                            .font(.largeTitle.bold())
                        Text("\(models.filter(\.enabled).count) of \(models.count) enabled")
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    Spacer()
                    HStack(spacing: 10) {
                        Button {
                            showRouteSheet = true
                        } label: {
                            Label("Route", systemImage: "arrow.triangle.branch")
                                .font(.caption.bold())
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .tint(ArchonTheme.accent)

                        Button { Task { await load() } } label: {
                            Image(systemName: "arrow.clockwise").foregroundStyle(ArchonTheme.accent)
                        }
                    }
                }

                // Provider pills
                if !providers.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(providerFilters, id: \.self) { p in
                                providerPill(p)
                            }
                        }
                        .padding(.horizontal, 1)
                    }
                }

                // Error
                if !errorMessage.isEmpty {
                    Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(ArchonTheme.warning)
                        .font(.subheadline)
                        .archonCard()
                }

                if isLoading && models.isEmpty {
                    ProgressView().tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity).archonCard()
                } else {
                    ForEach(groupedModels, id: \.0) { providerName, provModels in
                        providerSection(providerName, models: provModels)
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Models")
        .task { if models.isEmpty { await load() } }
        .refreshable { await load() }
        .sheet(isPresented: $showRouteSheet) {
            routeSheet
        }
    }

    // MARK: - Provider pill

    private func providerPill(_ p: String) -> some View {
        let isActive = selectedProvider == p
        let prov = providers.first(where: { $0.provider == p })
        return Button {
            withAnimation(.easeInOut(duration: 0.15)) { selectedProvider = p }
        } label: {
            HStack(spacing: 4) {
                if let prov, p != "all" {
                    Circle()
                        .fill(prov.keyConfigured ? ArchonTheme.success : ArchonTheme.muted)
                        .frame(width: 6, height: 6)
                }
                Text(p == "all" ? "All" : p.capitalized)
                    .font(.caption.bold())
                if let prov, p != "all" {
                    Text("(\(prov.enabledModels)/\(prov.totalModels))")
                        .font(.caption2)
                        .foregroundStyle(isActive ? .black.opacity(0.6) : ArchonTheme.muted)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(isActive ? ArchonTheme.accent : ArchonTheme.card)
            .foregroundStyle(isActive ? .black : ArchonTheme.text)
            .clipShape(Capsule())
        }
    }

    // MARK: - Provider section

    private func providerSection(_ providerName: String, models: [LLMModel]) -> some View {
        let prov = providers.first(where: { $0.provider == providerName })
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(providerName.capitalized)
                    .font(.headline)
                if let prov {
                    if prov.keyConfigured {
                        Label("API Key ✓", systemImage: "key.fill")
                            .font(.caption2.bold())
                            .foregroundStyle(ArchonTheme.success)
                    } else {
                        Label("No API Key", systemImage: "key.slash")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 4)

            ForEach(models) { model in
                modelRow(model)
            }
        }
    }

    // MARK: - Model row

    private func modelRow(_ model: LLMModel) -> some View {
        HStack(alignment: .center, spacing: 12) {
            // Toggle
            Toggle("", isOn: Binding(
                get: { model.enabled },
                set: { newVal in Task { await toggle(model, enabled: newVal) } }
            ))
            .labelsHidden()
            .tint(ArchonTheme.accent)
            .disabled(!model.keyConfigured && model.provider != "ollama")

            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(model.display)
                        .font(.subheadline.bold())
                        .foregroundStyle(model.enabled ? ArchonTheme.text : ArchonTheme.muted)
                    tierBadge(model.tier)
                }
                // Capability chips
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 4) {
                        ForEach(model.capabilities, id: \.self) { cap in
                            capChip(cap)
                        }
                        Text("\(model.contextK)k ctx")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(ArchonTheme.background)
                            .clipShape(Capsule())
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(ArchonTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(model.enabled ? ArchonTheme.accent.opacity(0.3) : Color.white.opacity(0.06), lineWidth: 1)
        )
        .opacity(model.keyConfigured || model.provider == "ollama" ? 1.0 : 0.5)
    }

    @ViewBuilder
    private func tierBadge(_ tier: String) -> some View {
        let color: Color = switch tier {
            case "premium":  Color(red: 0.98, green: 0.72, blue: 0.0)
            case "standard": ArchonTheme.accent
            case "economy":  ArchonTheme.muted
            case "local":    Color(red: 0.2, green: 0.7, blue: 0.4)
            default:         ArchonTheme.muted
        }
        Text(tier.capitalized)
            .font(.caption2.bold())
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.18))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }

    private func capChip(_ cap: String) -> some View {
        let icon = capIcon(cap)
        return Label(cap, systemImage: icon)
            .font(.caption2)
            .foregroundStyle(ArchonTheme.accent.opacity(0.9))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(ArchonTheme.accent.opacity(0.1))
            .clipShape(Capsule())
    }

    private func capIcon(_ cap: String) -> String {
        switch cap {
        case "reasoning":    return "brain"
        case "code":         return "chevron.left.forwardslash.chevron.right"
        case "fast":         return "bolt.fill"
        case "long_context": return "doc.text.fill"
        case "vision":       return "eye.fill"
        case "search":       return "magnifyingglass"
        case "finance":      return "chart.line.uptrend.xyaxis"
        case "writing":      return "pencil"
        case "agents":       return "cpu"
        default:             return "star"
        }
    }

    // MARK: - Route sheet

    private var routeSheet: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 20) {
                Text("Ask the router which model to use for a given task type.")
                    .font(.subheadline)
                    .foregroundStyle(ArchonTheme.muted)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Task Type").font(.caption.bold()).foregroundStyle(ArchonTheme.muted)
                    TextField("e.g. code, reasoning, finance, writing…", text: $routeTaskType)
                        .textFieldStyle(.roundedBorder)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                }

                Button {
                    Task { await testRoute() }
                } label: {
                    HStack {
                        if isRouting { ProgressView().tint(.white).scaleEffect(0.8) }
                        Text(isRouting ? "Routing…" : "Find Best Model")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(ArchonTheme.accent)
                    .foregroundStyle(.black)
                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                }
                .disabled(routeTaskType.isEmpty || isRouting)

                if let route = routeResult {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Recommended Model", systemImage: "checkmark.seal.fill")
                            .font(.caption.bold())
                            .foregroundStyle(ArchonTheme.success)

                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(route.display)
                                    .font(.title3.bold())
                                Text("\(route.provider.capitalized) · \(route.capability)")
                                    .font(.caption)
                                    .foregroundStyle(ArchonTheme.muted)
                            }
                            Spacer()
                            Image(systemName: "arrow.triangle.branch")
                                .font(.title2)
                                .foregroundStyle(ArchonTheme.accent)
                        }
                        Text(route.reason)
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    .archonCard()
                }

                Spacer()
            }
            .padding()
            .background(ArchonTheme.background.ignoresSafeArea())
            .foregroundStyle(ArchonTheme.text)
            .navigationTitle("Smart Route")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { showRouteSheet = false }
                }
            }
        }
        .preferredColorScheme(.dark)
    }

    // MARK: - Network

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            async let m: [LLMModel]     = HubClient.shared.get("/api/models")
            async let p: [LLMProvider]  = HubClient.shared.get("/api/models/providers")
            (models, providers) = try await (m, p)
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func toggle(_ model: LLMModel, enabled: Bool) async {
        struct ToggleBody: Encodable { let provider: String; let modelId: String; let enabled: Bool }
        do {
            let _: LLMModel = try await HubClient.shared.put(
                "/api/models/toggle",
                body: ToggleBody(provider: model.provider, modelId: model.modelId, enabled: enabled)
            )
            if let idx = models.firstIndex(where: { $0.id == model.id }) {
                models[idx] = LLMModel(
                    provider: model.provider, modelId: model.modelId, display: model.display,
                    capabilities: model.capabilities, contextK: model.contextK, tier: model.tier,
                    key: model.key, keyConfigured: model.keyConfigured, enabled: enabled
                )
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func testRoute() async {
        isRouting = true
        defer { isRouting = false }
        struct RouteBody: Encodable { let taskType: String; let agentId: String }
        do {
            routeResult = try await HubClient.shared.post(
                "/api/models/route",
                body: RouteBody(taskType: routeTaskType, agentId: "")
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { ModelsView() }
        .preferredColorScheme(.dark)
}
