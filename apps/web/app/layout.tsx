import type { Metadata } from "next";

import "./globals.css";
import { QueryProvider } from "../contexts/QueryProvider";
import { AuthProvider } from "../contexts/AuthContext";
import { LocationProvider } from "../contexts/LocationContext";
import { ConditionalShell } from "../components/ConditionalHeader";
import { ToastProvider } from "../components/ui/Toast";

export const metadata: Metadata = {
  description: "OldPages — buy, sell and exchange books near you.",
  title: "OldPages",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AuthProvider>
            <LocationProvider>
              <ToastProvider>
                <ConditionalShell>{children}</ConditionalShell>
              </ToastProvider>
            </LocationProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
