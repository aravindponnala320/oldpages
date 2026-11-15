import { colors, font } from "./ui";

/** Minimum password length; the API refuses anything shorter. */
export const MIN_PASSWORD_LENGTH = 12;

export function PasswordStrength({ password }: { password: string }) {
  const checks = [
    password.length >= MIN_PASSWORD_LENGTH,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];
  const score = checks.filter(Boolean).length;
  const bars = ["#ef4444", "#f97316", "#eab308", "#22c55e"];
  const labels = ["Weak", "Fair", "Good", "Strong"];
  const color = bars[score - 1] ?? colors.borderStrong;
  const label = labels[score - 1] ?? "";

  return (
    <div>
      <div style={{ display: "flex", gap: 3, marginTop: 8 }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              background: i < score ? color : colors.borderStrong,
              transition: "background 0.2s",
            }}
          />
        ))}
      </div>
      {label && (
        <p
          style={{
            fontSize: font.size.xs,
            color,
            margin: "4px 0 0",
            fontWeight: font.weight.semibold,
          }}
        >
          {label}
        </p>
      )}
    </div>
  );
}
