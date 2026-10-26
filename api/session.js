import {equal,sessionValue,sameOrigin} from '../lib/auth.js';
export default async function handler(req,res) {
  res.setHeader('Cache-Control','no-store');
  if (!['POST','DELETE'].includes(req.method)) return res.status(405).json({error:'Method not allowed'});
  if (!sameOrigin(req)) return res.status(403).json({error:'Invalid origin'});
  if (req.method==='DELETE') {
    res.setHeader('Set-Cookie','cs_session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0');
    return res.status(200).json({ok:true});
  }
  const password=process.env.DASHBOARD_PASSWORD;
  let body=req.body;
  if (typeof body==='string') {try {body=JSON.parse(body);}catch {return res.status(400).json({error:'Invalid JSON'});}}
  if (!password) return res.status(503).json({error:'Live workspace is not configured'});
  if (typeof body?.password!=='string' || body.password.length>256 || !equal(body.password,password)) {
    // Do not reveal secrets or which part of the configuration is present.
    return res.status(401).json({error:'Incorrect workspace password'});
  }
  res.setHeader('Set-Cookie',`cs_session=${sessionValue(password)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=28800`);
  return res.status(200).json({ok:true});
}
