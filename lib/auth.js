import {createHmac,timingSafeEqual} from 'node:crypto';
export function equal(a,b) {
  const ah=createHmac('sha256','classisense-compare').update(String(a)).digest();
  const bh=createHmac('sha256','classisense-compare').update(String(b)).digest();
  return timingSafeEqual(ah,bh);
}
export function sessionValue(password, timestamp=Date.now()) {
  const signature=createHmac('sha256',password).update(String(timestamp)).digest('base64url');
  return `${timestamp}.${signature}`;
}
export function authorized(req, password, now=Date.now()) {
  if (!password) return false;
  const value=(req.headers.cookie || '').split(';').map(s=>s.trim()).find(s=>s.startsWith('cs_session='))?.slice(11);
  if (!value || !/^\d+\.[A-Za-z0-9_-]+$/.test(value)) return false;
  const timestamp=Number(value.split('.')[0]);
  return timestamp <= now && now-timestamp<8*3600000 && equal(value,sessionValue(password,timestamp));
}
export function sameOrigin(req) {
  if (!req.headers.origin) return false;
  try { return new URL(req.headers.origin).host === req.headers.host; } catch {return false;}
}
