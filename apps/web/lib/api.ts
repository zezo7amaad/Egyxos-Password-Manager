const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SessionResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user_id: string;
};

export async function authenticate(
  mode: "login" | "register",
  email: string,
  password: string
): Promise<SessionResponse> {
  const response = await fetch(`${API_URL}/api/v1/auth/${mode}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to authenticate");
  }
  return response.json() as Promise<SessionResponse>;
}
