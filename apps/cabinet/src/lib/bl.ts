import { env } from "./env";
import { getSession, type Session } from "./session";

/** Error from the BL API carrying its HTTP status (and problem+json detail). */
export class BlError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Call the BL with the user's access token; retries once with a refreshed token on 401. */
export async function blFetch(path: string, init: RequestInit = {}, session?: Session): Promise<Response> {
  let s = session ?? (await getSession());
  if (!s) throw new BlError(401, "Not signed in");
  const call = (tok: string) => {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${tok}`);
    return fetch(`${env.blUrl}${path}`, { ...init, headers, cache: "no-store" });
  };
  let res: Response;
  try {
    res = await call(s.accessToken);
    if (res.status === 401) {
      s = await getSession({ forceRefresh: true });
      if (s) res = await call(s.accessToken);
    }
  } catch (e) {
    if (e instanceof BlError) throw e;
    throw new BlError(503, "Сервис BL недоступен");
  }
  return res;
}

export async function blJson<T>(path: string, init?: RequestInit, session?: Session): Promise<T> {
  const res = await blFetch(path, init, session);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.title || detail;
    } catch {
      /* not json */
    }
    throw new BlError(res.status, detail);
  }
  return (await res.json()) as T;
}
