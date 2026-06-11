import SwiftUI
import Foundation

let ARCHON_PROJECTS = [
    "xftc", "yepc", "pbs-foundation", "s2tdesigns", "smithcap", "smithcap-finance",
    "ministry", "business-law", "social-media", "solar-repair", "sigma-signal",
    "nutrue", "the-elevation", "travel", "holdings", "markets", "nightking"
]

let QUICK_AGENTS = [
    "grants-research-agent", "finance-cfo", "social-project-lead",
    "markets-project-lead", "xftc-project-lead", "business-law-project-lead"
]

enum ArchonTheme {
    static let accent = Color(hex: "#00B8FF")
    static let background = Color(hex: "#0B0F17")
    static let card = Color(hex: "#111827")
    static let text = Color(hex: "#D9E3F0")
    static let success = Color(hex: "#22c55e")
    static let warning = Color(hex: "#f59e0b")
    static let error = Color(hex: "#ef4444")
    static let muted = Color.white.opacity(0.55)

    static func statusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "running", "active", "online", "in_progress":
            return success
        case "queued", "pending":
            return warning
        case "failed", "error", "offline", "cancelled":
            return error
        case "done", "completed", "success":
            return accent
        default:
            return muted
        }
    }

    static func priorityColor(_ priority: String) -> Color {
        switch priority.lowercased() {
        case "high", "urgent", "critical":
            return error
        case "medium", "normal":
            return warning
        case "low":
            return accent
        default:
            return muted
        }
    }
}

extension Color {
    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)

        let a, r, g, b: UInt64
        switch cleaned.count {
        case 8:
            a = (value & 0xFF00_0000) >> 24
            r = (value & 0x00FF_0000) >> 16
            g = (value & 0x0000_FF00) >> 8
            b = value & 0x0000_00FF
        default:
            a = 255
            r = (value & 0xFF00_00) >> 16
            g = (value & 0x00FF_00) >> 8
            b = value & 0x0000_FF
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

extension View {
    func archonCard(padding: CGFloat = 16) -> some View {
        self
            .padding(padding)
            .background(ArchonTheme.card)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
    }
}

enum ArchonDateFormatter {
    private static let formatters: [ISO8601DateFormatter] = {
        let withFractional = ISO8601DateFormatter()
        withFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        let standard = ISO8601DateFormatter()
        standard.formatOptions = [.withInternetDateTime]
        return [withFractional, standard]
    }()

    static func parse(_ raw: String?) -> Date? {
        guard let raw, !raw.isEmpty else { return nil }
        for formatter in formatters {
            if let date = formatter.date(from: raw) {
                return date
            }
        }
        return nil
    }

    static func relativeString(_ raw: String?) -> String {
        guard let date = parse(raw) else { return raw ?? "—" }
        return date.formatted(.relative(presentation: .named))
    }

    static func timestampString(_ raw: String?) -> String {
        guard let date = parse(raw) else { return raw ?? "—" }
        return date.formatted(date: .abbreviated, time: .shortened)
    }
}

extension JSONValue {
    var displayText: String {
        switch self {
        case .string(let s): return s
        case .number(let n): return n.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(n)) : String(n)
        case .bool(let b): return b ? "Yes" : "No"
        case .null: return ""
        case .array(let arr): return arr.map(\.displayText).filter { !$0.isEmpty }.joined(separator: "\n")
        case .object(let dict):
            let ordered = ["summary", "content", "text", "message", "body"]
            for key in ordered {
                if let val = dict[key] { return val.displayText }
            }
            return dict.map { "**\($0.key):** \($0.value.displayText)" }.joined(separator: "\n")
        }
    }
}

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case server(String)
    case decoding

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The ArchonHub server URL is invalid."
        case .invalidResponse:
            return "The server returned an invalid response."
        case .server(let message):
            return message
        case .decoding:
            return "The server response could not be decoded."
        }
    }
}

struct EmptyBody: Encodable {}
struct EmptyResponse: Codable {}
