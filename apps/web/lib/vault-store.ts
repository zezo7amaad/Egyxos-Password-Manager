import type { EncryptedEnvelope } from "@egyxos/crypto";

const DATABASE_NAME = "egyxos-vault";
const STORE_NAME = "encrypted-items";
const DATABASE_VERSION = 1;

type StoredItem = {
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
    };
    request.onsuccess = () => resolve(request.result);
  });
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
