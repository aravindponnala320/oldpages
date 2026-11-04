import type { Metadata } from "next";
import AdminLayout from "../components/AdminLayout";
import "./globals.css";

export const metadata: Metadata = {
  description: "OldPages.in admin application shell.",
  title: "OldPages Admin",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AdminLayout>{children}</AdminLayout>
      </body>
    </html>
  );
}
