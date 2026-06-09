import SwiftUI

struct WatchMainView: View {
    var body: some View {
        TabView {
            WatchStatusView()
            WatchQuickRunView()
            WatchNotificationsView()
        }
        .tabViewStyle(.verticalPage)
        .background(ArchonTheme.background)
    }
}

#Preview {
    WatchMainView()
}
