import SwiftUI

struct ChatView: View {
    @State private var conversations: [Conversation] = []
    @State private var selectedConversation: Conversation?
    @State private var messages: [Message] = []
    @State private var draft = ""
    @State private var errorMessage = ""
    @State private var isLoadingMessages = false

    var body: some View {
        NavigationSplitView {
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
            .scrollContentBackground(.hidden)
            .background(ArchonTheme.background)
            .navigationTitle("Conversations")
            .toolbar {
                Button {
                    Task { await createConversation() }
                } label: {
                    Image(systemName: "plus.bubble.fill")
                        .foregroundStyle(ArchonTheme.accent)
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
}

#Preview {
    ChatView()
        .preferredColorScheme(.dark)
}
