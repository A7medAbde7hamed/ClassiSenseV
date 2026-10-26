import {createSign} from 'node:crypto';
let cachedToken;
const timeout = () => AbortSignal.timeout(8000);
export function decodeValue(v) {
  if (!v) return null;
  if ('nullValue' in v) return null;
  if ('integerValue' in v) return Number(v.integerValue);
  if ('doubleValue' in v) return Number(v.doubleValue);
  if ('booleanValue' in v) return v.booleanValue;
  if ('timestampValue' in v) return v.timestampValue;
  if ('stringValue' in v) return v.stringValue;
  if ('mapValue' in v) return decodeFields(v.mapValue.fields);
  if ('arrayValue' in v) return (v.arrayValue.values || []).map(decodeValue);
  return null;
}
export function decodeFields(fields = {}) {
  return Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,decodeValue(v)]));
}
export async function getAccessToken(account, request = fetch) {
  if (cachedToken?.email === account.client_email && cachedToken.until > Date.now()) return cachedToken.token;
  const now = Math.floor(Date.now()/1000);
  const b64 = value => Buffer.from(JSON.stringify(value)).toString('base64url');
  const claim = `${b64({alg:'RS256',typ:'JWT'})}.${b64({iss:account.client_email,scope:'https://www.googleapis.com/auth/datastore',aud:'https://oauth2.googleapis.com/token',iat:now,exp:now+3600})}`;
  const sign = createSign('RSA-SHA256');sign.update(claim);sign.end();
  const assertion = `${claim}.${sign.sign(account.private_key,'base64url')}`;
  const response = await request('https://oauth2.googleapis.com/token',{method:'POST',body:new URLSearchParams({grant_type:'urn:ietf:params:oauth:grant-type:jwt-bearer',assertion}),signal:timeout()});
  if (!response.ok) throw new Error('Firebase authentication failed');
  const result = await response.json();
  cachedToken = {token:result.access_token,until:Date.now()+Math.max(0,Number(result.expires_in)-120)*1000,email:account.client_email};
  return result.access_token;
}
export async function readWorkspace(account, days, request = fetch, tokenProvider = getAccessToken) {
  if (!/^[a-z0-9-]+$/.test(account.project_id)) throw new Error('Invalid project ID');
  const token = await tokenProvider(account, request);
  const root = `https://firestore.googleapis.com/v1/projects/${account.project_id}/databases/(default)/documents`;
  const headers = {Authorization:`Bearer ${token}`,'Content-Type':'application/json'};
  const cutoff = new Date(Date.now()-days*86400000).toISOString();
  async function query(collection) {
    const response = await request(`${root}:runQuery`,{method:'POST',headers,signal:timeout(),body:JSON.stringify({structuredQuery:{from:[{collectionId:collection}],where:{fieldFilter:{field:{fieldPath:'sampled_at'},op:'GREATER_THAN_OR_EQUAL',value:{doubleValue:Date.parse(cutoff)/1000}}},orderBy:[{field:{fieldPath:'sampled_at'},direction:'DESCENDING'}],limit:1000}})});
    if (!response.ok) throw new Error('Firebase history unavailable');
    return (await response.json()).filter(r=>r.document).map(r=>({id:r.document.name.split('/').at(-1),...decodeFields(r.document.fields)}));
  }
  const [status, history, alerts] = await Promise.all([
    request(`${root}/classroom/live_status`,{headers,signal:timeout()}),query('monitoring_logs'),query('alerts')
  ]);
  if (!status.ok && status.status!==404) throw new Error('Firebase status unavailable');
  const live = status.status===404 ? null : decodeFields((await status.json()).fields);
  return {live,history:history.reverse(),alerts,truncated:history.length===1000 || alerts.length===1000};
}
