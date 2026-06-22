import SwiftUI
import Speech
import AVFoundation
import PhotosUI
import UniformTypeIdentifiers

// MARK: - Pending File Upload Model

struct PendingFileUpload: Identifiable {
    let id = UUID()
    let filename: String
    let data: Data
    let mimeType: String
    
    var icon: String {
        if mimeType.contains("pdf") {
            return "doc.text.fill"
        } else if mimeType.hasPrefix("image/") {
            return "photo.fill"
        } else if mimeType.contains("spreadsheet") || mimeType.contains("csv") || mimeType.contains("excel") {
            return "tablecells.fill"
        } else {
            return "doc.fill"
        }
    }
    
    var formattedSize: String {
        let kb = Double(data.count) / 1024
        let mb = kb / 1024
        
        if mb >= 1 {
            return String(format: "%.1f MB", mb)
        } else {
            return String(format: "%.0f KB", kb)
        }
    }
}

// MARK: - File Attachment Chip View

struct FileAttachmentChip: View {
    let file: PendingFileUpload
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: file.icon)
                .font(.caption)
                .foregroundStyle(.white)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(file.filename)
                    .font(.caption2.weight(.medium))
                    .foregroundStyle(.white)
                    .lineLimit(1)
                
                Text(file.formattedSize)
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.7))
            }
            
            Button {
                onRemove()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.6))
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(red: 0.49, green: 0.23, blue: 0.93))
        )
    }
}

// MARK: - Inez Message Model

struct InezMessage: Identifiable, Hashable {
    let id = UUID().uuidString
    let role: InezRole
    let content: String
    let dispatches: [InezDispatch]
    let followupSuggestions: [String]
    let timestamp: Date
    let attachedFiles: [UploadedFile]

    init(role: InezRole, content: String, dispatches: [InezDispatch] = [], followupSuggestions: [String] = [], timestamp: Date = .now, attachedFiles: [UploadedFile] = []) {
        self.role = role
        self.content = content
        self.dispatches = dispatches
        self.followupSuggestions = followupSuggestions
        self.timestamp = timestamp
        self.attachedFiles = attachedFiles
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
    
    // Prompt templates state
    @State private var showTemplates = false
    @State private var templates: [PromptTemplate] = []
    @State private var isLoadingTemplates = false
    
    // Voice input state
    @State private var isRecording = false
    @State private var speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var audioEngine = AVAudioEngine()
    
    // File upload state
    @State private var pendingUploads: [PendingFileUpload] = []
    @State private var showPhotoPicker = false
    @State private var showDocumentPicker = false
    @State private var selectedPhotoItem: PhotosPickerItem?
    @State private var isUploading = false

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
        .sheet(isPresented: $showTemplates) {
            NavigationStack {
                promptTemplatesView
                    .navigationTitle("Prompt Templates")
                    .navigationBarTitleDisplayMode(.large)
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") { showTemplates = false }
                        }
                    }
            }
            .presentationDetents([.large])
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
                // Templates button
                quickActionButton("Templates", icon: "doc.text.fill") {
                    Task { await loadTemplates() }
                    showTemplates = true
                }
                
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
                
                // Display file attachments
                if !msg.attachedFiles.isEmpty {
                    VStack(alignment: .trailing, spacing: 6) {
                        ForEach(msg.attachedFiles) { file in
                            HStack(spacing: 8) {
                                Image(systemName: file.icon)
                                    .font(.caption)
                                    .foregroundStyle(inezPurple)
                                
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(file.filename)
                                        .font(.caption2.bold())
                                        .foregroundStyle(ArchonTheme.text)
                                    Text(file.formattedSize)
                                        .font(.caption2)
                                        .foregroundStyle(ArchonTheme.muted)
                                }
                                
                                Image(systemName: file.statusIcon)
                                    .font(.caption2)
                                    .foregroundStyle(file.parsingStatus == "complete" ? ArchonTheme.success : ArchonTheme.warning)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(ArchonTheme.card)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(ArchonTheme.muted.opacity(0.2), lineWidth: 1)
                            )
                        }
                    }
                }
                
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
        VStack(spacing: 0) {
            // File attachments preview
            if !pendingUploads.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(pendingUploads) { upload in
                            FileAttachmentChip(file: upload) {
                                pendingUploads.removeAll { $0.id == upload.id }
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                }
                .background(ArchonTheme.card)
                
                Divider()
            }
            
            HStack(spacing: 12) {
                // File attachment button
                Menu {
                    Button {
                        showPhotoPicker = true
                    } label: {
                        Label("Photos", systemImage: "photo.fill")
                    }
                    
                    Button {
                        showDocumentPicker = true
                    } label: {
                        Label("Documents", systemImage: "doc.fill")
                    }
                } label: {
                    Image(systemName: "paperclip")
                        .foregroundStyle(inezLavender)
                        .padding(10)
                        .background(inezPurple.opacity(0.15))
                        .clipShape(Circle())
                }
                .disabled(isThinking || isRecording)
                
                // Microphone button for voice input
                Button {
                    if isRecording {
                        stopRecording()
                    } else {
                        startRecording()
                    }
                } label: {
                    Image(systemName: isRecording ? "stop.circle.fill" : "mic.fill")
                        .foregroundStyle(isRecording ? ArchonTheme.error : inezLavender)
                        .padding(10)
                        .background(isRecording ? ArchonTheme.error.opacity(0.2) : inezPurple.opacity(0.15))
                        .clipShape(Circle())
                }
                .disabled(isThinking)
                
                TextField("Message Inez...", text: $draft, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...5)
                    .disabled(isThinking || isRecording)

                Button {
                    Task {
                        await sendWithAttachments()
                    }
                } label: {
                    if isUploading {
                        ProgressView()
                            .tint(.white)
                            .padding(10)
                            .background(inezPurple)
                            .clipShape(Circle())
                    } else {
                        Image(systemName: isThinking ? "ellipsis" : "paperplane.fill")
                            .foregroundStyle(ArchonTheme.background)
                            .padding(10)
                            .background(isThinking ? ArchonTheme.muted : inezPurple)
                            .clipShape(Circle())
                    }
                }
                .disabled((draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && pendingUploads.isEmpty) || isThinking || isUploading)
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
        .photosPicker(isPresented: $showPhotoPicker, selection: $selectedPhotoItem, matching: .images)
        .fileImporter(
            isPresented: $showDocumentPicker,
            allowedContentTypes: [.pdf, .commaSeparatedText, .spreadsheet, .text, .plainText],
            allowsMultipleSelection: false
        ) { result in
            if case .success(let urls) = result, let url = urls.first {
                handleDocumentSelection(url)
            }
        }
        .onChange(of: selectedPhotoItem) { oldValue, newValue in
            if let item = newValue {
                handlePhotoSelection(item)
                selectedPhotoItem = nil
            }
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
                    body: InezChatRequest(message: content, conversationId: conversationId, fileIds: nil)
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
    
    // MARK: - Voice Input
    
    private func startRecording() {
        // Request speech recognition authorization
        SFSpeechRecognizer.requestAuthorization { authStatus in
            DispatchQueue.main.async {
                guard authStatus == .authorized else {
                    errorMessage = "Speech recognition not authorized"
                    return
                }
                
                guard let recognizer = speechRecognizer, recognizer.isAvailable else {
                    errorMessage = "Speech recognition not available"
                    return
                }
                
                do {
                    try startRecognitionTask()
                } catch {
                    errorMessage = "Could not start recording: \(error.localizedDescription)"
                }
            }
        }
    }
    
    private func startRecognitionTask() throws {
        // Cancel any ongoing task
        recognitionTask?.cancel()
        recognitionTask = nil
        
        // Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        
        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw NSError(domain: "SpeechError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Unable to create recognition request"])
        }
        
        recognitionRequest.shouldReportPartialResults = true
        
        // Get audio input node
        let inputNode = audioEngine.inputNode
        
        // Start recognition task
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { result, error in
            let isFinal = result?.isFinal ?? false
            
            if let result = result {
                // Update draft with transcribed text
                DispatchQueue.main.async {
                    self.draft = result.bestTranscription.formattedString
                }
            }
            
            if error != nil || isFinal {
                // Stop recording on error or final result
                DispatchQueue.main.async {
                    self.stopRecording()
                }
            }
        }
        
        // Configure audio tap
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        // Start audio engine
        audioEngine.prepare()
        try audioEngine.start()
        
        isRecording = true
        
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
    }
    
    private func stopRecording() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        
        recognitionTask?.cancel()
        recognitionTask = nil
        
        isRecording = false
        
        // Haptic feedback
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
    }
    
    // MARK: - Prompt Templates
    
    private var promptTemplatesView: some View {
        Group {
            if isLoadingTemplates {
                ProgressView()
                    .tint(inezLavender)
            } else if templates.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "doc.text")
                        .font(.largeTitle)
                        .foregroundStyle(ArchonTheme.muted)
                    Text("No templates available")
                        .foregroundStyle(ArchonTheme.muted)
                }
            } else {
                List {
                    ForEach(templatesByCategory(), id: \.category) { group in
                        Section(header: Text(group.category.uppercased())) {
                            ForEach(group.templates) { template in
                                Button {
                                    useTemplate(template)
                                } label: {
                                    VStack(alignment: .leading, spacing: 6) {
                                        HStack {
                                            Text(template.title)
                                                .font(.headline)
                                                .foregroundStyle(ArchonTheme.text)
                                            Spacer()
                                            if template.usageCount > 0 {
                                                Text("\(template.usageCount)×")
                                                    .font(.caption2)
                                                    .foregroundStyle(ArchonTheme.muted)
                                            }
                                        }
                                        Text(template.promptText.prefix(100) + (template.promptText.count > 100 ? "..." : ""))
                                            .font(.caption)
                                            .foregroundStyle(ArchonTheme.muted)
                                            .lineLimit(2)
                                    }
                                    .padding(.vertical, 4)
                                }
                                .listRowBackground(ArchonTheme.card)
                            }
                        }
                    }
                }
                .scrollContentBackground(.hidden)
                .background(ArchonTheme.background)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(ArchonTheme.background)
    }
    
    private struct TemplateGroup {
        let category: String
        let templates: [PromptTemplate]
    }
    
    private func templatesByCategory() -> [TemplateGroup] {
        let grouped = Dictionary(grouping: templates, by: { $0.category })
        let sorted = grouped.keys.sorted()
        return sorted.map { TemplateGroup(category: $0, templates: grouped[$0]!) }
    }
    
    private func useTemplate(_ template: PromptTemplate) {
        // Fill draft with template text
        draft = template.promptText
        
        // Increment usage count on server (fire and forget)
        Task {
            do {
                struct UsageResponse: Decodable {
                    let success: Bool?
                }
                let _: UsageResponse = try await HubClient.shared.post(
                    "/api/prompt-templates/\(template.id)/use",
                    body: EmptyBody()
                )
            } catch {
                // Silent fail - usage count is not critical
            }
        }
        
        // Close templates sheet
        showTemplates = false
    }
    
    private func loadTemplates() async {
        isLoadingTemplates = true
        do {
            templates = try await HubClient.shared.get("/api/prompt-templates")
        } catch {
            errorMessage = "Failed to load templates: \(error.localizedDescription)"
            templates = []
        }
        isLoadingTemplates = false
    }
    
    // MARK: - File Upload Actions
    
    private func sendWithAttachments() async {
        var uploadedFiles: [UploadedFile] = []
        
        // Upload files if any
        if !pendingUploads.isEmpty {
            isUploading = true
            uploadedFiles = await uploadFiles()
            isUploading = false
        }
        
        // Send message
        let content = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // If we have files but no text, create a default message
        let messageText = content.isEmpty && !uploadedFiles.isEmpty 
            ? "I've uploaded \(uploadedFiles.count) file(s). Please analyze them."
            : content
        
        guard !messageText.isEmpty else { return }
        
        draft = ""
        errorMessage = ""
        
        // Add user message with attachments
        messages.append(InezMessage(
            role: .user,
            content: messageText,
            attachedFiles: uploadedFiles
        ))
        
        isThinking = true

        Task {
            do {
                // Include file IDs in the request
                let fileIds = uploadedFiles.map { $0.fileId }
                
                let response: InezChatResponse = try await HubClient.shared.post(
                    "/api/inez/chat",
                    body: InezChatRequest(
                        message: messageText,
                        conversationId: conversationId,
                        fileIds: fileIds.isEmpty ? nil : fileIds
                    )
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
            } catch {
                isThinking = false
                errorMessage = error.localizedDescription
            }
        }
    }
    
    func handlePhotoSelection(_ item: PhotosPickerItem) {
        Task {
            if let data = try? await item.loadTransferable(type: Data.self) {
                let filename = "image-\(UUID().uuidString.prefix(8)).jpg"
                let mimeType = "image/jpeg"
                
                let upload = PendingFileUpload(
                    filename: filename,
                    data: data,
                    mimeType: mimeType
                )
                
                await MainActor.run {
                    pendingUploads.append(upload)
                }
            }
        }
    }
    
    func handleDocumentSelection(_ url: URL) {
        guard url.startAccessingSecurityScopedResource() else { return }
        defer { url.stopAccessingSecurityScopedResource() }
        
        do {
            let data = try Data(contentsOf: url)
            let filename = url.lastPathComponent
            
            let mimeType: String
            let ext = url.pathExtension.lowercased()
            
            switch ext {
            case "pdf": mimeType = "application/pdf"
            case "csv": mimeType = "text/csv"
            case "xlsx", "xls": mimeType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            case "docx": mimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            case "txt": mimeType = "text/plain"
            case "png": mimeType = "image/png"
            case "jpg", "jpeg": mimeType = "image/jpeg"
            default: mimeType = "application/octet-stream"
            }
            
            let upload = PendingFileUpload(
                filename: filename,
                data: data,
                mimeType: mimeType
            )
            
            pendingUploads.append(upload)
        } catch {
            print("Error loading document: \(error)")
        }
    }
    
    func uploadFiles() async -> [UploadedFile] {
        var uploadedFiles: [UploadedFile] = []
        
        for pendingUpload in pendingUploads {
            do {
                let boundary = UUID().uuidString
                var body = Data()
                
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(pendingUpload.filename)\"\r\n".data(using: .utf8)!)
                body.append("Content-Type: \(pendingUpload.mimeType)\r\n\r\n".data(using: .utf8)!)
                body.append(pendingUpload.data)
                body.append("\r\n".data(using: .utf8)!)
                
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"filename\"\r\n\r\n".data(using: .utf8)!)
                body.append(pendingUpload.filename.data(using: .utf8)!)
                body.append("\r\n".data(using: .utf8)!)
                
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"mime_type\"\r\n\r\n".data(using: .utf8)!)
                body.append(pendingUpload.mimeType.data(using: .utf8)!)
                body.append("\r\n".data(using: .utf8)!)
                
                body.append("--\(boundary)--\r\n".data(using: .utf8)!)
                
                // Construct URL manually since buildURL is private
                let serverURL = hubClient.serverURL
                guard var components = URLComponents(string: serverURL) else {
                    throw APIError.invalidURL
                }
                components.path = "/api/files/upload"
                guard let url = components.url else {
                    throw APIError.invalidURL
                }
                
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
                
                // Add authorization header if available
                let token = hubClient.currentToken
                if !token.isEmpty {
                    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                }
                
                request.httpBody = body
                
                let (data, _) = try await URLSession.shared.data(for: request)
                let response = try JSONDecoder().decode(FileUploadResponse.self, from: data)
                
                if response.success, let fileInfo = response.file {
                    let uploadedFile = UploadedFile(
                        fileId: fileInfo.fileId,
                        filename: fileInfo.filename,
                        fileType: fileInfo.fileType,
                        mimeType: pendingUpload.mimeType,
                        fileSize: fileInfo.fileSize,
                        parsingStatus: fileInfo.status,
                        uploadedAt: ISO8601DateFormatter().string(from: Date()),
                        parsedContent: nil,
                        metadata: nil
                    )
                    uploadedFiles.append(uploadedFile)
                }
            } catch {
                print("Upload failed for \(pendingUpload.filename): \(error)")
            }
        }
        
        pendingUploads.removeAll()
        return uploadedFiles
    }
}

// MARK: - Empty Request Helper

private struct EmptyRequest: Codable {}

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
