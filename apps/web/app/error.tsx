"use client";

export default function Error({
  reset,
}: Readonly<{ error: Error; reset: () => void }>) {
  return (
    <main className="shell-main">
      <section className="empty-state" role="alert">
        <h2>OldPages could not load</h2>
        <p>Refresh the workspace or retry the request.</p>
        <button className="retry-button" type="button" onClick={reset}>
          Retry
        </button>
      </section>
    </main>
  );
}
