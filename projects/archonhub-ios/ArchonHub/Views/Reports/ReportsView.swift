import SwiftUI

struct ReportsView: View {
    @State private var reports: [Report] = []
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var expandedId: String?
    @State private var selectedType = "all"
    
    private let reportTypes = ["all", "daily", "weekly", "monthly", "custom"]
    
    private var filteredReports: [Report] {
        guard selectedType != "all" else { return reports }
        return reports.filter { $0.reportType.lowercased() == selectedType }
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                
                // Header with type filter
                HStack {
                    Picker("Type", selection: $selectedType) {
                        ForEach(reportTypes, id: \.self) { type in
                            Text(type.capitalized).tag(type)
                        }
                    }
                    .pickerStyle(.segmented)
                    
                    Spacer()
                    
                    Button {
                        Task { await loadReports() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(ArchonTheme.accent)
                    }
                }
                
                // Reports list
                if isLoading && reports.isEmpty {
                    ProgressView()
                        .tint(ArchonTheme.accent)
                        .frame(maxWidth: .infinity)
                        .archonCard()
                } else if filteredReports.isEmpty {
                    Text(errorMessage.isEmpty ? "No reports available." : errorMessage)
                        .foregroundStyle(ArchonTheme.muted)
                        .archonCard()
                } else {
                    ForEach(filteredReports) { report in
                        reportCard(report)
                    }
                }
            }
            .padding()
        }
        .background(ArchonTheme.background.ignoresSafeArea())
        .foregroundStyle(ArchonTheme.text)
        .navigationTitle("Reports")
        .task { if reports.isEmpty { await loadReports() } }
        .refreshable { await loadReports() }
    }
    
    private func reportCard(_ report: Report) -> some View {
        let isExpanded = expandedId == report.id
        
        return VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(report.reportType.capitalized)
                            .font(.caption.bold())
                            .foregroundStyle(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(reportTypeColor(report.reportType))
                            .cornerRadius(4)
                        
                        if let project = report.projectSlug, !project.isEmpty {
                            Text(project)
                                .font(.caption2)
                                .foregroundStyle(ArchonTheme.muted)
                        }
                    }
                    
                    Text(report.title)
                        .font(.headline)
                        .lineLimit(isExpanded ? nil : 2)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    if let date = report.generatedAt {
                        Text(ArchonDateFormatter.relativeString(date))
                            .font(.caption2)
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption2)
                        .foregroundStyle(ArchonTheme.muted)
                }
            }
            
            // Summary
            if !report.summary.isEmpty {
                Text(report.summary)
                    .font(.subheadline)
                    .foregroundStyle(ArchonTheme.muted)
                    .lineLimit(isExpanded ? nil : 3)
            }
            
            // Full content (when expanded)
            if isExpanded && !report.content.isEmpty {
                Divider()
                    .background(ArchonTheme.muted)
                
                ScrollView {
                    Text(report.content)
                        .font(.body.leading(.loose))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(maxHeight: 400)
            }
        }
        .archonCard(padding: 16)
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                expandedId = isExpanded ? nil : report.id
            }
        }
    }
    
    private func reportTypeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "daily": return ArchonTheme.accent
        case "weekly": return ArchonTheme.success
        case "monthly": return ArchonTheme.warning
        default: return ArchonTheme.muted
        }
    }
    
    private func loadReports() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            reports = try await HubClient.shared.get("/api/reports")
            errorMessage = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationStack { ReportsView() }
        .preferredColorScheme(.dark)
}
