import { getPublicConfig } from "@oldpages/config";

export const apiBaseUrl = getPublicConfig().apiBaseUrl.replace(/\/+$/, "");

export async function adminFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("op_access_token")
      : null;
  const res = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
