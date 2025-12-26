// frontend/src/app/layout.tsx
import * as React from "react";

export const metadata = {
    title: "Guidance Bot",
    description: "Planned educations search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
        <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>{children}</body>
        </html>
    );
}
