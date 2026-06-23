import SwiftUI

// MARK: - Memory View

struct MemoryView: View {
    @EnvironmentObject var hubClient: HubClient

    @State private var facts: [GlobalMemoryFact] = []
    @State private var counts: [String: Int] = [:]
    @State private var categories: [String] = []
    @State private var selectedCategory: String? = nil
    @State private var searchText = ""
    @State private var isLoading = false
    @State private var showAddFact = false
    @State private var editingFact: GlobalMemoryFact? = nil
    @State private var errorMessage = ""

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)

    var filteredFacts: [GlobalMemoryFact] {
        var result = facts
        if let cat = selectedCategory {
            result = result.filter { $0.category == cat }
        }
        if !searchText.isEmpty {
            result = result.filter {
                $0.key.localizedCaseInsensitiveContains(searchText) ||
                $0.value.localizedCaseInsensitiveContains(searchText)
            }
        }
        return result
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            categoryFilter
            searchBar
            
            if isLoading {
                Spacer()
                ProgressView("Loading memory...")
                    .foregroundStyle(ArchonTheme.muted)
                Spacer()
            } else if filteredFacts.isEmpty {
                emptyState
            } else {
                factsList
            }
        }
        .background(ArchonTheme.background)
        .sheet(isPresented: $showAddFact) {
            MemoryFactEditorView(fact: nil) { saved in
                Task { await loadFacts() }
            }
        }
        .sheet(item: $editingFact) { fact in
            MemoryFactEditorView(fact: fact) { saved in
                Task { await loadFacts() }
            }
        }
        .task { await loadFacts() }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("GLOBAL MEMORY")
                    .font(.caption.weight(.semibold))
                    .tracking(1.2)
                    .foregroundStyle(ArchonTheme.muted)
                Text("Persistent Knowledge")
                    .font(.title3.bold())
                    .foregroundStyle(ArchonTheme.text)
            }
            Spacer()
            HStack(spacing: 8) {
                Text("\(facts.count) facts")
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.muted)
                Button {
                    showAddFact = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .foregroundStyle(inezPurple)
                        .font(.title3)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(ArchonTheme.card)
    }

    // MARK: - Category Filter

    private var categoryFilter: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                categoryChip(label: "All", category: nil, count: facts.count)
                ForEach(categories, id: \.self) { cat in
                    categoryChip(label: cat.capitalized, category: cat, count: counts[cat] ?? 0)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(ArchonTheme.card)
        .overlay(alignment: .bottom) {
            Rectangle().fill(ArchonTheme.muted.opacity(0.15)).frame(height: 1)
        }
    }

    private func categoryChip(label: String, category: String?, count: Int) -> some View {
        let isSelected = selectedCategory == category
        return Button {
            withAnimation(.easeInOut(duration: 0.2)) {
                selectedCategory = category
            }
        } label: {
            HStack(spacing: 4) {
                Text(label)
                    .font(.caption.weight(isSelected ? .semibold : .regular))
                Text("\(count)")
                    .font(.caption2)
                    .opacity(0.7)
            }
            .foregroundStyle(isSelected ? .white : ArchonTheme.muted)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(isSelected ? inezPurple : ArchonTheme.muted.opacity(0.12))
            .clipShape(Capsule())
        }
    }

    // MARK: - Search Bar

    private var searchBar: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(ArchonTheme.muted)
                .font(.caption)
            TextField("Search memory...", text: $searchText)
                .font(.subheadline)
                .foregroundStyle(ArchonTheme.text)
            if !searchText.isEmpty {
                Button { searchText = "" } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(ArchonTheme.muted)
                        .font(.caption)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(ArchonTheme.muted.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(ArchonTheme.background)
    }

    // MARK: - Facts List

    private var factsList: some View {
        List {
            ForEach(filteredFacts) { fact in
                FactRowView(fact: fact)
                    .listRowBackground(ArchonTheme.card)
                    .listRowSeparatorTint(ArchonTheme.muted.opacity(0.2))
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) {
                            Task { await deleteFact(fact) }
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                        Button {
                            editingFact = fact
                        } label: {
                            Label("Edit", systemImage: "pencil")
                        }
                        .tint(inezPurple)
                    }
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "brain.head.profile")
                .font(.system(size: 48))
                .foregroundStyle(inezPurple.opacity(0.5))
            Text(searchText.isEmpty ? "No memory facts yet" : "No results for \"\(searchText)\"")
                .font(.headline)
                .foregroundStyle(ArchonTheme.text)
            Text("Add facts to help Inez and all agents\nremember what matters to you.")
                .font(.subheadline)
                .foregroundStyle(ArchonTheme.muted)
                .multilineTextAlignment(.center)
            if searchText.isEmpty {
                Button {
                    showAddFact = true
                } label: {
                    Text("Add First Fact")
                        .font(.subheadline.bold())
                        .foregroundStyle(.white)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 10)
                        .background(inezPurple)
                        .clipShape(Capsule())
                }
            }
            Spacer()
        }
        .padding()
    }

    // MARK: - Actions

    private func loadFacts() async {
        isLoading = true
        do {
            let response: GlobalMemoryResponse = try await HubClient.shared.get("/api/memory/global")
            facts = response.facts
            counts = response.counts ?? [:]
            categories = response.categories ?? []
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func deleteFact(_ fact: GlobalMemoryFact) async {
        do {
            try await HubClient.shared.delete("/api/memory/global/\(fact.id)")
            facts.removeAll { $0.id == fact.id }
            if let cat = counts[fact.category] {
                counts[fact.category] = max(0, cat - 1)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Fact Row View

struct FactRowView: View {
    let fact: GlobalMemoryFact

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)

    var importanceColor: Color {
        if fact.importance >= 9 { return ArchonTheme.error }
        if fact.importance >= 7 { return ArchonTheme.warning }
        return ArchonTheme.muted
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Category icon
            Image(systemName: fact.categoryIcon)
                .font(.caption)
                .foregroundStyle(inezPurple)
                .frame(width: 28, height: 28)
                .background(inezPurple.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 6))

            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(fact.key.replacingOccurrences(of: "_", with: " ").capitalized)
                        .font(.subheadline.bold())
                        .foregroundStyle(ArchonTheme.text)
                    Spacer()
                    // Importance indicator
                    HStack(spacing: 2) {
                        ForEach(0..<3, id: \.self) { i in
                            Circle()
                                .fill(i < (fact.importance / 4) ? importanceColor : ArchonTheme.muted.opacity(0.3))
                                .frame(width: 5, height: 5)
                        }
                    }
                }

                Text(fact.value)
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.muted)
                    .lineLimit(3)

                HStack(spacing: 8) {
                    Label(fact.category, systemImage: "tag")
                        .font(.caption2)
                        .foregroundStyle(inezPurple.opacity(0.8))
                    Label(fact.source.replacingOccurrences(of: "_", with: " "), systemImage: "arrow.down.circle")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                    if fact.usageCount > 0 {
                        Label("\(fact.usageCount)×", systemImage: "arrow.clockwise")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                }
            }
        }
        .padding(.vertical, 6)
    }
}

// MARK: - Fact Editor

struct MemoryFactEditorView: View {
    let fact: GlobalMemoryFact?
    let onSave: (GlobalMemoryFact) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var category = "preferences"
    @State private var key = ""
    @State private var value = ""
    @State private var importance = 5
    @State private var isSaving = false
    @State private var errorMessage = ""

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let allCategories = ["preferences","projects","people","deadlines","ministry","technical","rules","finance"]

    init(fact: GlobalMemoryFact?, onSave: @escaping (GlobalMemoryFact) -> Void) {
        self.fact = fact
        self.onSave = onSave
        if let f = fact {
            _category = State(initialValue: f.category)
            _key = State(initialValue: f.key)
            _value = State(initialValue: f.value)
            _importance = State(initialValue: f.importance)
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Category") {
                    Picker("Category", selection: $category) {
                        ForEach(allCategories, id: \.self) { cat in
                            Text(cat.capitalized).tag(cat)
                        }
                    }
                    .pickerStyle(.menu)
                }

                Section("Fact") {
                    TextField("Key (e.g. sermon_prep_day)", text: $key)
                        .autocorrectionDisabled()
                    TextField("Value", text: $value, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section("Importance (1–10)") {
                    Stepper("\(importance) — \(importanceLabel)", value: $importance, in: 1...10)
                }

                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(ArchonTheme.error)
                            .font(.caption)
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(ArchonTheme.background)
            .navigationTitle(fact == nil ? "New Memory Fact" : "Edit Fact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isSaving ? "Saving…" : "Save") {
                        Task { await save() }
                    }
                    .disabled(key.isEmpty || value.isEmpty || isSaving)
                    .bold()
                }
            }
        }
    }

    private var importanceLabel: String {
        switch importance {
        case 9...10: return "Critical"
        case 7...8:  return "High"
        case 5...6:  return "Medium"
        default:     return "Low"
        }
    }

    private func save() async {
        isSaving = true
        errorMessage = ""
        do {
            let body = MemoryFactRequest(
                category: category,
                key: key.lowercased().replacingOccurrences(of: " ", with: "_"),
                value: value,
                importance: importance,
                source: "user"
            )
            if let existing = fact {
                struct SaveResponse: Decodable {
                    let success: Bool
                    let fact: GlobalMemoryFact
                }
                let response: SaveResponse = try await HubClient.shared.put(
                    "/api/memory/global/\(existing.id)", body: body)
                if response.success {
                    onSave(response.fact)
                    dismiss()
                }
            } else {
                struct SaveResponse: Decodable {
                    let success: Bool
                    let fact: GlobalMemoryFact
                }
                let response: SaveResponse = try await HubClient.shared.post(
                    "/api/memory/global", body: body)
                if response.success {
                    onSave(response.fact)
                    dismiss()
                }
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isSaving = false
    }
}

#Preview {
    NavigationStack {
        MemoryView()
            .environmentObject(HubClient.shared)
            .preferredColorScheme(.dark)
    }
}
