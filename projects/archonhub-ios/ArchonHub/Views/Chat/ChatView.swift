import SwiftUI

// MARK: - Search Result Model

struct SearchResult: Identifiable, Codable {
    let messageId: String
    let conversationId: String
    let conversationTitle: String
    let conversationSlug: String?
    let role: String
    let excerpt: String
    let createdAt: String?
    
    var id: String { messageId }
}

struct SearchResponse: Codable {
    let query: String
    let count: Int
    let results: [SearchResult]
}

struct ChatView: View {
    @EnvironmentObject var hubClient: HubClient
    
    @State private var conversations: [Conversation] = []
    @State private var selectedConversation: Conversation?
    @State private var messages: [Message] = []
    @State private var draft = ""
    @State private var errorMessage = ""
    @State private var isLoadingMessages = false
    
    // Search state
    @State private var searchText = ""
    @State private var searchResults: [SearchResult] = []
    @State private var isSearching = false

    var body: some View {
        NavigationSplitView {
            Group {
                if searchText.isEmpty {
                    // Normal conversation list
                    List(conversations, selection: $selectedConversation) { conversation in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(conversation.title)
                                .font(.headline)
                            Text(ArchonDateFormatter.relativeString(conversation.createdAt))
                                .font(.caption)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                        .padding(.vertical, 4)
                        .listRowBackground(ArchonTheme.card)
                    }
                } else {
                    // Search results
                    List(searchResults) { result in
                        Button {
                            // Navigate to conversation containing this message
                            if let conv = conversations.first(where: { $0.id == result.conversationId }) {
                                selectedConversation = conv
                                searchText = "" // Clear search
                            }
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text(result.role.uppercased())
                                        .font(.caption2.weight(.semibold))
                                        .foregroundStyle(ArchonTheme.accent)
                                    Text("in")
                                        .font(.caption2)
                                        .foregroundStyle(ArchonTheme.muted)
                                    Text(result.conversationTitle)
                                        .font(.caption2.bold())
                                        .foregroundStyle(ArchonTheme.text)
                                }
                                Text(result.excerpt)
                                    .font(.caption)
                                    .foregroundStyle(ArchonTheme.muted)
                                    .lineLimit(3)
                                if let createdAt = result.createdAt {
                                    Text(ArchonDateFormatter.relativeString(createdAt))
                                        .font(.caption2)
                                        .foregroundStyle(ArchonTheme.muted.opacity(0.7))
                                }
                            }
                            .padding(.vertical, 4)
                        }
                        .listRowBackground(ArchonTheme.card)
                    }
                    .overlay {
                        if isSearching {
                            ProgressView()
                                .tint(ArchonTheme.accent)
                        } else if searchResults.isEmpty && !searchText.isEmpty {
                            VStack(spacing: 8) {
                                Image(systemName: "magnifyingglass")
                                    .font(.largeTitle)
                                    .foregroundStyle(ArchonTheme.muted)
                                Text("No results for '\(searchText)'")
                                    .foregroundStyle(ArchonTheme.muted)
                            }
                        }
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(ArchonTheme.background)
            .navigationTitle(searchText.isEmpty ? "Conversations" : "Search Results")
            .searchable(text: $searchText, prompt: "Search conversations")
            .onChange(of: searchText) {
                Task {
                    await performSearch()
                }
            }
            .toolbar {
                if searchText.isEmpty {
                    Button {
                        Task { await createConversation() }
                    } label: {
                        Image(systemName: "plus.bubble.fill")
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }
            }
        } detail: {
            VStack(spacing: 0) {
                if let conversation = selectedConversation {
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(messages) { message in
                                    HStack {
                                        if message.role.lowercased() == "user" {
                                            Spacer(minLength: 40)
                                        }

                                        VStack(alignment: .leading, spacing: 6) {
                                            Text(message.content)
                                                .foregroundStyle(ArchonTheme.text)
                                            Text(ArchonDateFormatter.timestampString(message.createdAt))
                                                .font(.caption2)
                                                .foregroundStyle(ArchonTheme.muted)
                                        }
                                        .padding(12)
                                        .background(message.role.lowercased() == "user" ? ArchonTheme.accent.opacity(0.18) : ArchonTheme.card)
                                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                                        .frame(maxWidth: 280, alignment: message.role.lowercased() == "user" ? .trailing : .leading)

                                        if message.role.lowercased() != "user" {
                                            Spacer(minLength: 40)
                                        }
                                    }
                                    .id(message.id)
                                }
                            }
                            .padding()
                        }
                        .background(ArchonTheme.background)
                        .onChange(of: messages) {
                            if let id = messages.last?.id {
                                withAnimation {
                                    proxy.scrollTo(id, anchor: .bottom)
                                }
                            }
                        }
                    }

                    composer(for: conversation)
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "message")
                            .font(.largeTitle)
                            .foregroundStyle(ArchonTheme.accent)
                        Text("Select or create a conversation.")
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(ArchonTheme.background)
                }
            }
            .navigationTitle(selectedConversation?.title ?? "Chat")
            .toolbarRole(.editor)
        }
        .foregroundStyle(ArchonTheme.text)
        .background(ArchonTheme.background.ignoresSafeArea())
        .task {
            await loadConversations()
        }
        .onChange(of: selectedConversation) {
            Task {
                await loadMessages()
            }
        }
        .overlay(alignment: .top) {
            if !errorMessage.isEmpty {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(ArchonTheme.error)
                    .padding(.top, 8)
            }
        }
    }

    private func composer(for conversation: Conversation) -> some View {
        HStack(spacing: 12) {
            TextField("Send a message", text: $draft, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...4)

            Button {
                Task { await sendMessage(to: conversation) }
            } label: {
                Image(systemName: "paperplane.fill")
                    .foregroundStyle(.black)
                    .padding(10)
                    .background(ArchonTheme.accent)
                    .clipShape(Circle())
            }
            .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isLoadingMessages)
        }
        .padding()
        .background(ArchonTheme.card)
    }

    private func loadConversations() async {
        do {
            conversations = try await HubClient.shared.get("/api/conversations")
            if selectedConversation == nil {
                selectedConversation = conversations.first
            }
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadMessages() async {
        guard let selectedConversation else { return }
        isLoadingMessages = true
        defer { isLoadingMessages = false }

        do {
            messages = try await HubClient.shared.get("/api/conversations/\(selectedConversation.id)/messages")
            errorMessage = ""
        } catch {
            messages = []
            errorMessage = error.localizedDescription
        }
    }

    private func createConversation() async {
        struct CreateConversationRequest: Encodable {
            let title: String
        }

        let title = "Conversation \(Date.now.formatted(date: .omitted, time: .shortened))"

        do {
            let created: Conversation = try await HubClient.shared.post("/api/conversations", body: CreateConversationRequest(title: title))
            conversations.insert(created, at: 0)
            selectedConversation = created
            messages = []
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func sendMessage(to conversation: Conversation) async {
        struct MessageCreateRequest: Encodable {
            let role: String
            let content: String
        }

        let content = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }

        do {
            let created: Message = try await HubClient.shared.post(
                "/api/conversations/\(conversation.id)/messages",
                body: MessageCreateRequest(role: "user", content: content)
            )
            draft = ""
            messages.append(created)
            errorMessage = ""
            await loadMessages()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    private func performSearch() async {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Clear results if query is empty or too short
        guard query.count >= 2 else {
            searchResults = []
            return
        }
        
        // Debounce: wait a bit before searching
        try? await Task.sleep(nanoseconds: 300_000_000) // 300ms
        
        // Check if search text changed while we were waiting
        guard query == searchText.trimmingCharacters(in: .whitespacesAndNewlines) else {
            return
        }
        
        isSearching = true
        errorMessage = ""
        
        do {
            let response: SearchResponse = try await HubClient.shared.get(
                "/api/search",
                queryItems: [
                    URLQueryItem(name: "q", value: query),
                    URLQueryItem(name: "limit", value: "50")
                ]
            )
            searchResults = response.results
        } catch {
            errorMessage = "Search failed: \(error.localizedDescription)"
            searchResults = []
        }
        
        isSearching = false
    }
}

#Preview {
    ChatView()
        .preferredColorScheme(.dark)
}
