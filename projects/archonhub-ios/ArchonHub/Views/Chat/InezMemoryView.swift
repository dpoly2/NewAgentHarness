import SwiftUI

// MARK: - Server Models

struct InezMemoryResponse: Codable {
    let shortTerm: [ShortTermMessage]
    var savedFacts: [SavedFact]
    let dailySessions: [DailySession]

    enum CodingKeys: String, CodingKey {
        case shortTerm = "short_term"
        case savedFacts = "saved_facts"
        case dailySessions = "daily_sessions"
    }
}

struct ShortTermMessage: Codable, Identifiable {
    var id: String { "\(role)-\(createdAt)" }
    let role: String
    let content: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case role, content
        case createdAt = "created_at"
    }
}

struct SavedFact: Codable, Identifiable {
    var id: String { key }
    let key: String
    let value: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case key, value
        case updatedAt = "updated_at"
    }
}

struct DailySession: Codable, Identifiable {
    var id: String { date }
    let date: String
    let conversations: [SessionConversation]
    let count: Int
}

struct SessionConversation: Codable, Identifiable {
    let id: String
    let title: String
    let slug: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, title, slug
        case updatedAt = "updated_at"
    }
}

// MARK: - Main View

struct InezMemoryView: View {
    @EnvironmentObject var hubClient: HubClient
    let conversationId: String?

    @State private var memory: InezMemoryResponse?
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var selectedDate: String?
    @State private var deletingKey: String?

    private let inezPurple = Color(red: 0.77, green: 0.71, blue: 0.99)

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if isLoading {
                    HStack { Spacer(); ProgressView(); Spacer() }
                        .padding(.top, 40)
                } else if let memory {
                    shortTermSection(memory.shortTerm)
                    savedFactsSection(memory.savedFacts)
                    dailySessionsSection(memory.dailySessions)
                } else if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.error)
                        .padding(.horizontal, 16)
                }
            }
            .padding(.vertical, 16)
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .task { await loadMemory() }
    }

    // MARK: - Short-term Memory

    @ViewBuilder
    private func shortTermSection(_ messages: [ShortTermMessage]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(
                icon: "clock.fill",
                title: "Short-term Memory",
                subtitle: "Context from the current conversation, updated every ~10 messages"
            )

            if messages.isEmpty {
                emptyState("No messages in current conversation yet.")
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(alignment: .top, spacing: 10) {
                        ForEach(messages) { msg in
                            shortTermCard(msg)
                        }
                    }
                    .padding(.horizontal, 16)
                }
            }
        }
    }

    private func shortTermCard(_ msg: ShortTermMessage) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 4) {
                Image(systemName: msg.role == "user" ? "person.fill" : "crown.fill")
                    .font(.caption2)
                    .foregroundStyle(msg.role == "user" ? ArchonTheme.accent : inezPurple)
                Text(msg.role == "user" ? "You" : "Inez")
                    .font(.caption2.bold())
                    .foregroundStyle(msg.role == "user" ? ArchonTheme.accent : inezPurple)
            }
            Text(msg.content.prefix(120) + (msg.content.count > 120 ? "…" : ""))
                .font(.caption)
                .foregroundStyle(ArchonTheme.text)
                .lineLimit(4)
        }
        .padding(12)
        .frame(width: 200, alignment: .topLeading)
        .background(ArchonTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Saved Facts

    @ViewBuilder
    private func savedFactsSection(_ facts: [SavedFact]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(
                icon: "bookmark.fill",
                title: "Saved Facts",
                subtitle: "Key facts that persist across all conversations"
            )

            if facts.isEmpty {
                emptyState("No saved facts yet. Inez saves key info from your conversations.")
            } else {
                VStack(spacing: 8) {
                    ForEach(facts) { fact in
                        savedFactRow(fact)
                    }
                }
                .padding(.horizontal, 16)
            }
        }
    }

    private func savedFactRow(_ fact: SavedFact) -> some View {
        HStack(alignment: .top, spacing: 10) {
            VStack(alignment: .leading, spacing: 4) {
                Text(fact.key.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.caption.bold())
                    .foregroundStyle(inezPurple)
                Text(fact.value)
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
            Button {
                Task { await deleteFact(fact.key) }
            } label: {
                Image(systemName: "trash")
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.muted)
            }
            .disabled(deletingKey == fact.key)
        }
        .padding(12)
        .background(ArchonTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }

    // MARK: - Daily Sessions Calendar

    @ViewBuilder
    private func dailySessionsSection(_ sessions: [DailySession]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader(
                icon: "calendar",
                title: "Daily Sessions",
                subtitle: "A summary of each day's conversations"
            )

            if sessions.isEmpty {
                emptyState("No past sessions found.")
            } else {
                VStack(spacing: 0) {
                    ForEach(sessions) { session in
                        dailySessionRow(session)
                        Divider().background(ArchonTheme.muted.opacity(0.3))
                    }
                }
                .background(ArchonTheme.card)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding(.horizontal, 16)
            }
        }
    }

    private func dailySessionRow(_ session: DailySession) -> some View {
        DisclosureGroup(
            isExpanded: Binding(
                get: { selectedDate == session.date },
                set: { selectedDate = $0 ? session.date : nil }
            )
        ) {
            VStack(spacing: 0) {
                ForEach(session.conversations) { conv in
                    HStack(spacing: 10) {
                        Image(systemName: "bubble.left.fill")
                            .font(.caption)
                            .foregroundStyle(inezPurple)
                        Text(conv.title.isEmpty ? "Conversation" : conv.title)
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.text)
                            .lineLimit(1)
                        Spacer()
                        Text(shortTime(conv.updatedAt))
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    .padding(.vertical, 8)
                    .padding(.horizontal, 16)
                    Divider().background(ArchonTheme.muted.opacity(0.2))
                }
            }
        } label: {
            HStack {
                Text(formattedDate(session.date))
                    .font(.subheadline.bold())
                    .foregroundStyle(ArchonTheme.text)
                Spacer()
                Text("\(session.count) conversation\(session.count == 1 ? "" : "s")")
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.muted)
            }
            .padding(.vertical, 10)
            .padding(.horizontal, 16)
        }
        .tint(inezPurple)
    }

    // MARK: - Helpers

    private func sectionHeader(icon: String, title: String, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(inezPurple)
                Text(title)
                    .font(.headline)
                    .foregroundStyle(ArchonTheme.text)
            }
            Text(subtitle)
                .font(.caption)
                .foregroundStyle(ArchonTheme.muted)
        }
        .padding(.horizontal, 16)
    }

    private func emptyState(_ text: String) -> some View {
        Text(text)
            .font(.caption)
            .foregroundStyle(ArchonTheme.muted)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 16)
    }

    private func formattedDate(_ iso: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        if let date = formatter.date(from: iso) {
            let display = DateFormatter()
            display.dateStyle = .medium
            return display.string(from: date)
        }
        return iso
    }

    private func shortTime(_ iso: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: iso) {
            let display = DateFormatter()
            display.timeStyle = .short
            return display.string(from: date)
        }
        return ""
    }

    // MARK: - Data loading

    private func loadMemory() async {
        isLoading = true
        errorMessage = ""
        do {
            var path = "/api/inez/memory"
            if let cid = conversationId, !cid.isEmpty {
                path += "?conversation_id=\(cid)"
            }
            let result: InezMemoryResponse = try await hubClient.get(path)
            memory = result
        } catch {
            errorMessage = "Could not load memory: \(error.localizedDescription)"
        }
        isLoading = false
    }

    private func deleteFact(_ key: String) async {
        deletingKey = key
        do {
            let encodedKey = key.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? key
            try await hubClient.delete("/api/inez/memory/facts/\(encodedKey)")
            memory?.savedFacts.removeAll { $0.key == key }
        } catch {
            // silently ignore — fact will still show until next refresh
        }
        deletingKey = nil
    }
}
