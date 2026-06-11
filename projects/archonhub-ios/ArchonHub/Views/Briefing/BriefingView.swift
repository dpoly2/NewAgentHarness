import SwiftUI

struct BriefingView: View {
    @State private var briefs: [DailyBrief] = []
    @State private var isLoading = false
    @State private var isGenerating = false
    @State private var errorMessage = ""
    @State private var expandedId: String?

    private var latest: DailyBrief? { briefs.first }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                // Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Daily Briefing")
                            .font(.largeTitle.bold())
                        Text(latest.flatMap { ArchonDateFormatter.parse($0.createdAt) }
                                .map { $0.formatted(date: .complete, time: .omitted) }
                             ?? "No briefing yet")
                            .font(.caption)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    Spacer()
                    HStack(spacing: 10) {
                        if isGenerating {
                            ProgressView().tint(ArchonTheme.accent)
                        } else {
                            Button {
                                Task { await generateBrief() }
                            } label: {
                                Label("Generate", systemImage: "sparkles")
                                    .font(.caption.bold())
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(Color(red: 0.49, green: 0.23, blue: 0.93))
                            .controlSize(.small)
                        }
                        Button { Task { await loadBriefs() } } label: {
                            Image(systemName: "arrow.clockwise")
                                .foregroundStyle(ArchonTheme.accent)
                        }
                    }
                }

                // Latest brief
                if isLoading && briefs.isEmpty {
                    ProgressView()
                        .tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity)
                        .archonCard()
                } else if let brief = latest {
                    briefCard(brief, isLatest: true)
                } else {
                    Text(errorMessage.isEmpty ? "No briefings yet. Tap Generate to create one." : errorMessage)
                        .foregroundStyle(ArchonTheme.muted)
                        .archonCard()
                }

                // History
                if briefs.count > 1 {
                    Text("History")
                        .font(.title3.bold())
                        .padding(.top, 4)

                    ForEach(briefs.dropFirst(), id: \.id) { brief in
                        briefCard(brief, isLatest: false)
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Briefing")
        .task { if briefs.isEmpty { await loadBriefs() } }
        .refreshable { await loadBriefs() }
    }

    private func briefCard(_ brief: DailyBrief, isLatest: Bool) -> some View {
        let isExpanded = expandedId == brief.id || isLatest
        return VStack(alignment: .leading, spacing: 10) {
            HStack {
                if isLatest {
                    Label("Today", systemImage: "sun.max.fill")
                        .font(.caption.bold())
                        .foregroundStyle(ArchonTheme.warning)
                }
                Spacer()
                Text(ArchonDateFormatter.relativeString(brief.createdAt))
                    .font(.caption2)
                    .foregroundStyle(ArchonTheme.muted)
                if !isLatest {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }

            if !brief.content.isEmpty {
                if isExpanded {
                    Text(brief.content)
                        .font(.body.leading(.loose))
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    Text(brief.content)
                        .font(.body)
                        .lineLimit(2)
                        .foregroundStyle(ArchonTheme.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
        .archonCard(padding: 16)
        .onTapGesture {
            if !isLatest {
                withAnimation(.easeInOut(duration: 0.2)) {
                    expandedId = isExpanded ? nil : brief.id
                }
            }
        }
    }

    private func loadBriefs() async {
        isLoading = true
        defer { isLoading = false }
        do {
            briefs = try await HubClient.shared.get("/api/briefs")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func generateBrief() async {
        isGenerating = true
        defer { isGenerating = false }
        do {
            let _: DailyBrief = try await HubClient.shared.get("/api/briefing")
            await loadBriefs()
        } catch {
            // Fall back silently — server may not have Inez module installed
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { BriefingView() }
        .preferredColorScheme(.dark)
}
