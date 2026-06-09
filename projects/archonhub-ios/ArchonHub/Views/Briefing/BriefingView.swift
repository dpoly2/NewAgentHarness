import SwiftUI

struct BriefingView: View {
    @State private var brief: DailyBrief?
    @State private var isLoading = false
    @State private var errorMessage = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Daily Brief")
                            .font(.largeTitle.bold())
                        Text(brief?.createdAt.map(ArchonDateFormatter.timestampString) ?? "Not updated yet")
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    Spacer()
                    Button {
                        Task { await loadBrief() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }

                if isLoading && brief == nil {
                    ProgressView()
                        .tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity)
                        .archonCard()
                } else if let brief {
                    Text(brief.content)
                        .font(.body.leading(.loose))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .archonCard(padding: 20)
                } else {
                    Text(errorMessage.isEmpty ? "No briefing available." : errorMessage)
                        .foregroundStyle(ArchonTheme.muted)
                        .archonCard()
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Briefing")
        .task {
            if brief == nil {
                await loadBrief()
            }
        }
    }

    private func loadBrief() async {
        isLoading = true
        defer { isLoading = false }

        do {
            brief = try await HubClient.shared.get("/api/briefing")
            errorMessage = ""
        } catch {
            brief = nil
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { BriefingView() }
        .preferredColorScheme(.dark)
}
