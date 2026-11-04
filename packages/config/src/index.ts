export type PublicConfig = {
  apiBaseUrl: string;
};

export function getPublicConfig(): PublicConfig {
  return {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  };
}
