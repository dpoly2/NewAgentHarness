import SwiftUI

// MARK: - Inline run button used inside message bubbles
struct RunCodeButton: View {
    let code: String
    @State private var showSheet = false

    var body: some View {
        Button {
            showSheet = true
        } label: {
            Label("Run Code", systemImage: "play.fill")
                .font(.caption.weight(.semibold))
                .foregroundColor(.white)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.purple)
                .clipShape(Capsule())
        }
        .sheet(isPresented: $showSheet) {
            CodeExecutionView(initialCode: code)
        }
    }
}

// MARK: - Full code execution sheet
struct CodeExecutionView: View {
    @State var initialCode: String
    @State private var code: String
    @State private var result: SandboxResult?
    @State private var isRunning = false
    @State private var error: String?
    @State private var selectedFile: SandboxGeneratedFile?
    @Environment(\.dismiss) private var dismiss

    init(initialCode: String = "") {
        self._initialCode = State(initialValue: initialCode)
        self._code = State(initialValue: initialCode)
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Code editor
                codeEditorSection

                Divider()

                // Run button
                runBar

                // Output
                if let result {
                    outputSection(result)
                } else if let error {
                    errorBanner(error)
                }
            }
            .navigationTitle("Code Sandbox")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button { code = "" } label: {
                        Image(systemName: "trash")
                    }
                    .disabled(code.isEmpty)
                }
            }
        }
        .sheet(item: $selectedFile) { file in
            GeneratedFilePreview(file: file)
        }
    }

    // MARK: Sub-views

    private var codeEditorSection: some View {
        TextEditor(text: $code)
            .font(.system(.footnote, design: .monospaced))
            .frame(minHeight: 220)
            .padding(8)
            .overlay(
                Group {
                    if code.isEmpty {
                        Text("# Write Python code here…")
                            .foregroundColor(.secondary)
                            .font(.system(.footnote, design: .monospaced))
                            .padding(12)
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                            .allowsHitTesting(false)
                    }
                }
            )
    }

    private var runBar: some View {
        HStack {
            Text("Python 3")
                .font(.caption)
                .foregroundColor(.secondary)
            Spacer()
            Button {
                runCode()
            } label: {
                if isRunning {
                    ProgressView()
                        .scaleEffect(0.8)
                        .padding(.horizontal, 16)
                } else {
                    Label("Run", systemImage: "play.fill")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 8)
                        .background(code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? Color.gray : Color.purple)
                        .clipShape(Capsule())
                }
            }
            .disabled(isRunning || code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color(.secondarySystemBackground))
    }

    private func outputSection(_ r: SandboxResult) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                // Status bar
                statusBar(r)

                // Blocked reason
                if let reason = r.blockedReason {
                    Label(reason, systemImage: "shield.slash.fill")
                        .font(.footnote)
                        .foregroundColor(.orange)
                        .padding(.horizontal)
                }

                // stdout
                if !r.stdout.isEmpty {
                    outputBlock(label: "Output", text: r.stdout, color: .primary)
                }

                // stderr
                if !r.stderr.isEmpty {
                    outputBlock(label: "Errors / Warnings", text: r.stderr, color: .red)
                }

                // Generated files
                if !r.generatedFiles.isEmpty {
                    generatedFilesSection(r.generatedFiles)
                }

                // Nothing produced
                if r.stdout.isEmpty && r.stderr.isEmpty && r.generatedFiles.isEmpty && r.blockedReason == nil {
                    Text("(no output)")
                        .font(.footnote)
                        .foregroundColor(.secondary)
                        .padding(.horizontal)
                }
            }
            .padding(.vertical, 12)
        }
    }

    private func statusBar(_ r: SandboxResult) -> some View {
        HStack(spacing: 12) {
            Image(systemName: r.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundColor(r.success ? .green : .red)
            Text(r.success ? "Completed" : "Failed")
                .font(.subheadline.weight(.semibold))
            Spacer()
            Text("\(r.executionTimeMs)ms")
                .font(.caption)
                .foregroundColor(.secondary)
            Text(r.mode.uppercased())
                .font(.caption2)
                .foregroundColor(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.purple.opacity(0.8))
                .cornerRadius(4)
        }
        .padding(.horizontal)
    }

    private func outputBlock(label: String, text: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption.weight(.semibold))
                .foregroundColor(.secondary)
                .padding(.horizontal)
            ScrollView(.horizontal, showsIndicators: false) {
                Text(text)
                    .font(.system(.footnote, design: .monospaced))
                    .foregroundColor(color)
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(Color(.tertiarySystemBackground))
            .cornerRadius(8)
            .padding(.horizontal)
        }
    }

    private func generatedFilesSection(_ files: [SandboxGeneratedFile]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Generated Files")
                .font(.caption.weight(.semibold))
                .foregroundColor(.secondary)
                .padding(.horizontal)

            ForEach(files.filter { $0.name != "fontlist-v390.json" }) { file in
                Button { selectedFile = file } label: {
                    HStack {
                        Image(systemName: fileIcon(for: file.mimeType))
                            .foregroundColor(.purple)
                        Text(file.name)
                            .font(.subheadline)
                        Spacer()
                        Text(formatBytes(file.sizeBytes))
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Image(systemName: "chevron.right")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(8)
                    .padding(.horizontal)
                }
            }
        }
    }

    private func errorBanner(_ msg: String) -> some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
            Text(msg)
                .font(.footnote)
                .foregroundColor(.red)
            Spacer()
        }
        .padding()
        .background(Color.red.opacity(0.08))
    }

    // MARK: Actions

    private func runCode() {
        isRunning = true
        result = nil
        error = nil

        let req = SandboxExecuteRequest(code: code, language: "python")
        Task {
            do {
                let res: SandboxResult = try await HubClient.shared.post(
                    "/api/sandbox/execute",
                    body: req
                )
                await MainActor.run {
                    result = res
                    isRunning = false
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isRunning = false
                }
            }
        }
    }

    // MARK: Helpers

    private func fileIcon(for mime: String) -> String {
        if mime.contains("image") { return "photo.fill" }
        if mime.contains("csv") || mime.contains("excel") { return "tablecells.fill" }
        if mime.contains("json") { return "curlybraces" }
        return "doc.fill"
    }

    private func formatBytes(_ n: Int) -> String {
        if n < 1024 { return "\(n) B" }
        if n < 1_048_576 { return String(format: "%.1f KB", Double(n) / 1024) }
        return String(format: "%.1f MB", Double(n) / 1_048_576)
    }
}

// MARK: - Preview for generated files

struct GeneratedFilePreview: View {
    let file: SandboxGeneratedFile
    @Environment(\.dismiss) private var dismiss

    private var imageData: UIImage? {
        guard file.mimeType.contains("image"),
              let data = Data(base64Encoded: file.contentBase64) else { return nil }
        return UIImage(data: data)
    }

    private var textContent: String? {
        guard file.mimeType.contains("text") || file.mimeType.contains("json") || file.mimeType.contains("csv"),
              let data = Data(base64Encoded: file.contentBase64) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    var body: some View {
        NavigationView {
            Group {
                if let img = imageData {
                    ScrollView([.horizontal, .vertical]) {
                        Image(uiImage: img)
                            .resizable()
                            .scaledToFit()
                            .padding()
                    }
                } else if let text = textContent {
                    ScrollView {
                        Text(text)
                            .font(.system(.footnote, design: .monospaced))
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                } else {
                    VStack {
                        Image(systemName: "doc.fill")
                            .font(.system(size: 64))
                            .foregroundColor(.secondary)
                        Text("Preview not available")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle(file.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
