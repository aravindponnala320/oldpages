"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
  LinkButton,
  PageHeader,
  Select,
  Spinner,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../components/ui";
import type { EventResponse, EventType } from "@oldpages/shared-types";

const EVENT_TYPE_LABELS: Partial<Record<EventType, string>> = {
  book_club_meeting: "Book Club",
  book_exchange:     "Book Exchange",
  used_book_fair:    "Book Fair",
  donation_drive:    "Donation Drive",
  author_meetup:     "Author Meetup",
  signing:           "Signing",
  reading_session:   "Reading Session",
  online_discussion: "Online Discussion",
};

function EventCard({
  event,
  onRsvp,
  rsvpLoading,
}: {
  event: EventResponse;
  onRsvp: (id: string) => void;
  rsvpLoading: boolean;
}) {
  const isOnline = !!event.online_url;
  const typeLabel = EVENT_TYPE_LABELS[event.event_type] ?? event.event_type.replace(/_/g, " ");
  const isPast = new Date(event.ends_at) < new Date();

  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        padding: 18,
        boxShadow: shadow.sm,
      }}
    >
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
        <Badge variant="info" label={typeLabel} />
        {isOnline && <Badge label="Online" />}
        {isPast && <Badge label="Past" />}
      </div>
      <Link href={`/events/${event.id}`} style={{ textDecoration: "none" }}>
        <h3
          style={{
            margin: "0 0 8px",
            fontSize: font.size.md,
            fontWeight: font.weight.bold,
            color: colors.text,
            lineHeight: font.lineHeight.snug,
          }}
        >
          {event.title}
        </h3>
      </Link>
      <div style={{ display: "flex", flexDirection: "column", gap: 3, marginBottom: 12 }}>
        <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>
          {new Date(event.starts_at).toLocaleDateString(undefined, {
            weekday: "short",
            month: "short",
            day: "numeric",
          })}
          {" · "}
          {new Date(event.starts_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
        {event.location_name && (
          <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>
            {event.location_name}
          </p>
        )}
        <p style={{ margin: 0, fontSize: font.size.xs, color: colors.textFaint }}>
          {event.rsvp_count} going{event.waitlist_count > 0 ? ` · ${event.waitlist_count} waitlisted` : ""}
        </p>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <LinkButton href={`/events/${event.id}`} variant="secondary" size="sm">View</LinkButton>
        {!isPast && event.status === "scheduled" && (
          <Button variant="primary" size="sm" loading={rsvpLoading} onClick={() => onRsvp(event.id)}>
            RSVP
          </Button>
        )}
      </div>
    </div>
  );
}

export default function EventsPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [events, setEvents] = useState<EventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [rsvpLoading, setRsvpLoading] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<EventType | "">("");
  const [onlineFilter, setOnlineFilter] = useState<"all" | "online" | "in_person">("all");

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    setLoading(true);
    const token = getAccessToken() ?? undefined;
    try {
      const res = await apiClient.listEvents({}, token);
      setEvents(res.items);
    } catch {
      toast("Failed to load events", "error");
    } finally {
      setLoading(false);
    }
  }

  const handleRsvp = async (eventId: string) => {
    if (!isAuthenticated) {
      router.push("/");
      return;
    }
    const token = getAccessToken();
    if (!token) return;
    setRsvpLoading(eventId);
    try {
      await apiClient.createEventRsvp(eventId, {}, token);
      setEvents((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, rsvp_count: e.rsvp_count + 1 } : e)),
      );
      toast("RSVP confirmed", "success");
    } catch {
      toast("Failed to RSVP", "error");
    } finally {
      setRsvpLoading(null);
    }
  };

  const filtered = events.filter((e) => {
    if (typeFilter && e.event_type !== typeFilter) return false;
    if (onlineFilter === "online" && !e.online_url) return false;
    if (onlineFilter === "in_person" && e.online_url) return false;
    return true;
  });

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Community"
          title="Events"
          subtitle="Book fairs, clubs, author meetups, and more near you."
          actions={<Button variant="secondary" onClick={loadEvents}>Refresh</Button>}
        />

        <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
          <Select
            containerStyle={{ width: 200 }}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as EventType | "")}
            options={[
              { value: "", label: "All types" },
              ...Object.entries(EVENT_TYPE_LABELS).map(([val, label]) => ({ value: val, label: label! })),
            ]}
          />
          <Select
            containerStyle={{ width: 200 }}
            value={onlineFilter}
            onChange={(e) => setOnlineFilter(e.target.value as typeof onlineFilter)}
            options={[
              { value: "all", label: "Online & In-Person" },
              { value: "online", label: "Online only" },
              { value: "in_person", label: "In-person only" },
            ]}
          />
          <span style={{ color: colors.textFaint, fontSize: font.size.sm, marginLeft: "auto" }}>
            {filtered.length} event{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spinner size="md" />
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <EmptyState
            icon={<Icon.book size={24} color={colors.primary} />}
            title="No events found"
            description="Check back later or adjust your filters."
          />
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {filtered.map((e) => (
            <EventCard key={e.id} event={e} onRsvp={handleRsvp} rsvpLoading={rsvpLoading === e.id} />
          ))}
        </div>
      </Container>
    </div>
  );
}
