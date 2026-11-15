"use client";

import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "../lib/auth";
import { apiBaseUrl } from "../lib/api";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 15 * 1024 * 1024;
export const MAX_LISTING_PHOTOS = 12;

export type ListingPhoto = {
  key: string;
  previewUrl: string;
  status: "uploading" | "done" | "error";
  mediaId?: string;
  error?: string;
};

async function uploadPhoto(file: File): Promise<string> {
  const token = getAccessToken();
  const auth = { Authorization: `Bearer ${token}` };
  const urlRes = await fetch(`${apiBaseUrl}/api/v1/media/upload-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify({
      filename: file.name || "photo.jpg",
      content_type: file.type,
      byte_size: file.size,
    }),
  });
  const upload = await urlRes.json();
  if (!urlRes.ok) throw new Error(upload.detail ?? "Could not start upload");

  const putRes = await fetch(upload.upload_url, {
    method: "PUT",
    headers: upload.headers,
    body: file,
  });
  if (!putRes.ok) throw new Error("Upload failed");

  const doneRes = await fetch(
    `${apiBaseUrl}/api/v1/media/${upload.id}/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...auth },
      body: JSON.stringify({ byte_size: file.size }),
    },
  );
  if (!doneRes.ok)
    throw new Error(
      (await doneRes.json().catch(() => ({}))).detail ?? "Upload failed",
    );
  return upload.id;
}

/** Take a photo with the camera or pick from the device; each file uploads as soon as it is chosen. */
export function ListingPhotoPicker({
  photos,
  onChange,
}: {
  photos: ListingPhoto[];
  onChange: (update: (prev: ListingPhoto[]) => ListingPhoto[]) => void;
}) {
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const remaining = MAX_LISTING_PHOTOS - photos.length;

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
    return () => stream?.getTracks().forEach((track) => track.stop());
  }, [stream]);

  async function takePhoto() {
    setCameraError(null);
    // Phones open their own camera app via the capture input; browsers ignore `capture`
    // on computers, so use the webcam in-page there.
    const isPhone = window.matchMedia("(pointer: coarse)").matches;
    if (isPhone || !navigator.mediaDevices?.getUserMedia) {
      cameraRef.current?.click();
      return;
    }
    try {
      setStream(
        await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        }),
      );
    } catch {
      setCameraError(
        "Couldn't open the camera. Allow camera access in your browser, or use Upload photos.",
      );
    }
  }

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob)
          addFiles([
            new File([blob], `camera-${Date.now()}.jpg`, {
              type: "image/jpeg",
            }),
          ]);
        setStream(null);
      },
      "image/jpeg",
      0.9,
    );
  }

  function addFiles(fileList: FileList | File[] | null) {
    const files = Array.from(fileList ?? []).slice(0, remaining);
    for (const file of files) {
      const key = `${Date.now()}-${Math.random()}`;
      const previewUrl = URL.createObjectURL(file);
      const invalid = !ACCEPTED_TYPES.includes(file.type)
        ? "Use a JPG, PNG or WebP image"
        : file.size > MAX_BYTES
          ? "Image is larger than 15 MB"
          : undefined;
      onChange((prev) => [
        ...prev,
        {
          key,
          previewUrl,
          status: invalid ? "error" : "uploading",
          error: invalid,
        },
      ]);
      if (invalid) continue;
      uploadPhoto(file)
        .then((mediaId) =>
          onChange((prev) =>
            prev.map((p) =>
              p.key === key ? { ...p, status: "done", mediaId } : p,
            ),
          ),
        )
        .catch((err: Error) =>
          onChange((prev) =>
            prev.map((p) =>
              p.key === key ? { ...p, status: "error", error: err.message } : p,
            ),
          ),
        );
    }
  }

  function remove(key: string) {
    onChange((prev) => {
      const photo = prev.find((p) => p.key === key);
      if (photo) URL.revokeObjectURL(photo.previewUrl);
      return prev.filter((p) => p.key !== key);
    });
  }

  const buttonStyle: React.CSSProperties = {
    flex: 1,
    padding: "0.75rem",
    border: "1.5px dashed #cbd5e1",
    borderRadius: 8,
    background: "#f8fafc",
    color: "#374151",
    fontSize: "0.875rem",
    fontWeight: 600,
    cursor: remaining > 0 ? "pointer" : "not-allowed",
    opacity: remaining > 0 ? 1 : 0.5,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <button
          type="button"
          style={buttonStyle}
          disabled={remaining <= 0}
          onClick={takePhoto}
        >
          📷 Take photo
        </button>
        <button
          type="button"
          style={buttonStyle}
          disabled={remaining <= 0}
          onClick={() => galleryRef.current?.click()}
        >
          🖼️ Upload photos
        </button>
      </div>
      {cameraError && (
        <p style={{ margin: 0, fontSize: "0.8rem", color: "#b42318" }}>
          {cameraError}
        </p>
      )}
      {stream && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: "rgba(0,0,0,0.85)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "1rem",
            padding: 16,
          }}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              maxWidth: "100%",
              maxHeight: "70vh",
              borderRadius: 8,
              background: "#000",
            }}
          />
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button
              type="button"
              onClick={capture}
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: 999,
                border: "none",
                background: "#2563eb",
                color: "white",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              📸 Capture
            </button>
            <button
              type="button"
              onClick={() => setStream(null)}
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: 999,
                border: "1px solid #9ca3af",
                background: "transparent",
                color: "white",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      <input
        ref={cameraRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        capture="environment"
        hidden
        onChange={(e) => {
          addFiles(e.target.files);
          e.target.value = "";
        }}
      />
      <input
        ref={galleryRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        multiple
        hidden
        onChange={(e) => {
          addFiles(e.target.files);
          e.target.value = "";
        }}
      />

      {photos.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(96px, 1fr))",
            gap: "0.5rem",
          }}
        >
          {photos.map((photo, i) => (
            <div
              key={photo.key}
              style={{
                position: "relative",
                aspectRatio: "1",
                borderRadius: 8,
                overflow: "hidden",
                border: `1.5px solid ${photo.status === "error" ? "#fca5a5" : "#e5e7eb"}`,
              }}
            >
              <img
                src={photo.previewUrl}
                alt={`Photo ${i + 1}`}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  opacity: photo.status === "done" ? 1 : 0.5,
                }}
              />
              {i === 0 && photo.status === "done" && (
                <span
                  style={{
                    position: "absolute",
                    left: 4,
                    bottom: 4,
                    background: "#2563eb",
                    color: "white",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: 4,
                  }}
                >
                  Cover
                </span>
              )}
              {photo.status !== "done" && (
                <span
                  style={{
                    position: "absolute",
                    inset: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: 4,
                    textAlign: "center",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: photo.status === "error" ? "#b42318" : "#374151",
                  }}
                >
                  {photo.status === "uploading" ? "Uploading…" : photo.error}
                </span>
              )}
              <button
                type="button"
                aria-label="Remove photo"
                onClick={() => remove(photo.key)}
                style={{
                  position: "absolute",
                  top: 4,
                  right: 4,
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  border: "none",
                  background: "rgba(0,0,0,0.6)",
                  color: "white",
                  fontSize: "0.8rem",
                  lineHeight: 1,
                  cursor: "pointer",
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      <p style={{ margin: 0, fontSize: "0.75rem", color: "#9ca3af" }}>
        Up to {MAX_LISTING_PHOTOS} photos. The first one is the cover. Clear
        photos of the cover and any damage help it sell faster.
      </p>
    </div>
  );
}
