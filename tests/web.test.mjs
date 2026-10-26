import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {authorized,sessionValue,sameOrigin} from '../lib/auth.js';
import {decodeFields,readWorkspace} from '../lib/firebase.js';
import monitoring from '../api/monitoring.js';
import session from '../api/session.js';
function response(){return {statusCode:200,headers:{},setHeader(k,v){this.headers[k]=v;},status(code){this.statusCode=code;return this;},json(data){this.body=data;return this;}};}
test('session rejects tampering, expiry, future timestamps, missing configuration',()=>{
 const password='test-workspace-secret';const now=100000000;
 const req={headers:{cookie:`cs_session=${sessionValue(password,now)}`}};
 assert.equal(authorized(req,password,now),true);
 assert.equal(authorized(req,'wrong',now),false);
 assert.equal(authorized(req,password,now+9*3600000),false);
 assert.equal(authorized(req,password,now-1),false);
 assert.equal(authorized(req,undefined,now),false);
});
test('session requires same origin',()=>{
 assert.equal(sameOrigin({headers:{origin:'https://evil.test',host:'classisense.test'}}),false);
 assert.equal(sameOrigin({headers:{origin:'https://classisense.test',host:'classisense.test'}}),true);
});
test('Firestore values retain null, zero and false correctly',()=>{
 assert.deepEqual(decodeFields({a:{nullValue:null},b:{integerValue:'0'},c:{booleanValue:false}}),{a:null,b:0,c:false});
});
test('unconfigured API never fabricates live readings',async()=>{
 const old=process.env.FIREBASE_SERVICE_ACCOUNT_JSON;delete process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
 try{const res=response();await monitoring({method:'GET'},res);assert.equal(res.body.mode,'setup');assert.equal(res.body.live,null);assert.deepEqual(res.body.history,[]);}finally{if(old)process.env.FIREBASE_SERVICE_ACCOUNT_JSON=old;}
});
test('configured live API denies requests without a session',async()=>{
 const oldAccount=process.env.FIREBASE_SERVICE_ACCOUNT_JSON,oldPassword=process.env.DASHBOARD_PASSWORD;
 process.env.FIREBASE_SERVICE_ACCOUNT_JSON='{}';process.env.DASHBOARD_PASSWORD='test';
 try{const res=response();await monitoring({method:'GET',headers:{}},res);assert.equal(res.statusCode,401);assert.equal(res.body.mode,'locked');}finally{if(oldAccount)process.env.FIREBASE_SERVICE_ACCOUNT_JSON=oldAccount;else delete process.env.FIREBASE_SERVICE_ACCOUNT_JSON;if(oldPassword)process.env.DASHBOARD_PASSWORD=oldPassword;else delete process.env.DASHBOARD_PASSWORD;}
});
test('Firestore query returns live data and chronological history',async()=>{
 const calls=[];
 const request=async(url,options)=>{
  calls.push([url,options]);
  if(url.endsWith('live_status'))return {ok:true,status:200,json:async()=>({fields:{people_count:{integerValue:'12'},sampled_at:{doubleValue:123}}})};
  return {ok:true,json:async()=>[{document:{name:'docs/id',fields:{people_count:{integerValue:'12'},sampled_at:{doubleValue:123}}}}]};
 };
 const result=await readWorkspace({project_id:'test-project'},1,request,async()=> 'test-token');
 assert.equal(result.live.people_count,12);assert.equal(result.history[0].people_count,12);assert.equal(calls.length,3);
 const query=JSON.parse(calls.find(([url])=>url.endsWith('runQuery'))[1].body);
 assert.equal(query.structuredQuery.limit,1000);
});
test('Firestore errors propagate rather than masquerade as empty history',async()=>{
 await assert.rejects(()=>readWorkspace({project_id:'test-project'},1,async()=>({ok:false,status:503}),async()=> 'x'));
});
test('service worker never caches API or session requests',async()=>{
 const sw=await readFile('public/sw.js','utf8');assert.match(sw,/pathname.startsWith\('\/api\/'\)/);assert.match(sw,/request.method!=='GET'/);
});
test('password sign-in sets HttpOnly secure session, rejects CSRF',async()=>{
 const old=process.env.DASHBOARD_PASSWORD;process.env.DASHBOARD_PASSWORD='test-password';
 try{
  const res=response();await session({method:'POST',headers:{origin:'https://lab.test',host:'lab.test'},body:{password:'test-password'}},res);
  assert.equal(res.statusCode,200);assert.match(res.headers['Set-Cookie'],/HttpOnly; Secure; SameSite=Strict/);
  const blocked=response();await session({method:'POST',headers:{origin:'https://evil.test',host:'lab.test'},body:{password:'test-password'}},blocked);assert.equal(blocked.statusCode,403);
 }finally{if(old)process.env.DASHBOARD_PASSWORD=old;else delete process.env.DASHBOARD_PASSWORD;}
});
test('offline navigation falls back to cached shell while API bypasses cache',async()=>{
 const vm=await import('node:vm');const handlers={};let cachedPath;
 const context={URL,fetch:async()=>{throw new Error('offline');},caches:{match:async path=>{cachedPath=path;return {offlineShell:true};}},self:{location:{origin:'https://lab.test'},addEventListener:(name,fn)=>handlers[name]=fn}};
 vm.runInNewContext(await readFile('public/sw.js','utf8'),context);
 let response;
 handlers.fetch({request:{url:'https://lab.test/history',method:'GET',mode:'navigate'},respondWith(value){response=value;}});
 assert.deepEqual(await response,{offlineShell:true});assert.equal(cachedPath,'/index.html');
 let intercepted=false;handlers.fetch({request:{url:'https://lab.test/api/monitoring',method:'GET'},respondWith(){intercepted=true;}});assert.equal(intercepted,false);
});
