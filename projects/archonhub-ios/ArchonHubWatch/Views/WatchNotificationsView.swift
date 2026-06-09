import SwiftUI

struct WatchNotificationsView: View {
    @State private var notifications: [Notification] = []
    @State private var errorMessage = ""

    var body: some View {
        List {
            if notifications.isEmpty {
                Text(errorMessage.isEmpty ? "No notifications." : errorMessage)
                    .foregroundStyle(ArchonTheme.muted)
                    .listRowBackground(ArchonTheme.card)
            } else {
                ForEach(notifications.prefix(5)) { notification in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(color(for: notification))
                            .frame(width: 8, height: 8)
                            .padding(.top, 4)
                        VStack(alignment: .leading, spacing: 4) {
                            Text(notification.text)
                                .font(.caption)
                            Text(ArchonDateFormatter.relativeString(notification.createdAt))
                                .font(.caption2)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                    }
                    .listRowBackground(ArchonTheme.card)
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(ArchonTheme.background)
        .foregroundStyle(ArchonTheme.text)
        .task {
            await loadNotifications()
        }
    }

    private func loadNotifications() async {
        do {
            notifications = try await HubClient.shared.get("/api/notifications?limit=5")
            errorMessage = ""
        } catch {
            notifications = []
            errorMessage = error.localizedDescription
        }
    }

    private func color(for notification: Notification) -> Color {
        if let color = notification.color, color.hasPrefix("#") {
            return Color(hex: color)
        }
        return ArchonTheme.statusColor(notification.category ?? "info")
    }
}
