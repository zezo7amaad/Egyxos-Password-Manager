export type EncryptedEnvelope = {
  version: 1;
  algorithm: "AES-256-GCM";
  keyVersion: number;
  nonce: string;
  ciphertext: string;
  associatedData?: string;
};

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function encode(value: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(value)));
}

function decode(value: string): Uint8Array {
  return Uint8Array.from(atob(value), (character) => character.charCodeAt(0));
}

export async function deriveVaultKey(masterKeyMaterial: Uint8Array, salt: Uint8Array): Promise<CryptoKey> {
  const baseKey = await crypto.subtle.importKey("raw", masterKeyMaterial, "HKDF", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256", salt, info: encoder.encode("egyxos/vault-key/v1") },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function encryptPayload(
  key: CryptoKey,
  payload: unknown,
  associatedData?: string
): Promise<EncryptedEnvelope> {
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const aad = associatedData ? encoder.encode(associatedData) : undefined;
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: aad },
    key,
    encoder.encode(JSON.stringify(payload))
  );
  return {
    version: 1,
    algorithm: "AES-256-GCM",
    keyVersion: 1,
    nonce: encode(nonce),
    ciphertext: encode(ciphertext),
    ...(associatedData ? { associatedData } : {})
  };
}

export async function decryptPayload<T>(key: CryptoKey, envelope: EncryptedEnvelope): Promise<T> {
  if (envelope.version !== 1 || envelope.algorithm !== "AES-256-GCM") {
    throw new Error("Unsupported encrypted payload version");
  }
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: decode(envelope.nonce),
      additionalData: envelope.associatedData ? encoder.encode(envelope.associatedData) : undefined
    },
    key,
    decode(envelope.ciphertext)
  );
  return JSON.parse(decoder.decode(plaintext)) as T;
}
