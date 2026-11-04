"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  Input,
  Modal,
  PageHeader,
  Section,
  Select,
  Spinner,
  Tabs,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../components/ui";
import type {
  ReadingShelfResponse,
  ReadingGoalResponse,
  ReadingGoalCreateRequest,
  ReadingNoteResponse,
  ReadingStatisticResponse,
} from "@oldpages/shared-types";

type Tab = "shelves" | "goals" | "stats" | "notes";

const SHELF_EMOJI: Record<string, string> = {
  want_to_read: "📖",
  currently_reading: "📚",
  finished: "✅",
  did_not_finish: "🚫",
  owned: "🏠",
  previously_owned: "📤",
  available_for_exchange: "🔄",
  available_for_lending: "🤝",
  favorites: "❤️",
  academic_books: "🎓",
  rare_collection: "💎",
  custom: "📂",
};

export default function ReadingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("shelves");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={1080}>
        <PageHeader
          eyebrow="Your library"
          title="Reading Tracker"
          subtitle="Track your reading journey, set goals, and manage your bookshelves."
        />

        <div style={{ marginBottom: 20 }}>
          <Tabs
            tabs={[
              { key: "shelves", label: "My Shelves" },
              { key: "goals", label: "Goals" },
              { key: "stats", label: "Statistics" },
              { key: "notes", label: "Notes" },
            ]}
            value={activeTab}
            onChange={(k) => setActiveTab(k as Tab)}
          />
        </div>

        {activeTab === "shelves" && <ShelvesTab />}
        {activeTab === "goals" && <GoalsTab />}
        {activeTab === "stats" && <StatsTab />}
        {activeTab === "notes" && <NotesTab />}
      </Container>
    </div>
  );
}

function ShelvesTab() {
  const [shelves, setShelves] = useState<ReadingShelfResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedShelf, setSelectedShelf] = useState<ReadingShelfResponse | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listMyReadingShelves(token)
      .then((res) => setShelves(res.items))
      .catch((err) => toast(err.message ?? "Failed to load shelves", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
        <Spinner />
      </div>
    );
  }

  if (selectedShelf) {
    return (
      <div>
        <Button variant="ghost" size="sm" onClick={() => setSelectedShelf(null)} style={{ marginBottom: 12 }}>
          ← Back to Shelves
        </Button>
        <h2 style={{ margin: "0 0 20px", fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text }}>
          {SHELF_EMOJI[selectedShelf.shelf_type] ?? "📂"} {selectedShelf.name}
        </h2>
        {selectedShelf.items.length === 0 ? (
          <EmptyState
            icon={<Icon.book size={26} color={colors.primary} />}
            title="No books on this shelf yet"
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 14 }}>
            {selectedShelf.items.map((item) => (
              <div
                key={item.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 14,
                }}
              >
                <div
                  style={{
                    width: "100%",
                    aspectRatio: "3/4",
                    background: colors.surfaceMuted,
                    borderRadius: radius.md,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 10,
                  }}
                >
                  <Icon.book size={28} color={colors.textFaint} />
                </div>
                <p style={{ margin: "0 0 2px", fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.book.title}
                </p>
                <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>
                  {item.book.authors.join(", ")}
                </p>
                {item.note && (
                  <p style={{ margin: "6px 0 0", fontSize: font.size.sm, color: colors.textFaint, fontStyle: "italic" }}>
                    {item.note}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return shelves.length === 0 ? (
    <EmptyState
      icon={<Icon.book size={26} color={colors.primary} />}
      title="No shelves found"
      description="Start adding books to track your reading!"
    />
  ) : (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 14 }}>
      {shelves.map((shelf) => (
        <button
          key={shelf.id}
          onClick={() => setSelectedShelf(shelf)}
          style={{
            all: "unset",
            cursor: "pointer",
            display: "block",
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.xl,
            padding: 18,
            textAlign: "left",
            boxShadow: shadow.sm,
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 8 }}>{SHELF_EMOJI[shelf.shelf_type] ?? "📂"}</div>
          <p style={{ margin: 0, fontWeight: font.weight.bold, color: colors.text, fontSize: font.size.md }}>
            {shelf.name}
          </p>
          <p style={{ margin: "3px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>
            {shelf.items.length} {shelf.items.length === 1 ? "book" : "books"}
          </p>
          {!shelf.is_system && (
            <div style={{ marginTop: 8 }}>
              <Badge label="Custom" />
            </div>
          )}
        </button>
      ))}
    </div>
  );
}

function GoalsTab() {
  const [goals, setGoals] = useState<ReadingGoalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const { toast } = useToast();

  const [form, setForm] = useState<{
    goal_type: ReadingGoalCreateRequest["goal_type"];
    target_value: string;
    period_start: string;
    period_end: string;
  }>({
    goal_type: "books_per_year",
    target_value: "12",
    period_start: `${new Date().getFullYear()}-01-01`,
    period_end: `${new Date().getFullYear()}-12-31`,
  });

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listReadingGoals(token)
      .then((res) => setGoals(res.items))
      .catch((err) => toast(err.message ?? "Failed to load goals", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  const handleCreate = async () => {
    const token = getAccessToken();
    if (!token) return;
    setCreating(true);
    try {
      const created = await apiClient.createReadingGoal(
        {
          goal_type: form.goal_type,
          target_value: Number(form.target_value),
          period_start: form.period_start,
          period_end: form.period_end,
        },
        token,
      );
      setGoals((prev) => [created, ...prev]);
      setShowCreate(false);
      toast("Goal created", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to create goal", "error");
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
        <Spinner />
      </div>
    );
  }

  const progressPct = (g: ReadingGoalResponse) =>
    g.target_value === 0 ? 0 : Math.min(100, Math.round((g.current_value / g.target_value) * 100));

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>
          Reading Goals
        </h2>
        <Button variant="primary" size="sm" onClick={() => setShowCreate(true)} leftIcon={<Icon.plus size={14} />}>
          New Goal
        </Button>
      </div>

      {goals.length === 0 ? (
        <EmptyState
          icon={<Icon.check size={26} color={colors.primary} />}
          title="No reading goals yet"
          description="Set a goal to track your progress!"
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {goals.map((goal) => {
            const pct = progressPct(goal);
            return (
              <div
                key={goal.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 18,
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
                  <div>
                    <p style={{ margin: 0, fontWeight: font.weight.bold, color: colors.text, fontSize: font.size.md }}>
                      {goal.goal_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </p>
                    <p style={{ margin: "3px 0 0", fontSize: font.size.sm, color: colors.textFaint }}>
                      {new Date(goal.period_start).toLocaleDateString()} –{" "}
                      {new Date(goal.period_end).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge
                    variant={goal.status === "completed" ? "success" : goal.status === "cancelled" ? "danger" : "info"}
                    label={goal.status}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: font.size.sm, color: colors.textSubtle, marginBottom: 6 }}>
                  <span>{goal.current_value} / {goal.target_value}</span>
                  <span style={{ fontWeight: font.weight.semibold, color: colors.primary }}>{pct}%</span>
                </div>
                <ProgressBar pct={pct} />
              </div>
            );
          })}
        </div>
      )}

      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Create Reading Goal"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)} disabled={creating}>Cancel</Button>
            <Button variant="primary" loading={creating} onClick={handleCreate}>Create Goal</Button>
          </>
        }
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Select
            label="Goal Type"
            value={form.goal_type}
            onChange={(e) => setForm({ ...form, goal_type: e.target.value as ReadingGoalCreateRequest["goal_type"] })}
            options={[
              { value: "books_per_year", label: "Books per Year" },
              { value: "pages_per_month", label: "Pages per Month" },
              { value: "minutes_per_day", label: "Minutes per Day" },
              { value: "genre", label: "Genre" },
              { value: "author", label: "Author" },
              { value: "language", label: "Language" },
            ]}
          />
          <Input
            label="Target"
            type="number"
            min={1}
            value={form.target_value}
            onChange={(e) => setForm({ ...form, target_value: e.target.value })}
          />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Input
              label="Start Date"
              type="date"
              value={form.period_start}
              onChange={(e) => setForm({ ...form, period_start: e.target.value })}
            />
            <Input
              label="End Date"
              type="date"
              value={form.period_end}
              onChange={(e) => setForm({ ...form, period_end: e.target.value })}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}

function StatsTab() {
  const [stats, setStats] = useState<ReadingStatisticResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listReadingStatistics(token)
      .then((res) => setStats(res.items))
      .catch((err) => toast(err.message ?? "Failed to load stats", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
        <Spinner />
      </div>
    );
  }

  const latest = stats[0];
  if (!latest) {
    return (
      <EmptyState
        icon={<Icon.book size={26} color={colors.primary} />}
        title="No reading statistics yet"
        description="Start reading and tracking your progress!"
      />
    );
  }

  const topGenres = Object.entries(latest.genres).sort(([, a], [, b]) => b - a).slice(0, 5);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Books Completed", value: latest.books_completed },
          { label: "Pages Read", value: latest.pages_read.toLocaleString() },
          { label: "Minutes Read", value: latest.minutes_read.toLocaleString() },
          { label: "Reading Streak", value: `${latest.reading_streak_days}d` },
        ].map((s) => (
          <div
            key={s.label}
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.xl,
              padding: 18,
              boxShadow: shadow.sm,
            }}
          >
            <div style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text }}>
              {s.value}
            </div>
            <div style={{ fontSize: font.size.sm, color: colors.textSubtle, marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {topGenres.length > 0 && (
        <Section title="Favorite genres">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {topGenres.map(([genre, count]) => {
              const max = topGenres[0]?.[1] ?? 1;
              const pct = Math.round((count / max) * 100);
              return (
                <div key={genre}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: font.size.sm, color: colors.textMuted, marginBottom: 4 }}>
                    <span>{genre}</span>
                    <span style={{ color: colors.textSubtle }}>{count} books</span>
                  </div>
                  <ProgressBar pct={pct} />
                </div>
              );
            })}
          </div>
        </Section>
      )}
    </div>
  );
}

function NotesTab() {
  const [notes, setNotes] = useState<ReadingNoteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const NOTE_ICONS: Record<string, string> = { note: "📝", highlight: "🖊️", quote: "💬" };

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listReadingNotes(token)
      .then((res) => setNotes(res.items))
      .catch((err) => toast(err.message ?? "Failed to load notes", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
        <Spinner />
      </div>
    );
  }

  return notes.length === 0 ? (
    <EmptyState
      icon={<Icon.chat size={26} color={colors.primary} />}
      title="No reading notes yet"
      description="Add notes while reading to capture your thoughts."
    />
  ) : (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {notes.map((note) => (
        <div
          key={note.id}
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.xl,
            padding: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
            <span style={{ fontSize: 18 }}>{NOTE_ICONS[note.note_type] ?? "📝"}</span>
            <span style={{ fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>
              {note.book.title}
            </span>
            <Badge label={note.note_type} />
            {note.page_number && <span style={{ color: colors.textFaint, fontSize: font.size.xs }}>p. {note.page_number}</span>}
          </div>
          <p style={{ margin: 0, lineHeight: font.lineHeight.relaxed, color: colors.textMuted, fontStyle: note.note_type === "quote" ? "italic" : "normal", fontSize: font.size.base }}>
            {note.note_type === "quote" ? `"${note.body}"` : note.body}
          </p>
          <p style={{ margin: "8px 0 0", fontSize: font.size.xs, color: colors.textFaint }}>
            {new Date(note.created_at).toLocaleDateString()}
          </p>
        </div>
      ))}
    </div>
  );
}

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div style={{ background: colors.divider, borderRadius: radius.pill, height: 8, overflow: "hidden" }}>
      <div
        style={{
          height: "100%",
          width: `${pct}%`,
          background: colors.primary,
          borderRadius: radius.pill,
          transition: "width 0.3s",
        }}
      />
    </div>
  );
}
