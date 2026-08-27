function bufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

function base64urlToBuffer(value: string): ArrayBuffer {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((3 * value.length) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json?.error ?? "request_failed");
  return json as T;
}

export async function registerWithInvitation(invitationToken: string, displayName: string) {
  const options = await post<{ challenge_id: string; publicKey: string }>(
    "/auth/register/options",
    { invitation_token: invitationToken }
  );
  const opts = JSON.parse(options.publicKey);
  const credential = (await navigator.credentials.create({
    publicKey: {
      ...opts,
      challenge: base64urlToBuffer(opts.challenge),
      user: { ...opts.user, id: base64urlToBuffer(opts.user.id) },
      excludeCredentials: (opts.excludeCredentials ?? []).map((c: any) => ({
        ...c,
        id: base64urlToBuffer(c.id),
      })),
    },
  })) as PublicKeyCredential;

  return post<{ tokens: any; recovery_codes: string[] }>("/auth/register", {
    invitation_token: invitationToken,
    challenge_id: options.challenge_id,
    credential: {
      id: credential.id,
      rawId: bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: bufferToBase64url(
          (credential.response as AuthenticatorAttestationResponse).clientDataJSON
        ),
        attestationObject: bufferToBase64url(
          (credential.response as AuthenticatorAttestationResponse).attestationObject
        ),
      },
    },
    display_name: displayName,
  });
}

export async function loginWithPasskey(email: string) {
  const options = await post<{ challenge_id: string; publicKey: string }>(
    "/auth/login/options",
    { email }
  );
  const opts = JSON.parse(options.publicKey);
  const assertion = (await navigator.credentials.get({
    publicKey: {
      ...opts,
      challenge: base64urlToBuffer(opts.challenge),
      allowCredentials: (opts.allowCredentials ?? []).map((c: any) => ({
        ...c,
        id: base64urlToBuffer(c.id),
      })),
    },
  })) as PublicKeyCredential;

  return post<{ access_token: string; refresh_token: string }>("/auth/login", {
    email,
    challenge_id: options.challenge_id,
    credential: {
      id: assertion.id,
      rawId: bufferToBase64url(assertion.rawId),
      type: assertion.type,
      response: {
        clientDataJSON: bufferToBase64url(
          (assertion.response as AuthenticatorAssertionResponse).clientDataJSON
        ),
        authenticatorData: bufferToBase64url(
          (assertion.response as AuthenticatorAssertionResponse).authenticatorData
        ),
        signature: bufferToBase64url((assertion.response as AuthenticatorAssertionResponse).signature),
        userHandle: bufferToBase64url(
          (assertion.response as AuthenticatorAssertionResponse).userHandle as ArrayBuffer
        ),
      },
    },
  });
}
