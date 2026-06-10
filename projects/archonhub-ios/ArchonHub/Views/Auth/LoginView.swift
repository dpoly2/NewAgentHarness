import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var authStore: AuthStore

    @State private var username = "admin"
    @State private var password = "ArchonHub2024!"
    @State private var isLoading = false
    @State private var errorMessage = ""

    var body: some View {
        NavigationStack {
            ZStack {
                ArchonTheme.background.ignoresSafeArea()

                VStack(spacing: 24) {
                    VStack(spacing: 10) {
                        Image("ArchonHubLogo")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 80, height: 80)
                            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                        Text("ArchonHub")
                            .font(.largeTitle.bold())
                            .foregroundStyle(ArchonTheme.text)
                        Text("AI Agent Harness")
                            .foregroundStyle(ArchonTheme.muted)
                    }
                    .padding(.top, 36)

                    VStack(spacing: 16) {
                        TextField("Username", text: $username)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .padding()
                            .background(Color.white.opacity(0.05))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

                        SecureField("Password", text: $password)
                            .padding()
                            .background(Color.white.opacity(0.05))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

                        if !errorMessage.isEmpty {
                            Text(errorMessage)
                                .font(.footnote)
                                .foregroundStyle(ArchonTheme.error)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }

                        Button {
                            Task { await login() }
                        } label: {
                            HStack {
                                if isLoading {
                                    ProgressView()
                                        .tint(.black)
                                }
                                Text(isLoading ? "Signing In..." : "Login")
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(ArchonTheme.accent)
                            .foregroundStyle(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                        .disabled(isLoading)
                    }
                    .archonCard(padding: 20)

                    Spacer()
                }
                .padding(24)
                .foregroundStyle(ArchonTheme.text)
            }
        }
    }

    private func login() async {
        guard !username.isEmpty, !password.isEmpty else {
            errorMessage = "Enter both username and password."
            return
        }

        isLoading = true
        errorMessage = ""

        do {
            try await authStore.login(username: username, password: password)
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthStore())
        .preferredColorScheme(.dark)
}
