"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { authenticate } from "../../lib/api";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = await authenticate(mode, email, password);
      sessionStorage.setItem("egyxos.session", JSON.stringify(session));
      window.location.assign("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to authenticate");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-brand"><img src="/logo.png" alt="" /><div><strong>EGYXOS</strong><span>PASSWORD MANAGER</span></div></div>
        <p className="eyebrow">{mode === "login" ? "Welcome back" : "Create your account"}</p>
        <h1>{mode === "login" ? "Sign in securely" : "Start with EGYXOS"}</h1>
        <p className="auth-copy">Account authentication is separate from vault unlocking. Your vault secrets remain encrypted on the client.</p>
        <label>Email<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={12} required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="primary-button auth-submit" disabled={busy}>{busy ? "Working..." : mode === "login" ? "Sign in" : "Create account"}</button>
        <p className="auth-switch">{mode === "login" ? "New to EGYXOS?" : "Already have an account?"} <Link href={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "Create an account" : "Sign in"}</Link></p>
      </form>
    </main>
  );
}
