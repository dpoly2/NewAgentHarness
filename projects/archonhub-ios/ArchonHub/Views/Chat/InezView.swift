import SwiftUI

// MARK: - Inez Message Model

struct InezMessage: Identifiable, Hashable {
    let id = UUID().uuidString
    let role: InezRole
    let content: String
    let dispatches: [InezDispatch]
    let followupSuggestions: [String]
    let timestamp: Date

    init(role: InezRole, content: String, dispatches: [InezDispatch] = [], followupSuggestions: [String] = [], timestamp: Date = .now) {
        self.role = role
        self.content = content
        self.dispatches = dispatches
        self.followupSuggestions = followupSuggestions
        self.timestamp = timestamp
    }
}

enum InezRole: Hashable {
    case user
    case inez
    case thinking
}

// MARK: - InezView

struct InezView: View {
    @EnvironmentObject var hubClient: HubClient

    @State private var messages: [InezMessage] = []
    @State private var draft = ""
    @State private var conversationId: String?
    @State private var isThinking = false
    @State private var thinkingStep = ""
    @State private var errorMessage = ""
    @State private var showMemory = false
    @State private var inezStatus: InezStatusResponse?
    @State private var showStatusHUD = true

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let inezLavender = Color(red: 0.77, green: 0.71, blue: 0.99)

    private func contextualGreeting() -> String {
        let hour = Calendar.current.component(.hour, from: .now)
        switch hour {
        case 5..<12: return "Good morning, David. I've reviewed the operation."
        case 12..<17: return "Good afternoon, David. I'm up to speed."
        case 17..<21: return "Good evening, David. Here's where things stand."
        default: return "David. I'm active and monitoring."
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            inezHeader

            // ── Awareness HUD (collapsible) ───────────────────────────────
            if showStatusHUD, let status = inezStatus, status.urgentCount > 0 {
                awarenessHUD(status)
            }

            // ── Quick Actions ─────────────────────────────────────────────
            quickActions

            // ── Messages ──────────────────────────────────────────────────
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 14) {
                        ForEach(messages) { msg in
                            messageRow(msg).id(msg.id)
                        }
                        if isThinking {
                            thinkingRow.id("thinking")
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .background(ArchonTheme.background)
                .onChange(of: messages) {
                    withAnimation(.easeOut(duration: 0.2)) {
                        proxy.scrollTo(messages.last?.id ?? "thinking", anchor: .bottom)
                    }
                }
                .onChange(of: isThinking) {
                    if isThinking {
                        withAnimation { proxy.scrollTo("thinking", anchor: .bottom) }
                    }
                }
            }

            if !errorMessage.isEmpty {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.error)
                    .padding(.horizontal, 16)
                    .padding(.top, 4)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            composer
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Inez")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showMemory = true
                } label: {
                    Image(systemName: "brain.head.profile")
                        .foregroundStyle(inezLavender)
                }
            }
        }
        .sheet(isPresented: $showMemory) {
            NavigationStack {
                InezMemoryView(conversationId: conversationId)
                    .environmentObject(hubClient)
                    .navigationTitle("Memory")
                    .navigationBarTitleDisplayMode(.large)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") { showMemory = false }
                        }
                    }
            }
            .presentationDetents([.medium, .large])
        }
        .task {
            if messages.isEmpty {
                messages.append(InezMessage(role: .inez, content: contextualGreeting()))
            }
            await loadStatus()
        }
        .onReceive(hubClient.wsEvents) { event in
            guard event.type == "inez_thinking", let step = event.text, !step.isEmpty else { return }
            withAnimation(.easeInOut(duration: 0.2)) { thinkingStep = step }
        }
    }

    // MARK: - Header

    private var inezHeader: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(inezPurple)
                    .frame(width: 44, height: 44)
                    .shadow(color: inezPurple.opacity(0.5), radius: 6)
                Text("👑")
                    .font(.title3)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text("INEZ")
                    .font(.headline.weight(.bold))
                    .foregroundStyle(inezLavender)
                    .tracking(1.5)
                Text("Intelligent Neural Executive Zone")
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 3) {
                HStack(spacing: 4) {
                    Circle()
                        .fill(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.warning)
                        .frame(width: 7, height: 7)
                    Text(hubClient.isOnline ? "ACTIVE" : "OFFLINE")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.warning)
                        .tracking(0.8)
                }
                if let status = inezStatus, status.urgentCount > 0 {
                    Text("\(status.urgentCount) need attention")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.error)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(ArchonTheme.card)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(inezPurple.opacity(0.3))
                .frame(height: 1)
        }
    }

    // MARK: - Awareness HUD

    private func awarenessHUD(_ status: InezStatusResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .font(.caption2)
                    .foregroundStyle(inezLavender)
                Text("INEZ AWARENESS")
                    .font(.caption2.weight(.semibold))
                    .tracking(1)
                    .foregroundStyle(inezLavender)
                Spacer()
                Button {
                    withAnimation { showStatusHUD = false }
                } label: {
                    Image(systemName: "xmark")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }

            Text(status.awareness.components(separatedBy: "\n").first ?? status.awareness)
                .font(.caption)
                .foregroundStyle(ArchonTheme.text)
                .lineLimit(3)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(inezPurple.opacity(0.08))
        .overlay(
            RoundedRectangle(cornerRadius: 0)
                .stroke(inezPurple.opacity(0.2), lineWidth: 1)
        )
    }

    // MARK: - Quick Actions

    private var quickActions: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                quickActionButton("Status", icon: "waveform") {
                    send(text: "What's the current status of all missions?")
                }
                quickActionButton("Brief Me", icon: "newspaper") {
                    send(text: "Give me a morning briefing.")
                }
                quickActionButton("Priorities", icon: "exclamationmark.triangle") {
                    send(text: "What needs my immediate attention?")
                }
                quickActionButton("Recommendations", icon: "lightbulb") {
                    send(text: "What do you recommend I focus on today?")
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .background(ArchonTheme.card)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(ArchonTheme.muted.opacity(0.15))
                .frame(height: 1)
        }
    }

    private func quickActionButton(_ label: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 5) {
                Image(systemName: icon)
                    .font(.caption2)
                Text(label)
                    .font(.caption.weight(.medium))
            }
            .foregroundStyle(inezLavender)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(inezPurple.opacity(0.12))
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(inezPurple.opacity(0.3), lineWidth: 1)
            )
        }
        .disabled(isThinking)
    }

    // MARK: - Message rows

    @ViewBuilder
    private func messageRow(_ msg: InezMessage) -> some View {
        switch msg.role {
        case .user: userBubble(msg)
        case .inez: inezBubble(msg)
        case .thinking: thinkingRow
        }
    }

    private func userBubble(_ msg: InezMessage) -> some View {
        HStack {
            Spacer(minLength: 60)
            VStack(alignment: .trailing, spacing: 4) {
                Text(msg.content)
                    .foregroundStyle(ArchonTheme.text)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(ArchonTheme.accent.opacity(0.22))
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                Text(msg.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)
            }
        }
    }

    private func inezBubble(_ msg: InezMessage) -> some View {
        HStack(alignment: .top, spacing: 10) {
            ZStack {
                Circle()
                    .fill(inezPurple)
                    .frame(width: 30, height: 30)
                Text("👑")
                    .font(.caption)
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Text("Inez")
                        .font(.caption.bold())
                        .foregroundStyle(inezLavender)
                    Text(msg.timestamp, style: .time)
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }

                Text(msg.content)
                    .foregroundStyle(ArchonTheme.text)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(ArchonTheme.card)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .stroke(inezPurple.opacity(0.4), lineWidth: 1)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                if !msg.dispatches.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("DEPLOYING AGENTS")
                            .font(.caption2.weight(.semibold))
                            .tracking(0.8)
                            .foregroundStyle(ArchonTheme.muted)
                        ForEach(msg.dispatches) { dispatch in
                            dispatchCard(dispatch)
                        }
                    }
                }
                
                // Follow-up suggestions
                if !msg.followupSuggestions.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("SUGGESTED FOLLOW-UPS")
                            .font(.caption2.weight(.semibold))
                            .tracking(0.8)
                            .foregroundStyle(ArchonTheme.muted)
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(msg.followupSuggestions, id: \.self) { question in
                                    Button {
                                        send(text: question)
                                    } label: {
                                        Text(question)
                                            .font(.caption)
                                            .foregroundStyle(inezLavender)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(inezPurple.opacity(0.1))
                                            .clipShape(Capsule())
                                            .overlay(
                                                Capsule()
                                                    .stroke(inezPurple.opacity(0.25), lineWidth: 1)
                                            )
                                    }
                                    .disabled(isThinking)
                                }
                            }
                        }
                    }
                }
            }

            Spacer(minLength: 40)
        }
    }

    private func dispatchCard(_ dispatch: InezDispatch) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "cpu.fill")
                .font(.caption2)
                .foregroundStyle(inezPurple)
            VStack(alignment: .leading, spacing: 2) {
                Text(agentDisplayName(dispatch.agentId ?? "agent"))
                    .font(.caption2.bold())
                    .foregroundStyle(inezLavender)
                if let task = dispatch.task {
                    Text(task.prefix(60) + (task.count > 60 ? "…" : ""))
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
            Spacer()
            if let graph = dispatch.graph {
                Text(graph.uppercased())
                    .font(.system(size: 9, weight: .medium))
                    .tracking(0.5)
                    .foregroundStyle(ArchonTheme.muted)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(ArchonTheme.background)
                    .clipShape(Capsule())
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
        .background(inezPurple.opacity(0.06))
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(inezPurple.opacity(0.2), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }

    /// Map agent IDs to Agent Command Network names where applicable.
    private func agentDisplayName(_ agentId: String) -> String {
        let mapping: [String: String] = [
            "grants-research-agent": "Atlas — Research",
            "markets-intelligence-desk": "Atlas — Intelligence",
            "markets-cio": "Athena — Strategy",
            "finance-cfo": "Ledger — Finance",
            "xftc-plugin-dev": "Forge — Dev",
            "s2t-webdev-agent": "Forge — Web",
            "xftc-frontend-dev": "Forge — Frontend",
            "finance-bookkeeper": "Ledger — Accounting",
            "business-law-project-lead": "Guardian — Legal",
            "holdings-legal-agent": "Guardian — Compliance",
            "nightking-design-agent": "Creator — Design",
            "nutrue-brand-agent": "Creator — Brand",
        ]
        return mapping[agentId] ?? agentId
    }

    private var thinkingRow: some View {
        HStack(alignment: .top, spacing: 10) {
            ZStack {
                Circle()
                    .fill(inezPurple)
                    .frame(width: 30, height: 30)
                Text("👑")
                    .font(.caption)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Inez")
                    .font(.caption.bold())
                    .foregroundStyle(inezLavender)
                HStack(spacing: 6) {
                    BouncingDotsView()
                    Text(thinkingStep.isEmpty ? "Processing..." : thinkingStep)
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.muted)
                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                        .id(thinkingStep)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(ArchonTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(inezPurple.opacity(0.4), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }

            Spacer(minLength: 40)
        }
    }

    // MARK: - Composer

    private var composer: some View {
        HStack(spacing: 12) {
            TextField("Message Inez...", text: $draft, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...5)
                .disabled(isThinking)

            Button {
                send(text: draft)
            } label: {
                Image(systemName: isThinking ? "ellipsis" : "paperplane.fill")
                    .foregroundStyle(ArchonTheme.background)
                    .padding(10)
                    .background(isThinking ? ArchonTheme.muted : inezPurple)
                    .clipShape(Circle())
            }
            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isThinking)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(ArchonTheme.card)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(ArchonTheme.muted.opacity(0.2))
                .frame(height: 1)
        }
    }

    // MARK: - Actions

    private func send(text: String) {
        let content = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty, !isThinking else { return }
        if text == draft { draft = "" }
        errorMessage = ""
        messages.append(InezMessage(role: .user, content: content))
        isThinking = true

        Task {
            do {
                let response: InezChatResponse = try await HubClient.shared.post(
                    "/api/inez/chat",
                    body: InezChatRequest(message: content, conversationId: conversationId)
                )
                conversationId = response.conversationId
                isThinking = false
                thinkingStep = ""
                messages.append(InezMessage(
                    role: .inez,
                    content: response.inezMessage,
                    dispatches: response.dispatches,
                    followupSuggestions: response.followupSuggestions ?? []
                ))
                await loadStatus()
            } catch {
                isThinking = false
                thinkingStep = ""
                errorMessage = error.localizedDescription
                messages.append(InezMessage(role: .inez, content: "I ran into an issue: \(error.localizedDescription)"))
            }
        }
    }

    private func loadStatus() async {
        guard hubClient.isOnline else { return }
        do {
            let status: InezStatusResponse = try await HubClient.shared.get("/api/inez/status")
            inezStatus = status
            if status.urgentCount > 0 { showStatusHUD = true }
        } catch {
            // Status is optional — fail silently
        }
    }
}

// MARK: - Bouncing Dots

private struct BouncingDotsView: View {
    @State private var animate = false

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3, id: \.self) { i in
                Circle()
                    .fill(Color(red: 0.77, green: 0.71, blue: 0.99))
                    .frame(width: 6, height: 6)
                    .offset(y: animate ? -4 : 0)
                    .animation(
                        .easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.15),
                        value: animate
                    )
            }
        }
        .onAppear { animate = true }
    }
}

#Preview {
    NavigationStack {
        InezView()
            .environmentObject(HubClient.shared)
            .preferredColorScheme(.dark)
    }
}
