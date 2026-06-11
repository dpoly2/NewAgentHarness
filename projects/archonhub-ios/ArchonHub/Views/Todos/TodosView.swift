import SwiftUI

struct TodosView: View {
    @State private var todos: [Todo] = []
    @State private var filter = "all"
    @State private var showAddTodo = false
    @State private var selectedTodo: Todo?
    @State private var errorMessage = ""

    private let filters = ["all", "pending", "in_progress", "done"]

    private var filteredTodos: [Todo] {
        guard filter != "all" else { return todos }
        return todos.filter { $0.status.lowercased() == filter }
    }

    var body: some View {
        List {
            Picker("Status", selection: $filter) {
                ForEach(filters, id: \.self) { value in
                    Text(value.replacingOccurrences(of: "_", with: " ").capitalized).tag(value)
                }
            }
            .pickerStyle(.segmented)
            .listRowBackground(ArchonTheme.card)

            if filteredTodos.isEmpty {
                Text(errorMessage.isEmpty ? "No todos." : errorMessage)
                    .foregroundStyle(ArchonTheme.muted)
                    .listRowBackground(ArchonTheme.card)
            } else {
                ForEach(filteredTodos) { todo in
                    Button { selectedTodo = todo } label: {
                        todoRow(todo)
                    }
                    .buttonStyle(.plain)
                    .listRowBackground(ArchonTheme.card)
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) {
                            Task { await delete(todo) }
                        } label: { Label("Delete", systemImage: "trash.fill") }
                    }
                    .swipeActions(edge: .leading) {
                        Button(action: { Task { await setStatus(todo, status: "done") } }) {
                            Label("Done", systemImage: "checkmark.circle.fill")
                        }
                        .tint(ArchonTheme.success)
                        Button(action: { Task { await setStatus(todo, status: "in_progress") } }) {
                            Label("Working", systemImage: "clock.fill")
                        }
                        .tint(ArchonTheme.warning)
                    }
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Todos")
        .toolbar {
            Button { showAddTodo = true } label: {
                Image(systemName: "plus").foregroundStyle(ArchonTheme.accent)
            }
        }
        .task { if todos.isEmpty { await loadTodos() } }
        .refreshable { await loadTodos() }
        .sheet(isPresented: $showAddTodo) {
            AddTodoView { await loadTodos() }
        }
        .sheet(item: $selectedTodo) { todo in
            TodoDetailSheet(todo: todo) { newStatus in
                Task { await setStatus(todo, status: newStatus) }
            } onDelete: {
                Task { await delete(todo) }
            }
        }
        .foregroundStyle(ArchonTheme.text)
    }

    private func todoRow(_ todo: Todo) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top) {
                statusIcon(todo.status)
                    .padding(.top, 2)
                VStack(alignment: .leading, spacing: 4) {
                    Text(todo.title)
                        .font(.headline)
                        .strikethrough(todo.status == "done")
                        .foregroundStyle(todo.status == "done" ? ArchonTheme.muted : ArchonTheme.text)
                    if let desc = todo.description, !desc.isEmpty {
                        Text(desc)
                            .font(.subheadline)
                            .foregroundStyle(ArchonTheme.muted)
                            .lineLimit(2)
                    }
                }
                Spacer()
                Circle()
                    .fill(ArchonTheme.priorityColor(todo.priority))
                    .frame(width: 8, height: 8)
                    .padding(.top, 4)
            }
            HStack {
                Text(todo.project ?? "General")
                    .font(.caption)
                    .foregroundStyle(ArchonTheme.accent.opacity(0.8))
                Spacer()
                if let due = todo.dueDate {
                    Text(ArchonDateFormatter.relativeString(due))
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func statusIcon(_ status: String) -> some View {
        switch status.lowercased() {
        case "done":
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(ArchonTheme.success)
        case "in_progress":
            Image(systemName: "clock.fill")
                .foregroundStyle(ArchonTheme.warning)
        default:
            Image(systemName: "circle")
                .foregroundStyle(ArchonTheme.muted)
        }
    }

    private func loadTodos() async {
        do {
            todos = try await HubClient.shared.get("/api/todos")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func delete(_ todo: Todo) async {
        selectedTodo = nil
        do {
            try await HubClient.shared.delete("/api/todos/\(todo.id)")
            await loadTodos()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func setStatus(_ todo: Todo, status: String) async {
        struct TodoUpdateRequest: Encodable { let status: String }
        selectedTodo = nil
        do {
            let _: Todo = try await HubClient.shared.put("/api/todos/\(todo.id)", body: TodoUpdateRequest(status: status))
            await loadTodos()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Todo Detail Sheet

struct TodoDetailSheet: View {
    let todo: Todo
    let onStatusChange: (String) -> Void
    let onDelete: () -> Void

    @Environment(\.dismiss) private var dismiss

    private let statuses = [
        ("pending",     "circle",               "Pending"),
        ("in_progress", "clock.fill",           "In Progress"),
        ("done",        "checkmark.circle.fill", "Done"),
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {

                    // Title + priority
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(todo.title)
                                .font(.title2.bold())
                            HStack(spacing: 6) {
                                Circle()
                                    .fill(ArchonTheme.priorityColor(todo.priority))
                                    .frame(width: 8, height: 8)
                                Text("\(todo.priority.capitalized) priority")
                                    .font(.caption)
                                    .foregroundStyle(ArchonTheme.muted)
                                if let project = todo.project {
                                    Text("· \(project)")
                                        .font(.caption)
                                        .foregroundStyle(ArchonTheme.accent)
                                }
                            }
                        }
                        Spacer()
                    }
                    .archonCard()

                    // Description
                    if let desc = todo.description, !desc.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Label("Description", systemImage: "text.alignleft")
                                .font(.caption.bold())
                                .foregroundStyle(ArchonTheme.muted)
                            Text(desc)
                                .font(.body)
                        }
                        .archonCard()
                    }

                    // Due date
                    if let due = todo.dueDate {
                        HStack {
                            Label("Due", systemImage: "calendar")
                                .font(.caption.bold())
                                .foregroundStyle(ArchonTheme.muted)
                            Spacer()
                            Text(ArchonDateFormatter.timestampString(due))
                                .font(.subheadline)
                        }
                        .archonCard()
                    }

                    // Status buttons
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Status", systemImage: "flag")
                            .font(.caption.bold())
                            .foregroundStyle(ArchonTheme.muted)
                        HStack(spacing: 10) {
                            ForEach(statuses, id: \.0) { value, icon, label in
                                let isActive = todo.status.lowercased() == value
                                Button {
                                    onStatusChange(value)
                                    dismiss()
                                } label: {
                                    HStack(spacing: 6) {
                                        Image(systemName: icon)
                                        Text(label)
                                            .font(.caption.bold())
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 10)
                                    .background(isActive ? ArchonTheme.statusColor(value) : ArchonTheme.background)
                                    .foregroundStyle(isActive ? .black : ArchonTheme.statusColor(value))
                                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                                            .stroke(ArchonTheme.statusColor(value).opacity(isActive ? 0 : 0.4), lineWidth: 1)
                                    )
                                }
                            }
                        }
                    }
                    .archonCard()

                    // Delete
                    Button(role: .destructive) {
                        onDelete()
                        dismiss()
                    } label: {
                        Label("Delete Todo", systemImage: "trash")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                    }
                    .archonCard()
                }
                .padding()
            }
            .background(ArchonTheme.background.ignoresSafeArea())
            .foregroundStyle(ArchonTheme.text)
            .navigationTitle("Todo")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
        .preferredColorScheme(.dark)
    }
}

#Preview {
    NavigationStack { TodosView() }
        .preferredColorScheme(.dark)
}
