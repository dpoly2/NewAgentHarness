import SwiftUI

struct NotificationsView: View {
    @State private var notifications: [Notification] = []
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var filter = "all"
    
    private let filters = ["all", "unread"]
    
    private var filteredNotifications: [Notification] {
        guard filter == "unread" else { return notifications }
        return notifications.filter { !$0.read }
    }
    
    private var unreadCount: Int {
        notifications.filter { !$0.read }.count
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Header with mark all read button
            HStack {
                Picker("Filter", selection: $filter) {
                    ForEach(filters, id: \.self) { value in
                        Text(value == "all" ? "All (\(notifications.count))" : "Unread (\(unreadCount))").tag(value)
                    }
                }
                .pickerStyle(.segmented)
                
                Spacer()
                
                if unreadCount > 0 {
                    Button {
                        Task { await markAllRead() }
                    } label: {
                        Text("Mark All Read")
                            .font(.caption.bold())
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }
            }
            .padding()
            .background(ArchonTheme.card)
            
            // Notifications list
            List {
                if isLoading && notifications.isEmpty {
                    ProgressView()
                        .tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity)
                        .listRowBackground(ArchonTheme.card)
                } else if filteredNotifications.isEmpty {
                    Text(errorMessage.isEmpty ? "No notifications." : errorMessage)
                        .foregroundStyle(ArchonTheme.muted)
                        .listRowBackground(ArchonTheme.card)
                } else {
                    ForEach(filteredNotifications) { notification in
                        notificationRow(notification)
                            .listRowBackground(notification.read ? ArchonTheme.card : ArchonTheme.card.opacity(1.2))
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    Task { await delete(notification) }
                                } label: {
                                    Label("Delete", systemImage: "trash.fill")
                                }
                            }
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(ArchonTheme.background)
        }
        .navigationTitle("Notifications")
        .background(ArchonTheme.background.ignoresSafeArea())
        .task { if notifications.isEmpty { await loadNotifications() } }
        .refreshable { await loadNotifications() }
    }
    
    private func notificationRow(_ notification: Notification) -> some View {
        HStack(alignment: .top, spacing: 12) {
            // Unread indicator
            Circle()
                .fill(notification.read ? ArchonTheme.muted.opacity(0.3) : ArchonTheme.accent)
                .frame(width: 10, height: 10)
                .padding(.top, 6)
            
            VStack(alignment: .leading, spacing: 6) {
                // Category badge (if exists)
                if let category = notification.category, !category.isEmpty {
                    Text(category.uppercased())
                        .font(.caption2.bold())
                        .foregroundStyle(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(categoryColor(category))
                        .cornerRadius(3)
                }
                
                // Text
                Text(notification.text)
                    .font(notification.read ? .body : .body.weight(.semibold))
                    .foregroundStyle(ArchonTheme.text)
                
                // Timestamp
                if let date = notification.createdAt {
                    Text(ArchonDateFormatter.relativeString(date))
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
            
            Spacer()
        }
        .padding(.vertical, 8)
    }
    
    private func categoryColor(_ category: String) -> Color {
        switch category.lowercased() {
        case "urgent", "critical": return ArchonTheme.error
        case "warning": return ArchonTheme.warning
        case "success": return ArchonTheme.success
        default: return ArchonTheme.accent
        }
    }
    
    private func loadNotifications() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            notifications = try await HubClient.shared.get("/api/notifications")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    private func markAllRead() async {
        do {
            let _: EmptyResponse = try await HubClient.shared.post("/api/notifications/read", body: EmptyBody())
            await loadNotifications()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
    
    private func delete(_ notification: Notification) async {
        // Remove from local list immediately for smooth UX
        notifications.removeAll { $0.id == notification.id }
        
        do {
            try await HubClient.shared.delete("/api/notifications/\(notification.id)")
        } catch {
            // Restore on error
            await loadNotifications()
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { NotificationsView() }
        .preferredColorScheme(.dark)
}
