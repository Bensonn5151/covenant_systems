import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="min-h-screen bg-[#050505] flex items-center justify-center px-6">
      <SignUp
        fallbackRedirectUrl="/dashboard"
        signInUrl="/sign-in"
        appearance={{
          variables: {
            colorPrimary: "#22c55e",
            colorBackground: "#111111",
            colorInputBackground: "#1a1a1a",
            colorInputText: "#f3f4f6",
            colorText: "#f3f4f6",
            colorTextSecondary: "#9ca3af",
            colorTextOnPrimaryBackground: "#000000",
            colorNeutral: "#f3f4f6",
            borderRadius: "0.75rem",
          },
          elements: {
            card: { backgroundColor: "#111111", borderColor: "#333", border: "1px solid #333" },
            headerTitle: { color: "#ffffff" },
            headerSubtitle: { color: "#9ca3af" },
            socialButtonsBlockButton: { backgroundColor: "#1a1a1a", borderColor: "#444", color: "#e5e7eb" },
            socialButtonsBlockButtonText: { color: "#e5e7eb" },
            dividerLine: { backgroundColor: "#444" },
            dividerText: { color: "#6b7280" },
            formFieldLabel: { color: "#d1d5db" },
            formFieldInput: { backgroundColor: "#1a1a1a", borderColor: "#444", color: "#f3f4f6" },
            footerActionLink: { color: "#22c55e" },
            footerActionText: { color: "#9ca3af" },
            formButtonPrimary: { backgroundColor: "#22c55e", color: "#000000" },
          },
        }}
      />
    </main>
  );
}
