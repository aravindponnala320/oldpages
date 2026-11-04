"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import {
  Avatar,
  Badge,
  Button,
  Container,
  Icon,
  Section,
  Spinner,
  colors,
  font,
  radius,
  useToast,
} from "../../../components/ui";
import type { EventResponse, EventRSVPResponse } from "@oldpages/shared-types";

const EVENT_TYPE_LABELS: Record<string, string> = {
  book_club_meeting: "Book Club Meeting",
  book_exchange:     "Book Exchange",
  used_book_fair:    "Used Book Fair",
  donation_drive:    "Donation Drive",
  author_meetup:     "Author Meetup",
  signing:           "Signing",
  reading_session:   "Reading Session",
  silent_reading:    "Silent Reading",
  online_discussion: "Online Discussion",
  author_interview:  "Author Interview",
};

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [event, setEvent] = useState<EventResponse | null>(null);
  const [rsvp, setRsvp] = useState<EventRSVPResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [rsvpLoading, setRsvpLoading] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [calLoading, setCalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken() ?? undefined;
    apiClient
      .getEvent(id, token)
      .then(setEvent)
      .catch(() => setError("Event not found"))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRsvp = async () => {
    if (!isAuthenticated) { router.push("/"); return; }
    const token = getAccessToken();
    if (!token) return;
    setRsvpLoading(true);
    try {
      const result = await apiClient.createEventRsvp(id, {}, token);
      setRsvp(result);
      setEvent((e) => (e ? { ...e, rsvp_count: e.rsvp_count + 1 } : e));
      toast("You're going!", "success");
    } catch {
      toast("Failed to RSVP", "error");
    } finally {
      setRsvpLoading(false);
    }
  };

  const handleCancelRsvp = async () => {
    const token = getAccessToken();
    if (!token) return;
    setCancelLoading(true);
    try {
      await apiClient.cancelEventRsvp(id, token);
      setRsvp(null);
      setEvent((e) => (e ? { ...e, rsvp_count: Math.max(0, e.rsvp_count - 1) } : e));
      toast("RSVP cancelled", "info");
    } catch {
      toast("Failed to cancel RSVP", "error");
    } finally {
      setCancelLoading(false);
    }
  };

  const handleAddToCalendar = async () => {
    setCalLoading(true);
    try {
      const token = getAccessToken() ?? undefined;
      const ics = await apiClient.getEventCalendar(id, token);
      const blob = new Blob([ics], { type: "text/calendar" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `event-${id}.ics`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast("Failed to export calendar", "error");
    } finally {
      setCalLoading(false);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try { await navigator.share({ title: event?.title, url: window.location.href }); } catch { /* dismissed */ }
    } else {
      await navigator.clipboard.writeText(window.location.href);
      toast("Link copied", "success");
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !event) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container maxWidth={720}>
          <div
            style={{
              background: colors.dangerSoft,
              border: `1px solid #fecaca`,
              color: colors.dangerText,
              borderRadius: radius.lg,
              padding: "14px 18px",
              marginBottom: 16,
            }}
          >
            {error ?? "Event not found"}
          </div>
          <Button variant="ghost" onClick={() => router.back()}>← Back</Button>
        </Container>
      </div>
    );
  }

  const isPast = new Date(event.ends_at) < new Date();
  const isGoing = rsvp?.status === "going";
  const isOnline = !!event.online_url;
  const typeLabel = EVENT_TYPE_LABELS[event.event_type] ?? event.event_type.replace(/_/g, " ");
  const heroIcon =
    event.event_type === "book_club_meeting" ? "📚"
    : event.event_type === "used_book_fair" ? "🏛️"
    : event.event_type === "author_meetup" ? "✍️"
    : "📅";

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={780}>
        <Button variant="ghost" size="sm" onClick={() => router.back()} style={{ marginBottom: 12 }}>
          ← Back
        </Button>

        <div
          style={{
            height: 200,
            borderRadius: radius.xl,
            marginBottom: 20,
            background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.primaryStrong} 100%)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 68,
          }}
        >
          {heroIcon}
        </div>

        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
            <Badge variant="info" label={typeLabel} />
            {isOnline && <Badge label="Online" />}
            <Badge
              variant={event.status === "scheduled" ? "success" : event.status === "cancelled" ? "danger" : "default"}
              label={event.status}
            />
          </div>
          <h1 style={{ margin: "0 0 10px", fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text, letterSpacing: "-0.02em" }}>
            {event.title}
          </h1>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <p style={{ margin: 0, fontSize: font.size.base, color: colors.textSubtle }}>
              {new Date(event.starts_at).toLocaleString()} — {new Date(event.ends_at).toLocaleString()}
            </p>
            {event.location_name && (
              <p style={{ margin: 0, fontSize: font.size.base, color: colors.textSubtle, display: "flex", alignItems: "center", gap: 4 }}>
                <Icon.pin color={colors.textSubtle} /> {event.location_name}
              </p>
            )}
            {isOnline && event.online_url && (
              <p style={{ margin: 0, fontSize: font.size.base }}>
                <a href={event.online_url} target="_blank" rel="noopener noreferrer" style={{ color: colors.primary }}>
                  {event.online_url}
                </a>
              </p>
            )}
            <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>
              {event.rsvp_count} going
              {event.capacity && ` · ${event.capacity} capacity`}
              {event.waitlist_count > 0 && ` · ${event.waitlist_count} waitlisted`}
            </p>
          </div>
        </div>

        {!isPast && event.status === "scheduled" && (
          <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
            {!isGoing ? (
              <Button variant="primary" loading={rsvpLoading} onClick={handleRsvp}>Going</Button>
            ) : (
              <>
                <Badge variant="success" label="You're going!" size="md" />
                <Button variant="ghost" size="sm" loading={cancelLoading} onClick={handleCancelRsvp}>
                  Cancel RSVP
                </Button>
              </>
            )}
            <Button variant="secondary" onClick={handleShare}>Share</Button>
            <Button variant="secondary" loading={calLoading} onClick={handleAddToCalendar}>Add to Calendar</Button>
          </div>
        )}

        {isPast && (
          <div
            style={{
              background: colors.surfaceMuted,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.lg,
              padding: "14px 18px",
              marginBottom: 20,
            }}
          >
            <p style={{ margin: 0, fontSize: font.size.base, color: colors.textSubtle }}>
              This event has ended. {event.rsvp_count} people attended.
            </p>
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <Section title="Organizer">
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Avatar name={`User ${event.organizer.id.slice(0, 4)}`} size="md" />
              <span style={{ fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>
                User {event.organizer.id.slice(0, 8)}
              </span>
            </div>
          </Section>
        </div>

        {event.description && (
          <div style={{ marginBottom: 16 }}>
            <Section title="About this event">
              <p style={{ margin: 0, fontSize: font.size.base, color: colors.textMuted, lineHeight: font.lineHeight.relaxed, whiteSpace: "pre-wrap" }}>
                {event.description}
              </p>
            </Section>
          </div>
        )}

        <Section title={`Attendees (${event.rsvp_count})`}>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            {Array.from({ length: Math.min(event.rsvp_count, 10) }).map((_, i) => (
              <Avatar key={i} name={`Attendee ${i + 1}`} size="sm" />
            ))}
            {event.rsvp_count > 10 && (
              <span style={{ fontSize: font.size.sm, color: colors.textSubtle, marginLeft: 4 }}>
                +{event.rsvp_count - 10} more
              </span>
            )}
            {event.rsvp_count === 0 && (
              <p style={{ margin: 0, color: colors.textSubtle, fontSize: font.size.base }}>
                No attendees yet. Be the first to RSVP!
              </p>
            )}
          </div>
        </Section>
      </Container>
    </div>
  );
}
