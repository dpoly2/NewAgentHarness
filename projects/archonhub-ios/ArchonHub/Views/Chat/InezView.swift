import SwiftUI

// MARK: - Inez Message Model

struct InezMessage: Identifiable, Hashable {
    let id = UUID()
    let role: InezRole
    let content: String
    let dispatches: [InezDispatch]
    let timestamp: Date

    init(role: InezRole, content: String, dispatches: [InezDispatch] = [], timestamp: Date = .now) {
        self.role = role
        self.content = content
        self.dispatches = dispatches
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
    @State private var errorMessage = ""

    private let welcomeMessage = InezMessage(
        role: .inez,
        content: "Good to see you. I'm Inez — your Chief of Staff. What do you need?"
    )

    var body: some View {
        VStack(spacing: 0) {
            // ── Header ────────────────────────────────────────────────────
            inezHeader

            // ── Messages ─────────────────────────────────────────────────
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 14) {
                        ForEach(messages) { msg in
                            messageRow(msg)
                                .id(msg.id)
                        }

                        if isThinking {
                            thinkingRow
                                .id("thinking")
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

            // ── Error banner ──────────────────────────────────────────────
            if !errorMessage.isEmpty {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.error)
                    .padding(.horizontal, 16)
                    .padding(.top, 4)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            // ── Composer ──────────────────────────────────────────────────
            composer
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Inez")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if messages.isEmpty {
                messages.append(welcomeMessage)
            }
        }
    }

    // MARK: - Header

    private var inezHeader: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color(red: 0.49, green: 0.23, blue: 0.93))
                    .frame(width: 44, height: 44)
                Text("👑")
                    .font(.title3)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text("Inez")
                    .font(.headline)
                    .foregroundStyle(Color(red: 0.77, green: 0.71, blue: 0.99))
                Text("Chief of Staff · Smith Capital Portfolio")
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)
            }

            Spacer()

            Circle()
                .fill(hubClient.isOnline ? ArchonTheme.success : ArchonTheme.warning)
                .frame(width: 8, height: 8)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(ArchonTheme.card)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(ArchonTheme.muted.opacity(0.2))
                .frame(height: 1)
        }
    }

    // MARK: - Message rows

    @ViewBuilder
    private func messageRow(_ msg: InezMessage) -> some View {
        switch msg.role {
        case .user:
            userBubble(msg)
        case .inez:
            inezBubble(msg)
        case .thinking:
            thinkingRow
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
                    .fill(Color(red: 0.49, green: 0.23, blue: 0.93))
                    .frame(width: 30, height: 30)
                Text("👑")
                    .font(.caption)
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Text("Inez")
                        .font(.caption.bold())
                        .foregroundStyle(Color(red: 0.77, green: 0.71, blue: 0.99))
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
                            .stroke(Color(red: 0.49, green: 0.23, blue: 0.93).opacity(0.5), lineWidth: 1)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                // Dispatch cards
                if !msg.dispatches.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Deploying agents:")
                            .font(.caption2.bold())
                            .foregroundStyle(ArchonTheme.muted)
                        ForEach(msg.dispatches) { dispatch in
                            dispatchCard(dispatch)
                        }
                    }
                }
            }

            Spacer(minLength: 40)
        }
    }

    private func dispatchCard(_ dispatch: InezDispatch) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "cpu")
                .font(.caption2)
                .foregroundStyle(ArchonTheme.accent)
            VStack(alignment: .leading, spacing: 2) {
                Text(dispatch.agentId ?? "agent")
                    .font(.caption2.bold())
                    .foregroundStyle(ArchonTheme.accent)
                if let project = dispatch.project, !project.isEmpty {
                    Text(project)
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
            Spacer()
            if let graph = dispatch.graph {
                Text(graph)
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(ArchonTheme.background)
                    .clipShape(Capsule())
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(ArchonTheme.accent.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }

    private var thinkingRow: some View {
        HStack(alignment: .top, spacing: 10) {
            ZStack {
                Circle()
                    .fill(Color(red: 0.49, green: 0.23, blue: 0.93))
                    .frame(width: 30, height: 30)
                Text("👑")
                    .font(.caption)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Inez")
                    .font(.caption.bold())
                    .foregroundStyle(Color(red: 0.77, green: 0.71, blue: 0.99))
                HStack(spacing: 4) {
                    BouncingDotsView()
                    Text("Thinking...")
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.muted)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(ArchonTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(Color(red: 0.49, green: 0.23, blue: 0.93).opacity(0.5), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }

            Spacer(minLength: 40)
        }
    }

    // MARK: - Composer

    private var composer: some View {
        HStack(spacing: 12) {
            TextField("Ask Inez anything...", text: $draft, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...5)
                .disabled(isThinking)

            Button {
                Task { await send() }
            } label: {
                Image(systemName: "paperplane.fill")
                    .foregroundStyle(ArchonTheme.background)
                    .padding(10)
                    .background(
                        isThinking
                        ? ArchonTheme.muted
                        : Color(red: 0.49, green: 0.23, blue: 0.93)
                    )
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

    // MARK: - Send

    private func send() async {
        let content = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }
        draft = ""
        errorMessage = ""

        messages.append(InezMessage(role: .user, content: content))
        isThinking = true

        do {
            let response: InezChatResponse = try await HubClient.shared.post(
                "/api/inez/chat",
                body: InezChatRequest(message: content, conversationId: conversationId)
            )
            conversationId = response.conversationId
            isThinking = false
            messages.append(InezMessage(
                role: .inez,
                content: response.inezMessage,
                dispatches: response.dispatches
            ))
        } catch {
            isThinking = false
            errorMessage = error.localizedDescription
            messages.append(InezMessage(
                role: .inez,
                content: "I ran into an issue: \(error.localizedDescription)"
            ))
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
                        .easeInOut(duration: 0.5)
                            .repeatForever()
                            .delay(Double(i) * 0.15),
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
