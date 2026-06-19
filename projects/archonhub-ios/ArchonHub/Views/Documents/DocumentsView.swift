import SwiftUI

// MARK: - Request Models
struct DocumentCreateRequest: Codable {
    let title: String
    let docType: String
    let content: String
    let format: String
    let projectSlug: String
    let clientId: String
    let tags: [String]
    let createdBy: String
    
    enum CodingKeys: String, CodingKey {
        case title
        case docType = "doc_type"
        case content
        case format
        case projectSlug = "project_slug"
        case clientId = "client_id"
        case tags
        case createdBy = "created_by"
    }
}

struct DocumentUpdateRequest: Codable {
    let title: String
    let content: String
    let docType: String
    
    enum CodingKeys: String, CodingKey {
        case title
        case content
        case docType = "doc_type"
    }
}

struct DeleteResponse: Codable {
    let id: String
    let deleted: Bool
}

struct DocumentsView: View {
    @State private var documents: [Document] = []
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var searchText = ""
    @State private var filterType: String = "all"
    @State private var showingAddSheet = false
    @State private var selectedDocument: Document?
    
    private let docTypes = ["all", "general", "contract", "proposal", "invoice", "note"]
    
    private var filteredDocuments: [Document] {
        var filtered = documents
        
        if filterType != "all" {
            filtered = filtered.filter { $0.docType == filterType }
        }
        
        if !searchText.isEmpty {
            filtered = filtered.filter {
                $0.title.localizedCaseInsensitiveContains(searchText) ||
                $0.content.localizedCaseInsensitiveContains(searchText)
            }
        }
        
        return filtered
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Documents")
                        .font(.largeTitle.bold())
                    Spacer()
                    Button {
                        showingAddSheet = true
                    } label: {
                        Label("New", systemImage: "plus.circle.fill")
                            .font(.caption.bold())
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(ArchonTheme.accent)
                    .controlSize(.small)
                    
                    Button { Task { await loadDocuments() } } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }
                
                // Search bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(ArchonTheme.muted)
                    TextField("Search documents...", text: $searchText)
                        .textFieldStyle(.plain)
                }
                .padding(10)
                .background(ArchonTheme.card)
                .cornerRadius(8)
                
                // Type filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(docTypes, id: \.self) { type in
                            Button {
                                filterType = type
                            } label: {
                                Text(type.capitalized)
                                    .font(.caption.bold())
                                    .foregroundStyle(filterType == type ? .white : ArchonTheme.muted)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(filterType == type ? ArchonTheme.accent : ArchonTheme.card)
                                    .cornerRadius(20)
                            }
                        }
                    }
                }
            }
            .padding()
            .background(ArchonTheme.background)
            
            // Document list
            if isLoading && documents.isEmpty {
                Spacer()
                ProgressView()
                    .tint(ArchonTheme.accent)
                Spacer()
            } else if !errorMessage.isEmpty {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 48))
                        .foregroundStyle(Color.orange)
                    Text(errorMessage)
                        .foregroundStyle(ArchonTheme.muted)
                        .multilineTextAlignment(.center)
                    Button("Retry") {
                        Task { await loadDocuments() }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(ArchonTheme.accent)
                }
                .padding()
                Spacer()
            } else if filteredDocuments.isEmpty {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 48))
                        .foregroundStyle(ArchonTheme.muted)
                    Text(searchText.isEmpty ? "No documents yet" : "No matching documents")
                        .foregroundStyle(ArchonTheme.muted)
                    if searchText.isEmpty {
                        Button("Create First Document") {
                            showingAddSheet = true
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(ArchonTheme.accent)
                    }
                }
                .padding()
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(filteredDocuments) { doc in
                            documentRow(doc)
                                .onTapGesture {
                                    selectedDocument = doc
                                }
                        }
                    }
                    .padding()
                }
            }
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .task {
            await loadDocuments()
        }
        .sheet(isPresented: $showingAddSheet) {
            AddDocumentView { newDoc in
                documents.insert(newDoc, at: 0)
            }
        }
        .sheet(item: $selectedDocument) { doc in
            DocumentDetailView(document: doc) { updated in
                if let index = documents.firstIndex(where: { $0.id == updated.id }) {
                    documents[index] = updated
                }
            } onDelete: {
                documents.removeAll { $0.id == doc.id }
            }
        }
    }
    
    @ViewBuilder
    private func documentRow(_ doc: Document) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(doc.title)
                        .font(.headline)
                        .foregroundStyle(.white)
                    
                    if let preview = doc.content.prefix(100).split(separator: "\n").first {
                        Text(String(preview))
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                            .lineLimit(2)
                    }
                }
                Spacer()
                
                // Type badge
                Text(doc.docType)
                    .font(.caption2.bold())
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(typeColor(doc.docType))
                    .cornerRadius(4)
            }
            
            HStack {
                if let tags = doc.tags, !tags.isEmpty {
                    HStack(spacing: 4) {
                        ForEach(tags.prefix(3), id: \.self) { tag in
                            Text("#\(tag)")
                                .font(.caption2)
                                .foregroundStyle(ArchonTheme.accent)
                        }
                        if tags.count > 3 {
                            Text("+\(tags.count - 3)")
                                .font(.caption2)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                    }
                }
                
                Spacer()
                
                if let date = ArchonDateFormatter.parse(doc.updatedAt) {
                    Text(date.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
        }
        .padding()
        .background(ArchonTheme.card)
        .cornerRadius(12)
    }
    
    private func typeColor(_ type: String) -> Color {
        switch type {
        case "contract": return Color.purple
        case "proposal": return Color.blue
        case "invoice": return Color.green
        case "note": return Color.orange
        default: return Color.gray
        }
    }
    
    private func loadDocuments() async {
        isLoading = true
        defer { isLoading = false }
        do {
            print("📄 Fetching documents from /api/documents")
            let docs: [Document] = try await HubClient.shared.get("/api/documents")
            documents = docs
            errorMessage = ""
            print("✅ Loaded \(docs.count) documents")
            
            // Debug: print first few document titles
            if !docs.isEmpty {
                print("Documents loaded:")
                for (index, doc) in docs.prefix(5).enumerated() {
                    print("  \(index + 1). \(doc.title) (type: \(doc.docType), updated: \(doc.updatedAt))")
                }
                if docs.count > 5 {
                    print("  ... and \(docs.count - 5) more")
                }
            }
        } catch {
            print("❌ Failed to load documents: \(error)")
            errorMessage = "Failed to load documents"
        }
    }
}

// MARK: - Add Document View
struct AddDocumentView: View {
    @Environment(\.dismiss) var dismiss
    @State private var title = ""
    @State private var docType = "general"
    @State private var content = ""
    @State private var projectSlug = ""
    @State private var tags = ""
    @State private var isSubmitting = false
    
    let onCreate: (Document) -> Void
    
    private let docTypes = ["general", "contract", "proposal", "invoice", "note"]
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Basic Info") {
                    TextField("Title", text: $title)
                    Picker("Type", selection: $docType) {
                        ForEach(docTypes, id: \.self) { type in
                            Text(type.capitalized).tag(type)
                        }
                    }
                }
                
                Section("Content") {
                    TextEditor(text: $content)
                        .frame(minHeight: 200)
                }
                
                Section("Optional") {
                    TextField("Project Slug", text: $projectSlug)
                    TextField("Tags (comma-separated)", text: $tags)
                }
            }
            .navigationTitle("New Document")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task { await createDocument() }
                    }
                    .disabled(title.isEmpty || isSubmitting)
                }
            }
        }
    }
    
    private func createDocument() async {
        isSubmitting = true
        defer { isSubmitting = false }
        
        let tagArray = tags.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        
        let request = DocumentCreateRequest(
            title: title,
            docType: docType,
            content: content,
            format: "markdown",
            projectSlug: projectSlug,
            clientId: "",
            tags: tagArray,
            createdBy: "ios-app"
        )
        
        do {
            let doc: Document = try await HubClient.shared.post("/api/documents", body: request)
            onCreate(doc)
            dismiss()
        } catch {
            print("❌ Failed to create document: \(error)")
        }
    }
}

// MARK: - Document Detail View
struct DocumentDetailView: View {
    @Environment(\.dismiss) var dismiss
    let document: Document
    let onUpdate: (Document) -> Void
    let onDelete: () -> Void
    
    @State private var isEditing = false
    @State private var editedTitle = ""
    @State private var editedContent = ""
    @State private var editedType = ""
    @State private var isDeleting = false
    @State private var showDeleteConfirm = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    if isEditing {
                        TextField("Title", text: $editedTitle)
                            .font(.title.bold())
                            .textFieldStyle(.plain)
                        
                        Picker("Type", selection: $editedType) {
                            ForEach(["general", "contract", "proposal", "invoice", "note"], id: \.self) { type in
                                Text(type.capitalized).tag(type)
                            }
                        }
                        .pickerStyle(.segmented)
                        
                        TextEditor(text: $editedContent)
                            .frame(minHeight: 300)
                    } else {
                        Text(document.title)
                            .font(.title.bold())
                        
                        HStack {
                            Text(document.docType.capitalized)
                                .font(.caption.bold())
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.blue)
                                .cornerRadius(4)
                            
                            if let date = ArchonDateFormatter.parse(document.updatedAt) {
                                Text("Updated \(date.formatted(date: .abbreviated, time: .shortened))")
                                    .font(.caption)
                                    .foregroundStyle(ArchonTheme.muted)
                            }
                        }
                        
                        if let tags = document.tags, !tags.isEmpty {
                            HStack(spacing: 8) {
                                ForEach(tags, id: \.self) { tag in
                                    Text("#\(tag)")
                                        .font(.caption)
                                        .foregroundStyle(ArchonTheme.accent)
                                }
                            }
                        }
                        
                        Divider()
                        
                        Text(document.content)
                            .font(.body)
                    }
                }
                .padding()
            }
            .background(ArchonTheme.background.ignoresSafeArea())
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                
                if isEditing {
                    ToolbarItem(placement: .primaryAction) {
                        Button("Save") {
                            Task { await saveChanges() }
                        }
                    }
                } else {
                    ToolbarItem(placement: .primaryAction) {
                        Button("Edit") {
                            editedTitle = document.title
                            editedContent = document.content
                            editedType = document.docType
                            isEditing = true
                        }
                    }
                    
                    ToolbarItem(placement: .destructiveAction) {
                        Button("Delete", role: .destructive) {
                            showDeleteConfirm = true
                        }
                    }
                }
            }
            .alert("Delete Document", isPresented: $showDeleteConfirm) {
                Button("Cancel", role: .cancel) { }
                Button("Delete", role: .destructive) {
                    Task { await deleteDocument() }
                }
            } message: {
                Text("Are you sure you want to delete \"\(document.title)\"? This cannot be undone.")
            }
        }
    }
    
    private func saveChanges() async {
        let request = DocumentUpdateRequest(
            title: editedTitle,
            content: editedContent,
            docType: editedType
        )
        
        do {
            let updated: Document = try await HubClient.shared.put("/api/documents/\(document.id)", body: request)
            onUpdate(updated)
            isEditing = false
        } catch {
            print("❌ Failed to update document: \(error)")
        }
    }
    
    private func deleteDocument() async {
        isDeleting = true
        defer { isDeleting = false }
        
        do {
            try await HubClient.shared.delete("/api/documents/\(document.id)")
            onDelete()
            dismiss()
        } catch {
            print("❌ Failed to delete document: \(error)")
        }
    }
}

#Preview {
    NavigationStack { DocumentsView() }
        .preferredColorScheme(.dark)
}
