import type { EncryptedEnvelope } from "@egyxos/crypto";

const DATABASE_NAME = "egyxos-vault";
const STORE_NAME = "encrypted-items";
const META_STORE_NAME = "metadata";
const DATABASE_VERSION = 1;

export type StoredItem = {
  id: string;
  envelope: EncryptedEnvelope;
  updatedAt: number;
};

let unlockedKey: CryptoKey | null = null;

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onerror = () => reject(request.error ?? new Error("Unable to open encrypted vault storage"));
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
      request.result.createObjectStore(META_STORE_NAME);
    };
    request.onsuccess = () => resolve(request.result);
  });
}

export async function getVaultSalt(): Promise<Uint8Array> {
  const database = await openDatabase();
  const salt = await new Promise<ArrayBuffer | undefined>((resolve, reject) => {
    const request = database.transaction(META_STORE_NAME, "readonly").objectStore(META_STORE_NAME).get("salt");
    request.onerror = () => reject(request.error ?? new Error("Unable to read vault metadata"));
    request.onsuccess = () => resolve(request.result as ArrayBuffer | undefined);
  });
  if (salt) {
    database.close();
    return new Uint8Array(salt);
  }
  const generated = crypto.getRandomValues(new Uint8Array(16));
  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction(META_STORE_NAME, "readwrite");
    transaction.objectStore(META_STORE_NAME).put(generated.buffer, "salt");
    transaction.onerror = () => reject(transaction.error ?? new Error("Unable to persist vault metadata"));
    transaction.oncomplete = () => resolve();
  });
  database.close();
  return generated;
}

export function setUnlockedKey(key: CryptoKey): void {
  unlockedKey = key;
}

export function clearUnlockedKey(): void {
  unlockedKey = null;
}

export function hasUnlockedVault(): boolean {
  return unlockedKey !== null;
}

export async function saveEncryptedItem(item: StoredItem): Promise<void> {
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).put(item);
    transaction.onerror = () => reject(transaction.error ?? new Error("Unable to persist encrypted item"));
    transaction.oncomplete = () => resolve();
  });
  database.close();
}

export async function loadEncryptedItems(): Promise<StoredItem[]> {
  const database = await openDatabase();
  const items = await new Promise<StoredItem[]>((resolve, reject) => {
    const request = database.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).getAll();
    request.onerror = () => reject(request.error ?? new Error("Unable to read encrypted vault"));
    request.onsuccess = () => resolve(request.result as StoredItem[]);
  });
  database.close();
  return items;
}

export function getUnlockedKey(): CryptoKey {
  if (!unlockedKey) {
    throw new Error("Vault is locked");
  }
  return unlockedKey;
}
