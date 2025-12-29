import * as React from "react";
import styles from "../app/page.module.css";

export type Source = {
    type?: string;
    tool?: string;
    args?: Record<string, unknown>;
    data?: unknown;
    [key: string]: unknown;
};

type SourcesPanelProps = {
    sources: Source[];
};

function sourceTitle(source: Source, index: number): string {
    return (
        (typeof source.tool === "string" && source.tool) ||
        (typeof source.type === "string" && source.type) ||
        `Source ${index + 1}`
    );
}

export default function SourcesPanel({ sources }: SourcesPanelProps) {
    if (!sources.length) {
        return null;
    }

    return (
        <details className={styles.sources}>
            <summary className={styles.sourcesSummary}>Sources ({sources.length})</summary>
            <ul className={styles.sourcesList}>
                {sources.map((source, index) => (
                    <li key={`${sourceTitle(source, index)}-${index}`} className={styles.sourceItem}>
                        <div className={styles.sourceTitle}>{sourceTitle(source, index)}</div>
                        {source.args ? (
                            <div className={styles.sourceMeta}>
                                <span>Parameters:</span>
                                <code>{JSON.stringify(source.args)}</code>
                            </div>
                        ) : null}
                        {source.data ? (
                            <pre className={styles.sourceData}>{JSON.stringify(source.data, null, 2)}</pre>
                        ) : null}
                    </li>
                ))}
            </ul>
        </details>
    );
}
