"use client";

export default function Error({
  reset,
}: Readonly<{ error: Error; reset: () => void }>) {
  return (
    <main className="admin-main">
      <section className="admin-panel" role="alert">
        <h1 className="admin-title">Admin could not load</h1>
        <p className="admin-muted">
          Retry the request from the current workspace.
        </p>
        <button type="button" onClick={reset}>
          Retry
        </button>
      </section>
    </main>
  );
}
