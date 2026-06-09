import SwiftUI

struct TodosView: View {
    @State private var todos: [Todo] = []
    @State private var filter = "all"
    @State private var showAddTodo = false
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
                Text(errorMessage.isEmpty ? "No todos available." : errorMessage)
                    .foregroundStyle(ArchonTheme.muted)
                    .listRowBackground(ArchonTheme.card)
            } else {
                ForEach(filteredTodos) { todo in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Circle()
                                .fill(ArchonTheme.priorityColor(todo.priority))
                                .frame(width: 10, height: 10)
                            Text(todo.title)
                                .font(.headline)
                            Spacer()
                            Text(todo.status.replacingOccurrences(of: "_", with: " ").capitalized)
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(ArchonTheme.statusColor(todo.status))
                        }

                        if let description = todo.description, !description.isEmpty {
                            Text(description)
                                .font(.subheadline)
                                .foregroundStyle(ArchonTheme.text)
                        }

                        HStack {
                            Text(todo.project ?? "General")
                            Spacer()
                            Text(todo.dueDate.map(ArchonDateFormatter.timestampString) ?? "No due date")
                        }
                        .font(.caption)
                        .foregroundStyle(ArchonTheme.muted)
                    }
                    .padding(.vertical, 6)
                    .listRowBackground(ArchonTheme.card)
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) {
                            Task { await delete(todo) }
                        } label: {
                            Label("Delete", systemImage: "trash.fill")
                        }
                    }
                    .swipeActions(edge: .leading) {
                        Button {
                            Task { await markDone(todo) }
                        } label: {
                            Label("Done", systemImage: "checkmark.circle.fill")
                        }
                        .tint(ArchonTheme.success)
                    }
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background.ignoresSafeArea())
        .navigationTitle("Todos")
        .toolbar {
            Button {
                showAddTodo = true
            } label: {
                Image(systemName: "plus")
                    .foregroundStyle(ArchonTheme.accent)
            }
        }
        .task {
            if todos.isEmpty {
                await loadTodos()
            }
        }
        .refreshable {
            await loadTodos()
        }
        .sheet(isPresented: $showAddTodo) {
            AddTodoView {
                await loadTodos()
            }
        }
        .foregroundStyle(ArchonTheme.text)
    }

    private func loadTodos() async {
        do {
            todos = try await HubClient.shared.get("/api/todos")
            errorMessage = ""
        } catch {
            todos = []
            errorMessage = error.localizedDescription
        }
    }

    private func delete(_ todo: Todo) async {
        do {
            try await HubClient.shared.delete("/api/todos/\(todo.id)")
            await loadTodos()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func markDone(_ todo: Todo) async {
        struct TodoUpdateRequest: Encodable {
            let status: String
        }

        do {
            let _: Todo = try await HubClient.shared.put("/api/todos/\(todo.id)", body: TodoUpdateRequest(status: "done"))
            await loadTodos()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { TodosView() }
        .preferredColorScheme(.dark)
}
