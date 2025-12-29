// guidance-bot/frontend/src/app/page.tsx
"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import styles from "./page.module.css";
import { resolveTenant, themeHrefForTenant } from "./tenantThemes";
import Chat from "../components/Chat";

export default function Page() {
    const tenantMunicipalityCode = resolveTenant();

    const [themeLoaded, setThemeLoaded] = useState(false);

    useEffect(() => {
        const href = themeHrefForTenant(tenantMunicipalityCode);

        let link = document.querySelector<HTMLLinkElement>(`link[data-tenant-theme="true"]`);
        if (!link) {
            link = document.createElement("link");
            link.rel = "stylesheet";
            link.setAttribute("data-tenant-theme", "true");
            document.head.appendChild(link);
        }

        link.onload = () => setThemeLoaded(true);
        link.onerror = () => setThemeLoaded(true);
        link.href = href;
    }, [tenantMunicipalityCode]);

    return (
        <div className={styles.shell} style={{ opacity: themeLoaded ? 1 : 0.98 }}>
            <header className={styles.topbar}>
                <div className={styles.topbarInner}>
                    <img className={styles.topLogo} src="/themes/0486/logotyp-strangnas2.svg" alt="Tenant logo" />
                    <div className={styles.topTitle}>School ChatBot</div>
                </div>
            </header>

            <main className={styles.main}>
                <div className={styles.container}>
                    <Chat tenantId={tenantMunicipalityCode} />
                </div>
            </main>

            <footer className={styles.footer}>
                <div className={styles.footerInner}>
                    <img className={styles.bottomLogo} src="/themes/0486/Skyline_sidfot.png" alt="Footer logo" />
                </div>
            </footer>
        </div>
    );
}
