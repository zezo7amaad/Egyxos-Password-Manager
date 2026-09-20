"use client";

import {
  Bell,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Filter,
  Folder,
  KeyRound,
  LockKeyhole,
  MoreVertical,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Star,
  Tags,
  Trash2,
  UserRound,
  UsersRound,
  WandSparkles
} from "lucide-react";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";

type VaultItem = {
  id: string;
  name: string;
  username: string;
  password: string;
  type: "Login" | "Card" | "Identity" | "Secure Note";
  icon: string;
  modified: string;
  favorite: boolean;
  website?: string;
  folder?: string;
  tags: string[];
};

const initialItems: VaultItem[] = [
  { id: "github", name: "GitHub", username: "john.doe", password: "N0t-a-real-password!", type: "Login", icon: "◉", modified: "2h ago", favorite: true, website: "https://github.com", folder: "Development", tags: ["Work", "Development"] },
  { id: "google", name: "Google", username: "john.doe@gmail.com", password: "N0t-a-real-password!", type: "Login", icon: "G", modified: "5h ago", favorite: true, website: "https://accounts.google.com", folder: "Personal", tags: ["Personal"] },
  { id: "aws", name: "AWS", username: "admin", password: "N0t-a-real-password!", type: "Login", icon: "aws", modified: "1d ago", favorite: true, website: "https://aws.amazon.com", folder: "Development", tags: ["Work"] },
  { id: "netflix", name: "Netflix", username: "john.doe", password: "N0t-a-real-password!", type: "Login", icon: "N", modified: "1d ago", favorite: true, website: "https://netflix.com", folder: "Entertainment", tags: [] },
  { id: "spotify", name: "Spotify", username: "john.doe", password: "N0t-a-real-password!", type: "Login", icon: "●", modified: "2d ago", favorite: false, website: "https://spotify.com", folder: "Entertainment", tags: [] },
  { id: "microsoft", name: "Microsoft", username: "john.doe@outlook.com", password: "N0t-a-real-password!", type: "Login", icon: "⊞", modified: "2d ago", favorite: false, website: "https://microsoft.com", folder: "Work", tags: ["Work"] },
  { id: "facebook", name: "Facebook", username: "john.doe", password: "N0t-a-real-password!", type: "Login", icon: "f", modified: "3d ago", favorite: false, website: "https://facebook.com", folder: "Personal", tags: [] },
  { id: "linkedin", name: "LinkedIn", username: "john.doe", password: "N0t-a-real-password!", type: "Login", icon: "in", modified: "3d ago", favorite: false, website: "https://linkedin.com", folder: "Work", tags: ["Work"] }
];

const categories = ["All", "Logins", "Cards", "Identities", "Secure Notes"];

export default function Home() {
  const [items, setItems] = useState(initialItems);
  const [selectedId, setSelectedId] = useState("github");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [revealed, setRevealed] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [showNewItem, setShowNewItem] = useState(false);
  const [newName, setNewName] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const selected = items.find((item) => item.id === selectedId) ?? items[0];
  const filteredItems = useMemo(
    () =>
      items.filter((item) => {
        const categoryTypes: Record<string, VaultItem["type"] | undefined> = {
          Logins: "Login",
          Cards: "Card",
          Identities: "Identity",
          "Secure Notes": "Secure Note"
        };
        const matchesCategory = category === "All" || item.type === categoryTypes[category];
        const haystack = `${item.name} ${item.username} ${item.website ?? ""} ${item.tags.join(" ")}`.toLowerCase();
        return matchesCategory && haystack.includes(query.toLowerCase());
      }),
    [category, items, query]
  );

  function toggleFavorite(id: string) {
    setItems((current) => current.map((item) => item.id === id ? { ...item, favorite: !item.favorite } : item));
  }

  function createItem(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const id = crypto.randomUUID();
    const item: VaultItem = {
      id,
      name: newName.trim(),
      username: newUsername.trim(),
      password: newPassword,
      type: "Login",
      icon: newName.trim().slice(0, 1).toUpperCase() || "?",
      modified: "just now",
      favorite: false,
      website: "",
      folder: "Personal",
      tags: []
    };
    setItems((current) => [item, ...current]);
    setSelectedId(id);
    setShowNewItem(false);
    setNewName("");
    setNewUsername("");
    setNewPassword("");
  }

  function deleteSelected() {
    if (!selected) return;
    setItems((current) => current.filter((item) => item.id !== selected.id));
    setSelectedId(items.find((item) => item.id !== selected.id)?.id ?? "");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><img className="brand-logo" src="/logo.png" alt="EGYXOS" /><div><strong>EGYXOS</strong><span>PASSWORD MANAGER</span></div></div>
        <label className="global-search"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search vault..." /><kbd>Ctrl + K</kbd></label>
        <div className="top-actions"><span className="sync"><RefreshCw size={16} /> Synced just now</span><Bell size={18} /><span className="divider" /><span className="profile"><span className="avatar"><UserRound size={17} /></span>John Doe <ChevronDown size={15} /></span><button className="outline-button" onClick={() => setIsLocked(true)}><LockKeyhole size={16} /> Lock Vault</button></div>
      </header>
      <div className="workspace">
        <aside className="sidebar">
          <nav>
            <a className="nav-item active"><KeyRound size={18} /> Home</a>
            <div className="nav-section"><a className="nav-item"><ShieldCheck size={18} /> Vault <ChevronDown size={15} className="push-right" /></a>
              <a className="nav-item sub active"><UsersRound size={17} /> All Items</a><a className="nav-item sub"><KeyRound size={17} /> Logins</a><a className="nav-item sub"><CreditCardIcon /> Cards</a><a className="nav-item sub"><UserRound size={17} /> Identities</a><a className="nav-item sub"><LockKeyhole size={17} /> Secure Notes</a>
            </div>
            <a className="nav-item"><Star size={18} /> Favorites</a><a className="nav-item"><WandSparkles size={18} /> Generator</a><a className="nav-item"><ShieldCheck size={18} /> Security Center</a><a className="nav-item"><SlidersHorizontal size={18} /> Settings</a>
          </nav>
          <div className="sidebar-footer"><div className="sync-card"><RefreshCw size={17} /><div><strong>Synced</strong><span>Just now</span></div></div><button className="lock-link" onClick={() => setIsLocked(true)}><LockKeyhole size={17} /> Lock Vault</button></div>
        </aside>
        <section className="content-grid">
          <section className="vault-panel panel">
            <div className="panel-heading"><h1>Vault</h1><div className="heading-actions"><button className="icon-button"><Filter size={17} /></button><button className="icon-button"><SlidersHorizontal size={17} /></button><button className="primary-button" onClick={() => setShowNewItem(true)}><Plus size={17} /> New Item</button></div></div>
            <div className="tabs">{categories.map((name) => <button key={name} className={category === name ? "tab active" : "tab"} onClick={() => setCategory(name)}>{name}</button>)}</div>
            <label className="local-search"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search vault items..." /></label>
            <div className="list-header"><span>Name <ChevronDown size={14} /></span><span>Last Modified <ChevronDown size={14} /></span></div>
            <div className="item-list">{filteredItems.map((item) => <button key={item.id} className={item.id === selectedId ? "vault-item selected" : "vault-item"} onClick={() => setSelectedId(item.id)}><span className="item-icon">{item.icon}</span><span className="item-copy"><strong>{item.name}</strong><small>{item.username}</small></span><span className="item-modified">{item.modified}</span><span className="item-controls" onClick={(event) => event.stopPropagation()}><Star size={17} fill={item.favorite ? "currentColor" : "none"} onClick={() => toggleFavorite(item.id)} className={item.favorite ? "favorite" : ""} /><MoreVertical size={17} /></span></button>)}</div>
          </section>
          {selected && <section className="detail-panel panel"><div className="detail-top"><span>← &nbsp; Back to Vault</span><div><button className="outline-button"><Pencil size={16} /> Edit</button><button className="icon-button"><MoreVertical size={17} /></button></div></div><div className="detail-title"><div className="large-icon">{selected.icon}</div><div><small>{selected.type.toUpperCase()}</small><h2>{selected.name} <Star size={19} fill="currentColor" /></h2></div></div><div className="detail-card"><DetailRow label="Username" value={selected.username} action={<Copy size={16} />} /><DetailRow label="Password" value={revealed ? selected.password : "••••••••••••••"} action={<button className="reveal" onClick={() => setRevealed(!revealed)}>{revealed ? "Hide" : "Reveal"}</button>} /><DetailRow label="Website" value={selected.website ?? "—"} action={<ExternalLink size={16} />} /><DetailRow label="Folder" value={selected.folder ?? "—"} action={<ChevronRight size={17} />} /><DetailRow label="Tags" value={selected.tags.join("   ") || "—"} action={<ChevronRight size={17} />} /><DetailRow label="Notes" value="Development account" action={<ChevronRight size={17} />} /><div className="favorite-row"><Star size={18} fill="currentColor" /> Favorite <button className="toggle on" onClick={() => toggleFavorite(selected.id)}><span /></button></div></div><div className="detail-actions"><button><Copy size={17} /> Copy Username</button><button><Copy size={17} /> Copy Password</button><button><ExternalLink size={17} /> Open Website</button><button><Pencil size={17} /> Edit</button><button><Copy size={17} /> Duplicate</button><button onClick={deleteSelected}><Trash2 size={17} /> Delete</button></div></section>}
        </section>
      </div>
      {isLocked && <div className="lock-overlay"><div className="lock-dialog"><LockKeyhole size={28} /><h2>Vault locked</h2><p>Your encrypted vault is cleared from the active session.</p><button className="primary-button" onClick={() => setIsLocked(false)}>Unlock vault</button></div></div>}
      {showNewItem && <div className="lock-overlay"><form className="item-dialog" onSubmit={createItem}><div className="dialog-heading"><div><p className="eyebrow">Vault item</p><h2>New login</h2></div><button type="button" className="icon-button" onClick={() => setShowNewItem(false)}>×</button></div><label>Name<input required value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="GitHub" /></label><label>Username<input required value={newUsername} onChange={(event) => setNewUsername(event.target.value)} placeholder="you@example.com" /></label><label>Password<input required type="password" minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="Use the generator for a strong password" /></label><div className="dialog-actions"><button type="button" className="outline-button" onClick={() => setShowNewItem(false)}>Cancel</button><button className="primary-button">Create item</button></div></form></div>}
    </main>
  );
}

function DetailRow({ label, value, action }: { label: string; value: string; action: ReactNode }) {
  return <div className="detail-row"><div><small>{label}</small><span>{value}</span></div><button className="row-action">{action}</button></div>;
}

function CreditCardIcon() {
  return <span className="card-icon" aria-hidden="true">▭</span>;
}
