import type { Metadata, Viewport } from "next";
import { connection } from "next/server";

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

// viewport-fit=cover lets the bottom nav pad itself clear of the iPhone home indicator.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Render per request: a page built ahead of time couldn't carry the request's CSP nonce.
  await connection();
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
