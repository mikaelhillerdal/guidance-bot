// frontend/src/app/page.tsx
"use client";

import * as React from "react";
import { useMemo, useState } from "react";

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
};

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
        const msg =
            (j && (j.message || j.error)) || `Request failed with status ${res.status}`;
        const err = new Error(msg) as Error & {
            status?: number;
            bodyText?: string;
            bodyJson?: unknown;
        };
        err.status = res.status;
        err.bodyText = text;
        err.bodyJson = json;
        throw err;
    }

    return json as T;
}

export default function Page() {
    const [municipality, setMunicipality] = useState<string>("0486");
    const [educationForm, setEducationForm] = useState<string>("komvux");
    const [query, setQuery] = useState<string>("");
    const [useMock, setUseMock] = useState<boolean>(true);

    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>("");
    const [result, setResult] = useState<PlannedResponse | null>(null);

    const canSearch = useMemo(() => {
        return (
            normalizeWhitespace(municipality).length > 0 &&
            normalizeWhitespace(educationForm).length > 0
        );
    }, [municipality, educationForm]);

    async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError("");
        setResult(null);

        if (!canSearch) {
            setError("Municipality and school form are required.");
            return;
        }

        setLoading(true);
        try {
            if (useMock) {
                await new Promise((r) => setTimeout(r, 250));
                setResult(MOCK_RESPONSE);
            } else {
                const payload = {
                    municipalityCode: normalizeWhitespace(municipality),
                    educationForm: normalizeWhitespace(educationForm),
                    query: normalizeWhitespace(query),
                };

                const data = await fetchJson<PlannedResponse>("/api/planned-educations/search", {
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
        <div style={{ maxWidth: 900, margin: "0 auto", padding: 16 }}>
            <h1>Planned educations</h1>

            <form
                onSubmit={onSubmit}
                style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" }}
            >
                <label style={{ display: "grid", gap: 6 }}>
                    <span>Municipality code</span>
                    <input
                        value={municipality}
                        onChange={(e) => setMunicipality(e.target.value)}
                        placeholder="e.g. 0486"
                    />
                </label>

                <label style={{ display: "grid", gap: 6 }}>
                    <span>School form</span>
                    <select
                        value={educationForm}
                        onChange={(e) => setEducationForm(e.target.value)}
                    >
                        <option value="komvux">komvux</option>
                        <option value="gymnasieskola">gymnasieskola</option>
                        <option value="grundskola">grundskola</option>
                    </select>
                </label>

                <label style={{ display: "grid", gap: 6, gridColumn: "1 / -1" }}>
                    <span>Query (optional)</span>
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. matematik, svenska, vård"
                    />
                </label>

                <label
                    style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                        gridColumn: "1 / -1",
                    }}
                >
                    <input
                        type="checkbox"
                        checked={useMock}
                        onChange={(e) => setUseMock(e.target.checked)}
                    />
                    <span>Use mock data (no backend)</span>
                </label>

                <button
                    type="submit"
                    disabled={!canSearch || loading}
                    style={{ gridColumn: "1 / -1" }}
                >
                    {loading ? "Searching..." : "Search"}
                </button>
            </form>

            {error ? (
                <div style={{ marginTop: 16, color: "crimson" }}>
                    <strong>Error:</strong> {error}
                </div>
            ) : null}

            <div style={{ marginTop: 16 }}>
                <h2>Results</h2>
                {!result && !loading ? <div>No results yet.</div> : null}

                {result ? (
                    <div style={{ display: "grid", gap: 10 }}>
                        {items.length === 0 ? <div>No items returned.</div> : null}

                        {items.map((it) => (
                            <div
                                key={it.id || it.url || it.title || it.name || Math.random().toString(16)}
                                style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}
                            >
                                <div style={{ fontWeight: 600 }}>
                                    {it.title || it.name || "Untitled"}
                                </div>
                                <div style={{ opacity: 0.8, marginTop: 4 }}>
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

                        <details style={{ marginTop: 8 }}>
                            <summary>Raw response</summary>
                            <pre style={{ overflowX: "auto" }}>{JSON.stringify(result, null, 2)}</pre>
                        </details>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
