// guidance-bot/frontend/src/app/page.tsx
"use client";

import * as React from "react";
import { useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";
import { resolveTenant, themeHrefForTenant } from "./tenantThemes";

type PlannedItem = {
    id?: string;
    title?: string;
    name?: string;
    organizer?: string;
    municipalityCode?: string;
    educationForm?: string;
    startDate?: string;
    url?: string;
};

type PlannedResponse = {
    source?: string;
    items?: PlannedItem[];
    data?: { items?: PlannedItem[] };
    message?: string;
    error?: string;
    answer?: string;
};

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");

const MOCK_RESPONSE: PlannedResponse = {
    source: "mock",
    items: [
        {
            id: "evt-1",
            title: "Komvux – Matematik 2b",
            organizer: "Strängnäs kommun",
            municipalityCode: "0486",
            educationForm: "komvux",
            startDate: "2026-01-12",
            url: "https://example.invalid/course/evt-1",
        },
        {
            id: "evt-2",
            title: "Komvux – Svenska som andraspråk 1",
            organizer: "Strängnäs kommun",
            municipalityCode: "0486",
            educationForm: "komvux",
            startDate: "2026-02-02",
            url: "https://example.invalid/course/evt-2",
        },
    ],
};

function normalizeWhitespace(s: string): string {
    return (s || "").trim().replace(/\s+/g, " ");
}

async function fetchJson<T>(url: string, options: RequestInit): Promise<T> {
    const res = await fetch(url, options);
    const text = await res.text();

    let json: unknown = null;
    try {
        json = text ? JSON.parse(text) : null;
    } catch {
        json = null;
    }

    if (!res.ok) {
        const j = json as any;
        const msg = (j && (j.message || j.error)) || `Request failed with status ${res.status}`;
        const err = new Error(msg) as Error & { status?: number };
        err.status = res.status;
        throw err;
    }

    return json as T;
}

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

    const [educationForm, setEducationForm] = useState<string>("");
    const [question, setQuestion] = useState<string>("");
    const [useMock, setUseMock] = useState<boolean>(true);

    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>("");
    const [result, setResult] = useState<PlannedResponse | null>(null);

    const canAsk = useMemo(() => {
        return normalizeWhitespace(educationForm).length > 0 && normalizeWhitespace(question).length > 0;
    }, [educationForm, question]);

    async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError("");
        setResult(null);

        if (normalizeWhitespace(educationForm).length === 0) {
            setError("School form is required.");
            return;
        }
        if (normalizeWhitespace(question).length === 0) {
            setError("Please enter a question.");
            return;
        }

        setLoading(true);
        try {
            if (useMock) {
                await new Promise((r) => setTimeout(r, 250));
                setResult(MOCK_RESPONSE);
            } else {
                const payload = {
                    municipalityCode: tenantMunicipalityCode,
                    educationForm: normalizeWhitespace(educationForm),
                    question: normalizeWhitespace(question),
                };

                const data = await fetchJson<PlannedResponse>(`${API_BASE_URL}/planned-educations/search`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                setResult(data);
            }
        } catch (err: any) {
            setError(err?.message || "Unknown error");
        } finally {
            setLoading(false);
        }
    }

    const items: PlannedItem[] = result?.items ?? result?.data?.items ?? [];

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
                    <div className={styles.card}>
                        <form onSubmit={onSubmit} className={styles.form}>
                            <label className={styles.field}>
                                <span className={styles.label}>School form \(\*\)</span>
                                <select
                                    className={styles.select}
                                    value={educationForm}
                                    onChange={(e) => setEducationForm(e.target.value)}
                                >
                                    <option value="">Select…</option>
                                    <option value="komvux">komvux</option>
                                    <option value="gymnasieskola">gymnasieskola</option>
                                    <option value="grundskola">grundskola</option>
                                </select>
                            </label>

                            <label className={styles.field}>
                                <span className={styles.label}>Your question \(\*\)</span>
                                <input
                                    className={styles.input}
                                    value={question}
                                    onChange={(e) => setQuestion(e.target.value)}
                                    placeholder="e.g. What komvux courses start in February?"
                                />
                            </label>

                            <label className={styles.row}>
                                <input type="checkbox" checked={useMock} onChange={(e) => setUseMock(e.target.checked)} />
                                <span>Use mock data \(no backend\)</span>
                            </label>

                            <button className={styles.button} type="submit" disabled={!canAsk || loading}>
                                {loading ? "Asking..." : "Ask"}
                            </button>
                        </form>
                    </div>

                    {error ? (
                        <div className={styles.error}>
                            <strong>Error:</strong> {error}
                        </div>
                    ) : null}

                    <div className={styles.results}>
                        <h2>Results</h2>

                        {!result && !loading ? <div>No results yet.</div> : null}

                        {result ? (
                            <div style={{ display: "grid", gap: 10 }}>
                                {items.length === 0 ? <div>No items returned.</div> : null}

                                {items.map((it, idx) => (
                                    <div key={it.id || it.url || it.title || it.name || `${idx}`} className={styles.item}>
                                        <div className={styles.itemTitle}>{it.title || it.name || "Untitled"}</div>

                                        <div className={styles.itemMeta}>
                                            {it.organizer ? <span>Organizer: {it.organizer}</span> : null}
                                            {it.startDate ? <span> · Start: {it.startDate}</span> : null}
                                        </div>

                                        {it.url ? (
                                            <div style={{ marginTop: 6 }}>
                                                <a href={it.url} target="_blank" rel="noreferrer">
                                                    Open
                                                </a>
                                            </div>
                                        ) : null}
                                    </div>
                                ))}
                            </div>
                        ) : null}
                    </div>
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
