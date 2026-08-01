interface Env {
  DB: D1Database;
  INTAKE_PEPPER: string;
  EXPORT_TOKEN: string;
}

type Json = Record<string, unknown>;

const allowedTopLevel = new Set([
  "schema_version", "run_id", "observed_day", "provenance", "provider",
  "data_center", "recipe_id", "recipe_revision", "app_version", "hardware",
  "storage", "cache_state", "timings_ms", "outcome",
]);

const forbidden = [
  /\bhf_[A-Za-z0-9]{20,}\b/,
  /\brpa_[A-Za-z0-9]{20,}\b/,
  /-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----/,
  /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}/i,
  /(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])/,
  /\bssh\s+[^\n]*@/i,
];

const json = (value: unknown, status = 200): Response => new Response(
  JSON.stringify(value),
  { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } },
);

const bytesToHex = (value: ArrayBuffer): string => [...new Uint8Array(value)]
  .map((byte) => byte.toString(16).padStart(2, "0"))
  .join("");

const sha256 = async (value: string): Promise<string> => bytesToHex(
  await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)),
);

const randomToken = (): string => {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
};

const isObject = (value: unknown): value is Json => Boolean(value) && typeof value === "object" && !Array.isArray(value);

const validateObservation = (value: unknown): string | null => {
  if (!isObject(value)) return "The body must be a JSON object.";
  if (Object.keys(value).some((key) => !allowedTopLevel.has(key))) return "The observation contains an unsupported field.";
  if (value.schema_version !== 1) return "Unsupported schema version.";
  if (typeof value.run_id !== "string" || !/^[0-9a-f-]{36}$/i.test(value.run_id)) return "Invalid run_id.";
  if (typeof value.observed_day !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value.observed_day)) return "Invalid observed_day.";
  if (!['imported', 'client-measured'].includes(String(value.provenance))) return "Automatic intake accepts imported or client-measured provenance.";
  if (!['runpod', 'vast'].includes(String(value.provider))) return "Unsupported provider.";
  if (typeof value.data_center !== "string" || value.data_center.length < 1 || value.data_center.length > 80) return "Invalid data_center.";
  if (!isObject(value.hardware) || !isObject(value.storage) || !isObject(value.timings_ms) || !isObject(value.outcome)) return "Missing structured observation facts.";
  if (!['cold', 'warm-dependencies', 'warm-model', 'unknown'].includes(String(value.cache_state))) return "Invalid cache_state.";
  const serialized = JSON.stringify(value);
  if (serialized.length > 20_000) return "Observation exceeds the size limit.";
  if (forbidden.some((pattern) => pattern.test(serialized))) return "Observation resembles private connection or credential data.";
  return null;
};

const handleSubmission = async (request: Request, env: Env): Promise<Response> => {
  if (!request.headers.get("content-type")?.toLowerCase().includes("application/json")) {
    return json({ error: "Content-Type must be application/json." }, 415);
  }
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON." }, 400);
  }
  const validationError = validateObservation(body);
  if (validationError) return json({ error: validationError }, 422);
  const observation = body as Json;
  const source = request.headers.get("CF-Connecting-IP") ?? "unavailable";
  const contributorKey = await sha256(`${env.INTAKE_PEPPER}:${source}`);
  const since = new Date(Date.now() - 60 * 60 * 1000).toISOString();
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) AS count FROM observations WHERE contributor_key = ? AND received_at >= ?",
  ).bind(contributorKey, since).first<{ count: number }>();
  if ((recent?.count ?? 0) >= 20) return json({ error: "Submission rate limit reached." }, 429);

  const payload = JSON.stringify(observation);
  const receipt = randomToken();
  try {
    await env.DB.prepare(
      "INSERT INTO observations (run_id, payload, payload_sha256, contributor_key, receipt_sha256, status, received_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
    ).bind(
      observation.run_id,
      payload,
      await sha256(payload),
      contributorKey,
      await sha256(receipt),
      new Date().toISOString(),
    ).run();
  } catch {
    return json({ error: "That run_id has already been submitted." }, 409);
  }
  return json({ status: "pending", run_id: observation.run_id, withdrawal_receipt: receipt }, 202);
};

const handleWithdrawal = async (request: Request, env: Env, runID: string): Promise<Response> => {
  const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!token) return json({ error: "Withdrawal receipt required." }, 401);
  const result = await env.DB.prepare(
    "UPDATE observations SET status = 'withdrawn', withdrawn_at = ? WHERE run_id = ? AND receipt_sha256 = ?",
  ).bind(new Date().toISOString(), runID, await sha256(token)).run();
  if (!result.meta.changes) return json({ error: "Observation or receipt not found." }, 404);
  return json({ status: "withdrawn", run_id: runID });
};

const handleExport = async (request: Request, env: Env): Promise<Response> => {
  if (request.headers.get("authorization") !== `Bearer ${env.EXPORT_TOKEN}`) {
    return json({ error: "Not authorized." }, 401);
  }
  const result = await env.DB.prepare(
    "SELECT payload FROM observations WHERE status = 'pending' ORDER BY received_at ASC LIMIT 1000",
  ).all<{ payload: string }>();
  return json({ observations: result.results.map((row) => JSON.parse(row.payload)) });
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ status: "ok", service: "podhammer-truth-intake", schema_version: 1 });
    }
    if (request.method === "POST" && url.pathname === "/v1/observations") {
      return handleSubmission(request, env);
    }
    if (request.method === "DELETE" && url.pathname.startsWith("/v1/observations/")) {
      return handleWithdrawal(request, env, decodeURIComponent(url.pathname.slice("/v1/observations/".length)));
    }
    if (request.method === "GET" && url.pathname === "/v1/export") {
      return handleExport(request, env);
    }
    return json({ error: "Not found." }, 404);
  },
} satisfies ExportedHandler<Env>;
