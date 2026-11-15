import { OldPagesApiClient } from "@oldpages/api-client";
import { getPublicConfig } from "@oldpages/config";

const isServer = typeof window === "undefined";

/** The one place the API's address comes from; pages import it rather than re-reading env. */
export const apiBaseUrl = (
  isServer
    ? (process.env.API_BASE_URL ?? getPublicConfig().apiBaseUrl)
    : getPublicConfig().apiBaseUrl
).replace(/\/+$/, "");

/** The API's websocket origin: same host as the API, ws(s) instead of http(s). */
export const socketBaseUrl = getPublicConfig()
  .apiBaseUrl.replace(/\/+$/, "")
  .replace(/^http/, "ws");

export const apiClient = new OldPagesApiClient({
  baseUrl: apiBaseUrl,
  fetcher: fetch.bind(globalThis),
});
