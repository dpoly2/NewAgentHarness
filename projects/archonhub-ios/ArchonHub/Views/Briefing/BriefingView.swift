import SwiftUI

struct BriefingView: View {
    @State private var briefs: [DailyBrief] = []
    @State private var isLoading = false
    @State private var isGenerating = false
    @State private var errorMessage = ""
    @State private var expandedId: String?

    private let inezPurple = Color(red: 0.49, green: 0.23, blue: 0.93)
    private let inezLavender = Color(red: 0.77, green: 0.71, blue: 0.99)

    private var latest: DailyBrief? { briefs.first }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                // ── Inez Briefing Header ──────────────────────────────────
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(inezPurple)
                                .frame(width: 42, height: 42)
                                .shadow(color: inezPurple.opacity(0.4), radius: 6)
                            Text("👑")
                                .font(.subheadline)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(spacing: 6) {
                                Text("INEZ")
                                    .font(.headline.weight(.bold))
                                    .tracking(1.2)
                                    .foregroundStyle(inezLavender)
                                Text("·")
                                    .foregroundStyle(ArchonTheme.muted)
                                Text("Executive Briefing")
                                    .font(.subheadline)
                                    .foregroundStyle(ArchonTheme.muted)
                            }
                            Text(latest.flatMap { ArchonDateFormatter.parse($0.createdAt) }
                                    .map { $0.formatted(date: .complete, time: .omitted) }
                                 ?? "No briefing on file")
                                .font(.caption)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                        Spacer()
                        if isGenerating {
                            ProgressView().tint(inezPurple)
                        } else {
                            Button {
                                Task { await generateBrief() }
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "sparkles")
                                        .font(.caption2)
                                    Text("Brief Me")
                                        .font(.caption.bold())
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(inezPurple)
                            .controlSize(.small)
                        }
                    }
                }
                .padding(14)
                .background(ArchonTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(inezPurple.opacity(0.3), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                // ── Latest Brief ─────────────────────────────────────────
                if isLoading && briefs.isEmpty {
                    ProgressView()
                        .tint(inezPurple)
                        .frame(maxWidth: .infinity)
                        .archonCard()
                } else if let brief = latest {
                    briefCard(brief, isLatest: true)
                } else {
                    VStack(spacing: 14) {
                        Text("👑")
                            .font(.title)
                        Text(errorMessage.isEmpty
                             ? "No briefing on file.\nAsk Inez to brief you on the current situation."
                             : errorMessage)
                            .foregroundStyle(ArchonTheme.muted)
                            .multilineTextAlignment(.center)
                        if errorMessage.isEmpty {
                            Button {
                                Task { await generateBrief() }
                            } label: {
                                Label("Generate Briefing", systemImage: "sparkles")
                                    .font(.caption.bold())
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(inezPurple)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .archonCard()
                }

                // ── History ───────────────────────────────────────────────
                if briefs.count > 1 {
                    HStack {
                        Text("PRIOR BRIEFINGS")
                            .font(.caption.weight(.semibold))
                            .tracking(1)
                            .foregroundStyle(ArchonTheme.muted)
                        Spacer()
                        Button { Task { await loadBriefs() } } label: {
                            Image(systemName: "arrow.clockwise")
                                .font(.caption)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                    }

                    ForEach(briefs.dropFirst(), id: \.id) { brief in
                        briefCard(brief, isLatest: false)
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Inez Briefing")
        .task { if briefs.isEmpty { await loadBriefs() } }
        .refreshable { await loadBriefs() }
    }

    private func briefCard(_ brief: DailyBrief, isLatest: Bool) -> some View {
        let isExpanded = expandedId == brief.id || isLatest
        return VStack(alignment: .leading, spacing: 10) {
            HStack {
                HStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(isLatest ? inezPurple : inezPurple.opacity(0.5))
                            .frame(width: 22, height: 22)
                        Text("👑")
                            .font(.system(size: 11))
                    }
                    Text("Inez")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(inezLavender)
                    if isLatest {
                        Text("· Latest")
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.success)
                    }
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
        .padding(16)
        .background(ArchonTheme.card)
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(isLatest ? inezPurple.opacity(0.25) : ArchonTheme.muted.opacity(0.1), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
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
            let response: [DailyBrief]? = try await HubClient.shared.get("/api/briefs")
            briefs = response ?? []
            errorMessage = ""
        } catch {
            briefs = []
            errorMessage = error.localizedDescription
        }
    }

    private func generateBrief() async {
        isGenerating = true
        defer { isGenerating = false }
        do {
            let brief: DailyBrief = try await HubClient.shared.get("/api/inez/brief")
            briefs.insert(brief, at: 0)
            errorMessage = ""
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

