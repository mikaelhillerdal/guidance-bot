"use client";

import * as React from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import styles from "../app/page.module.css";
import SourcesPanel, { Source } from "./SourcesPanel";

export type ChatMessage = {
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
};

type ChatProps = {
    tenantId: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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

export default function Chat({ tenantId }: ChatProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            role: "assistant",
            content: "Hi! Ask me about education options, and I will find results for you.",
        },
    ]);
    const [draft, setDraft] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const scrollRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, [messages, loading]);

    const canSend = useMemo(() => normalizeWhitespace(draft).length > 0 && !loading, [draft, loading]);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");

        const trimmed = normalizeWhitespace(draft);
        if (!trimmed) {
            return;
        }

        const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
        setMessages(nextMessages);
        setDraft("");
        setLoading(true);

        try {
            const payload = {
                tenant_id: tenantId,
                messages: nextMessages.map((m) => ({ role: m.role, content: m.content })),
            };

            const data = await fetchJson<{ answer: string; sources?: Source[] }>(`${API_BASE_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: data.answer,
                    sources: data.sources || [],
                },
            ]);
        } catch (err: any) {
            setError(err?.message || "Unknown error");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.chatCard}>
            <div className={styles.chatHeader}>
                <div>
                    <h2 className={styles.chatTitle}>Chat with the Guidance Bot</h2>
                    <p className={styles.chatSubtitle}>Ask about upcoming education opportunities or programs.</p>
                </div>
                <div className={styles.chatTenant}>Tenant: {tenantId}</div>
            </div>

            <div className={styles.chatMessages}>
                {messages.length === 0 ? <div className={styles.emptyState}>Start the conversation below.</div> : null}

                {messages.map((message, idx) => (
                    <div
                        key={`${message.role}-${idx}`}
                        className={
                            message.role === "user" ? styles.messageRowUser : styles.messageRowAssistant
                        }
                    >
                        <div
                            className={
                                message.role === "user" ? styles.messageBubbleUser : styles.messageBubbleAssistant
                            }
                        >
                            <div className={styles.messageRole}>
                                {message.role === "user" ? "You" : "Guidance Bot"}
                            </div>
                            <div className={styles.messageContent}>{message.content}</div>
                            {message.sources && message.sources.length > 0 ? (
                                <SourcesPanel sources={message.sources} />
                            ) : null}
                        </div>
                    </div>
                ))}

                {loading ? <div className={styles.loadingIndicator}>The bot is thinking…</div> : null}
                <div ref={scrollRef} />
            </div>

            {error ? (
                <div className={styles.error}>
                    <strong>Error:</strong> {error}
                </div>
            ) : null}

            <form onSubmit={onSubmit} className={styles.composer}>
                <textarea
                    className={styles.composerInput}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    placeholder="Type your message..."
                    rows={3}
                />
                <button className={styles.composerButton} type="submit" disabled={!canSend}>
                    {loading ? "Sending..." : "Send"}
                </button>
            </form>
        </div>
    );
}
