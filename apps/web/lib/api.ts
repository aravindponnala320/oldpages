import { OldPagesApiClient } from "@oldpages/api-client";
import { getPublicConfig } from "@oldpages/config";

const isServer = typeof window === "undefined";

const baseUrl = isServer
  ? (process.env.API_BASE_URL ?? getPublicConfig().apiBaseUrl)
  : getPublicConfig().apiBaseUrl;

export const apiClient = new OldPagesApiClient({
  baseUrl,
  fetcher: fetch.bind(globalThis),
});
