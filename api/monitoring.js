import {authorized} from '../lib/auth.js';
import {readWorkspace} from '../lib/firebase.js';
export default async function handler(req,res) {
  res.setHeader('Cache-Control','no-store');
  if (req.method!=='GET') return res.status(405).json({error:'Method not allowed'});
  const raw=process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (!raw || !process.env.DASHBOARD_PASSWORD) return res.status(200).json({mode:'setup',live:null,history:[],alerts:[],message:'Connect a test Firebase project to enable live readings.'});
  if (!authorized(req,process.env.DASHBOARD_PASSWORD)) return res.status(401).json({mode:'locked',error:'Workspace password required'});
  const days=Number(new URL(req.url,'https://local').searchParams.get('days') || 1);
  if (![1,7,30].includes(days)) return res.status(400).json({error:'Choose 1, 7 or 30 days'});
  try {
    const data=await readWorkspace(JSON.parse(raw),days);
    const age=data.live?.sampled_at ? Math.max(0,Date.now()/1000-data.live.sampled_at) : null;
    return res.status(200).json({mode:'live',...data,server_time:Date.now()/1000,age_seconds:age,connection:age===null?'disconnected':age>15?'stale':'healthy'});
  }catch(error){
    console.error('monitoring_read_failed',error.name);
    return res.status(503).json({mode:'error',error:'Unable to read classroom data. Please retry.'});
  }
}
