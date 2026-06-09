import SwiftUI

struct AddTodoView: View {
    let onCreated: () async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var description = ""
    @State private var priority = "medium"
    @State private var project = ARCHON_PROJECTS.first ?? "xftc"
    @State private var dueDate = Date()
    @State private var includeDueDate = false
    @State private var isSaving = false
    @State private var errorMessage = ""

    private let priorities = ["low", "medium", "high"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Details") {
                    TextField("Title", text: $title)
                    TextField("Description", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section("Metadata") {
                    Picker("Priority", selection: $priority) {
                        ForEach(priorities, id: \.self, content: Text.init)
                    }

                    Picker("Project", selection: $project) {
                        ForEach(ARCHON_PROJECTS, id: \.self, content: Text.init)
                    }

                    Toggle("Include Due Date", isOn: $includeDueDate)
                    if includeDueDate {
                        DatePicker("Due Date", selection: $dueDate, displayedComponents: [.date, .hourAndMinute])
                    }
                }

                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(ArchonTheme.error)
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(ArchonTheme.background.ignoresSafeArea())
            .navigationTitle("Add Todo")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isSaving ? "Saving..." : "Save") {
                        Task { await saveTodo() }
                    }
                    .disabled(isSaving || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
        .preferredColorScheme(.dark)
    }

    private func saveTodo() async {
        struct TodoCreateRequest: Encodable {
            let title: String
            let description: String
            let priority: String
            let project: String
            let dueDate: String?
        }

        isSaving = true
        defer { isSaving = false }

        let formatter = ISO8601DateFormatter()
        let payload = TodoCreateRequest(
            title: title.trimmingCharacters(in: .whitespacesAndNewlines),
            description: description.trimmingCharacters(in: .whitespacesAndNewlines),
            priority: priority,
            project: project,
            dueDate: includeDueDate ? formatter.string(from: dueDate) : nil
        )

        do {
            let _: Todo = try await HubClient.shared.post("/api/todos", body: payload)
            await onCreated()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
