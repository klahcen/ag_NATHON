/** Backend base URL. Set NEXT_PUBLIC_API_URL in Railway (frontend service). */
export function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  return base || "http://localhost:8000";
}
