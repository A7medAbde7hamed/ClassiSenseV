const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const labels={healthy:'Healthy',danger:'Danger',disconnected:'Not connected',stale:'Stale reading'};
const titles={overview:['Overview','A little more <em>in sync.</em>','Your classroom, understood at a glance.'],history:['History & insights','The bigger <em>picture.</em>','Small readings. A clearer understanding over time.'],alerts:['Alert journal','Nothing left <em>unnoticed.</em>','A record of the moments that need your attention.'],devices:['Devices & sensors','Behind the <em>scenes.</em>','The hardware keeping a quiet eye on your classroom.'],settings:['Connection settings','Make the <em>connection.</em>','A dedicated workspace for your classroom signals.']};
let workspace={mode:'setup',live:null,history:[],alerts:[]};
let demo=new URLSearchParams(location.search).get('demo')==='1';
let days=1, pageSize=30, currentView='overview', requestId=0, busy=false, installEvent;
let sample;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>`<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const stateHtml=state=>`<span class="state ${esc(labels[state]?state:'disconnected')}">${esc(labels[state] || labels.disconnected)}</span>`;
const num=value=>Number.isFinite(value)?value:null;
const timeOf=timestamp=>new Date(timestamp*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
const dateTime=timestamp=>new Date(timestamp*1000).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,4000);}
function info(title,text){$('#dialog-title').textContent=title;$('#dialog-text').textContent=text;$('#info-dialog').showModal();}
function showView(view){if(!titles[view])return;currentView=view;$$('.view').forEach(el=>el.hidden=el.id!==`${view}-view`);$$('.nav').forEach(el=>{el.classList.toggle('active',el.dataset.view===view);if(el.dataset.view===view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});$('#breadcrumb-current').textContent=titles[view][0];$('#page-title').innerHTML=titles[view][1];$('#page-subtitle').textContent=titles[view][2];$('#sidebar').classList.remove('open');$('#menu').setAttribute('aria-expanded','false');}
function buildDemo(){
 const now=Math.floor(Date.now()/1000);
 const history=Array.from({length:96},(_,i)=>{
  const count=Math.max(0,Math.round(18+12*Math.sin(i/11)+5*Math.cos(i/4)));
  return {sampled_at:now-(95-i)*900,people_count:count,temperature_c:Math.round((24.4+1.3*Math.sin(i/14))*10)/10,gas_detected:false,gas_state:'healthy',temperature_state:'healthy',controller_state:'healthy',source_state:'healthy',lights_on:count>0,led_on_seconds:12840,fps:18.6,inference_ms:49.2};
 });
 return {mode:'demo',connection:'healthy',live:{...history.at(-1),people_count:28,temperature_c:24.8},history,alerts:[{id:'demo-temp',sampled_at:now-9300,alert_type:'HIGH_TEMPERATURE',severity:'CRITICAL',temperature_c:46.2},{id:'demo-gas',sampled_at:now-18000,alert_type:'GAS_LEAK',severity:'CRITICAL',gas_detected:true}],truncated:false};
}
function data(){return demo?(sample ||= buildDemo()):workspace;}
function ageOf(live){return live?.sampled_at?Math.max(0,Date.now()/1000-live.sampled_at):null;}
function effective(){
 const d=data(),live=d.live;
 const age=ageOf(live);
 const expired=!demo && (age===null || age>15 || !navigator.onLine || workspace.mode==='error');
 const globalState=!live?'disconnected':expired?'stale':live.stopped?'disconnected':'healthy';
 const valid=globalState==='healthy';
 return {d,live,age,globalState,valid,gasState:valid?(live.gas_state || 'disconnected'):globalState,tempState:valid?(live.temperature_state || 'disconnected'):globalState,controllerState:valid?(live.controller_state || 'disconnected'):globalState};
}
function render(){
 const {d,live,age,globalState,valid,gasState,tempState,controllerState}=effective();
 const count=valid&&live.source_state==='healthy'?num(live.people_count):null;
 const temp=valid&&['healthy','danger'].includes(tempState)?num(live.temperature_c):null;
 $('#people').textContent=count??'—';
 $('#people-note').textContent=count===null?'No fresh camera data':count===0?'The room is empty':'People currently detected';
 $('#temperature').textContent=temp===null?'—':temp.toFixed(1);
 $('#temperature-state').className=`state ${tempState}`;$('#temperature-state').textContent=labels[tempState]||labels.disconnected;
 $('#gas').textContent=gasState==='danger'?'Detected':gasState==='healthy'?'Clear':'Unknown';
 $('#gas-state').className=`state ${gasState}`;$('#gas-state').textContent=labels[gasState]||labels.disconnected;
 const actuatorFresh=valid && controllerState==='healthy';
 $('#lights').textContent=actuatorFresh&&typeof live.lights_on==='boolean'?(live.lights_on?'On':'Off'):'—';
 $('#lights-unit').textContent=actuatorFresh?'lighting':'status';
 $('#lights-note').textContent=actuatorFresh&&num(live.led_on_seconds)!==null?`${(live.led_on_seconds/3600).toFixed(1)}h on this session`:'No fresh actuator reading';
 $('#room-status').innerHTML=`<span class="dot"></span>${demo?'Demo classroom':valid?'Live classroom':globalState==='stale'?'Readings are stale':'Awaiting readings'}`;
 $('#room-note').textContent=count===null?'Waiting for the classroom':count>0?'A room full of possibility':'Taking a quiet moment';
 $('#desks').innerHTML=Array.from({length:16},(_,i)=>`<span class="desk ${count!==null&&i<Math.ceil(Math.min(count,40)/40*16)?'filled':''}"></span>`).join('');
 let connection=demo?'Demo workspace':!navigator.onLine?'Offline':workspace.mode==='locked'?'Workspace locked':workspace.mode==='error'?'Connection error':workspace.mode==='setup'?'Setup required':valid?'Live connection':globalState==='stale'?'Readings stale':'No readings';
 $('#connection-label').textContent=connection;
 $('#connection-button').style.color=demo?'#8971ad':valid?'#4b8979':'#b58a4e';
 $('#mode-tag').textContent=demo?'DEMO DATA':workspace.mode==='live'?'LIVE WORKSPACE':'CONNECTION';
 $('#mode-text').textContent=demo?'An illustrative day in the lab. These are sample readings.':workspace.mode==='setup'?'Live data is not connected. Configure a test Firebase workspace.':workspace.mode==='locked'?'Sign in to view live classroom readings.':workspace.mode==='error'?'Could not refresh. Previous readings may be out of date.':valid?'Connected to the classroom. Readings refresh every 10 seconds.':'Waiting for fresh readings from the tracking computer.';
 $('#mode-action').textContent=demo?'Connect live ↗':workspace.mode==='setup'?'Explore demo ↗':'Connection settings ↗';
 const signals=[['chip','Arduino controller','USB Serial · Protocol v1',controllerState],['grid','Vision pipeline',valid&&num(live?.fps)!==null?`${live.fps.toFixed(1)} FPS · YOLO tracking`:'Local video processor',valid?(live.source_state || 'disconnected'):globalState],['air','Gas sensor','MQ-5 · Digital threshold',gasState],['refresh','Cloud sync',demo?'Illustrative connection':age===null?'No sync received':`Sample age: ${Math.floor(age)}s`,demo?'healthy':workspace.mode==='live'?globalState:'disconnected']];
 $('#signal-list').innerHTML=signals.map(([sym,name,desc,state])=>`<div class="signal-row"><span class="signal-icon">${icon(sym)}</span><span class="signal-name">${name}<small>${esc(desc)}</small></span>${stateHtml(state)}</div>`).join('');
 $('#sync-note').textContent=demo?'Sample workspace · not connected to hardware':valid?'All available signals are up to date':globalState==='stale'?'Readings are old. Check the local tracker.':'Waiting for a first sync';
 $('#last-update').textContent=demo?'DEMO · No hardware connected':live?.sampled_at?`Last sample · ${dateTime(live.sampled_at)}`:'No live readings yet';
 $('#alert-count').textContent=d.alerts.length;
 $('#settings-status').textContent=demo?'You are exploring sample data. Live readings require a configured test workspace.':workspace.mode==='locked'?'The workspace is configured. Enter its password to connect.':workspace.mode==='setup'?'No live Firebase connection is configured on this deployment.':'Live connection state: '+connection.toLowerCase()+'.';
 $('#logout').hidden=demo||workspace.mode!=='live';
 renderChart(d.history);renderHistory(d.history);renderAlerts(d.alerts);renderDevices(effective());
 $('#recent-activity').innerHTML=d.alerts.length?d.alerts.slice(0,2).map(activity).join(''):'<div class="empty-state">No safety alerts in this period.</div>';
}
function activity(row){const gas=row.alert_type==='GAS_LEAK';const when=num(row.sampled_at);return `<div class="activity-row"><span class="activity-mark danger">${icon(gas?'air':'temp')}</span><div class="activity-content">${gas?'Gas threshold exceeded':'High temperature recorded'}<small>${gas?'Gas alert reported by the local tracker':`Temperature: ${esc(row.temperature_c??'—')} °C`}${demo?' · Sample event':''}</small></div><span class="activity-badge">CRITICAL</span><span class="activity-time">${when?dateTime(when):'Time unavailable'}</span></div>`;}
function renderChart(history){
 const rows=history.filter(r=>num(r.people_count)!==null&&num(r.sampled_at)!==null);
 const svg=$('#occupancy-chart');$('#chart-empty').hidden=rows.length>0;
 $('#chart-average').textContent=rows.length?(rows.reduce((a,r)=>a+r.people_count,0)/rows.length).toFixed(1):'—';
 $('#history-total').textContent=`${rows.length} readings`;
 $('#history-caption').textContent=data().truncated?'Showing most recent 1,000 records':'Recorded every 3 minutes';
 $('#chart-subtitle').textContent=demo?'An illustrative 24-hour occupancy pattern':`Occupancy over the last ${days===1?'24 hours':days+' days'}`;
 const max=Math.max(10,...rows.map(r=>r.people_count));const ceiling=Math.ceil(max/10)*10;
 let markup='<defs><linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#aaa0de" stop-opacity=".22"/><stop offset="1" stop-color="#aaa0de" stop-opacity="0"/></linearGradient></defs>';
 for(let i=0;i<4;i++){const y=15+i*50;markup+=`<path class="chart-grid" d="M30 ${y}H745"/><text class="chart-label" x="0" y="${y+4}">${Math.round(ceiling*(1-i/3))}</text>`;}
 if(rows.length){
  const start=rows[0].sampled_at,end=rows.at(-1).sampled_at;
  const points=rows.map((r,i)=>[rows.length===1?390:35+(r.sampled_at-start)/Math.max(1,end-start)*705,165-r.people_count/ceiling*150]);
  const path=points.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
  markup+=`<path class="chart-area" d="${path} L${points.at(-1)[0]} 165 L${points[0][0]} 165 Z"/><path class="chart-line" d="${path}"/>`;
  const stride=Math.max(1,Math.floor(rows.length/24));
  points.forEach((p,i)=>{if(i%stride===0||i===points.length-1)markup+=`<circle class="chart-dot" cx="${p[0]}" cy="${p[1]}" r="3"><title>${esc(dateTime(rows[i].sampled_at))} · ${rows[i].people_count} people</title></circle>`;});
  for(let i=0;i<5;i++){const index=Math.round((rows.length-1)*i/4);markup+=`<text class="chart-label" text-anchor="${i===0?'start':i===4?'end':'middle'}" x="${35+i*176}" y="198">${esc(days>1&&!demo?new Date(rows[index].sampled_at*1000).toLocaleDateString([], {month:'short',day:'numeric'}):timeOf(rows[index].sampled_at))}</text>`;}
 }
 svg.innerHTML=markup;
 svg.setAttribute('aria-label',rows.length?`Occupancy chart with ${rows.length} readings; average ${(rows.reduce((a,r)=>a+r.people_count,0)/rows.length).toFixed(1)} people.`:'No occupancy history available');
}
function renderHistory(history){
 const rows=[...history].reverse();const visible=rows.slice(0,pageSize);
 $('#history-body').innerHTML=visible.length?visible.map(r=>`<tr><td>${num(r.sampled_at)!==null?esc(dateTime(r.sampled_at)):'—'}</td><td>${esc(num(r.people_count)??'—')}</td><td>${num(r.temperature_c)===null?'—':r.temperature_c.toFixed(1)+' °C'}</td><td>${stateHtml(r.gas_state)}</td><td>${r.lights_on===true?'On':r.lights_on===false?'Off':'Unknown'}</td><td>${num(r.fps)===null?'—':r.fps.toFixed(1)}</td></tr>`).join(''):'<tr><td colspan="6" class="empty-state">No historical readings for this period.</td></tr>';
 $('#table-caption').textContent=`${Math.min(pageSize,rows.length)} of ${rows.length} readings${data().truncated?' · latest 1,000 only':''}${demo?' · sample data':''}`;
 $('#more-history').hidden=pageSize>=rows.length;
}
function renderAlerts(alerts){const filter=$('#alert-filter').value;const rows=alerts.filter(a=>filter==='all'||a.alert_type===filter);$('#alerts-list').innerHTML=rows.length?rows.map(activity).join(''):'<div class="empty-state">No matching safety events in this period.</div>';}
function renderDevices({live,gasState,tempState,controllerState,valid,globalState}){
 const devices=[['chip','Arduino Uno / Nano','Runs local gas alarm logic, even when the computer is offline.',controllerState],['air','MQ-5 gas sensor','Digital input D4 · Active low. Warmup and missing readings are marked.',gasState],['temp','LM35 temperature','Analog input A0 · 45 °C high-temperature threshold.',tempState],['light','Classroom lighting','Digital output D2 · 10-second empty-room delay.',controllerState],['bell','Local buzzer','Digital output D3 · No remote mute command.',controllerState],['grid','Vision processor',valid&&num(live?.inference_ms)!==null?`YOLO · ${live.inference_ms.toFixed(1)} ms inference · ${live.fps?.toFixed(1)??'—'} FPS`:'YOLO detection + ByteTrack · Runs on local computer.',valid?(live.source_state || 'disconnected'):globalState]];
 $('#device-list').innerHTML=devices.map(([sym,name,desc,state])=>`<article class="device-card">${icon(sym)}<h3>${name}</h3><p>${esc(desc)}</p>${stateHtml(state)}</article>`).join('');
}
async function refresh(){
 if(demo){render();return;}
 if(busy)return;busy=true;const id=++requestId;
 const previous=workspace;
 try {
  const response=await fetch(`/api/monitoring?days=${days}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  const result=await response.json();
  if(id!==requestId||demo)return;
  if(response.status===401)workspace={mode:'locked',live:null,history:[],alerts:[]};
  else if(!response.ok)workspace={...previous,mode:'error'};
  else workspace=result;
 }catch {if(id===requestId&&!demo)workspace={...previous,mode:'error'};}
 finally {busy=false;render();}
}
function setDemo(on){demo=on;requestId++;busy=false;sample=undefined;const url=new URL(location.href);if(on)url.searchParams.set('demo','1');else url.searchParams.delete('demo');history.replaceState(null,'',url);render();if(!on)refresh();toast(on?'Sample workspace opened. No hardware is connected.':'Checking your live workspace…');}
function setDays(value){days=Number(value);pageSize=30;$$('[data-days]').forEach(el=>el.classList.toggle('selected',Number(el.dataset.days)===days));$('#history-range').value=String(days);if(demo)toast('Demo contains one illustrative day. Connect live for longer history.');refresh();}
$$('[data-view]').forEach(el=>el.addEventListener('click',()=>showView(el.dataset.view)));
$$('[data-days]').forEach(el=>el.addEventListener('click',()=>setDays(el.dataset.days)));
$('#history-range').addEventListener('change',event=>setDays(event.target.value));
$('#alert-filter').addEventListener('change',()=>renderAlerts(data().alerts));
$('#more-history').addEventListener('click',()=>{pageSize+=30;renderHistory(data().history);});
$('#mode-action').addEventListener('click',()=>{if(!demo&&workspace.mode==='setup')setDemo(true);else showView('settings');});
$('#connection-button').addEventListener('click',()=>showView('settings'));
$('#refresh').addEventListener('click',()=>{refresh();toast(demo?'Demo readings refreshed.':'Refreshing classroom readings…');});
$('#demo-mode').addEventListener('click',()=>setDemo(true));
$('#live-mode').addEventListener('click',()=>setDemo(false));
$('#close-menu').addEventListener('click',()=>{$('#sidebar').classList.remove('open');$('#menu').setAttribute('aria-expanded','false');});
$('#menu').addEventListener('click',()=>{$('#sidebar').classList.toggle('open');$('#menu').setAttribute('aria-expanded',String($('#sidebar').classList.contains('open')));});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){$('#sidebar').classList.remove('open');$('#menu').setAttribute('aria-expanded','false');}});
$('#room-info').addEventListener('click',()=>info('One room, in focus.','This workspace monitors the main classroom. The seating illustration is a schematic, not a live map of individual people. Counts come from the camera; sensor readings come from the local Arduino.'));
$('#login-form').addEventListener('submit',async event=>{
 event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;
 try{const response=await fetch('/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('#password').value}),signal:AbortSignal.timeout(10000)});const result=await response.json();if(!response.ok)throw new Error(result.error || 'Could not connect');$('#password').value='';$('#login-message').textContent='Connected. Opening your live workspace.';setDemo(false);}
 catch(error){$('#login-message').textContent=error.name==='TimeoutError'?'Connection timed out. Try again.':error.message;}
 finally{button.disabled=false;}
});
$('#logout').addEventListener('click',async()=>{try{await fetch('/api/session',{method:'DELETE'});workspace={mode:'locked',live:null,history:[],alerts:[]};render();toast('Signed out.');}catch{toast('Could not sign out. Check your connection.');}});
$('#export').addEventListener('click',()=>{
 const rows=data().history;if(!rows.length){toast('No historical readings to export yet.');return;}
 const columns=['sampled_at','people_count','temperature_c','gas_state','lights_on','fps'];
 const cell=v=>`"${String(v??'').replace(/^[=+@-]/,"'$&").replaceAll('"','""')}"`;
 const csv=[columns.join(','),...rows.map(row=>columns.map(key=>cell(key==='sampled_at'?new Date(row[key]*1000).toISOString():row[key])).join(','))].join('\r\n');
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=`classisense-${demo?'demo':'live'}-${new Date().toISOString().slice(0,10)}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Classroom history exported.');
});
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installEvent=event;});
async function install(){
 if(installEvent){await installEvent.prompt();await installEvent.userChoice;installEvent=null;}
 else if(matchMedia('(display-mode: standalone)').matches)info('Already at home.','ClassiSense is running as an installed app.');
 else info('A home for your observatory.','On iPhone or iPad: open this page in Safari, tap Share, then Add to Home Screen.\n\nOn Android or desktop: open your browser menu and choose Install app or Add to Home Screen. Availability depends on your browser.');
}
$('#install-side').addEventListener('click',install);$('#install-main').addEventListener('click',install);
$('#dialog-close').addEventListener('click',()=>$('#info-dialog').close());$('#dialog-ok').addEventListener('click',()=>$('#info-dialog').close());
window.addEventListener('online',()=>{toast('Back online. Checking readings…');refresh();});
window.addEventListener('offline',()=>{render();toast('Offline. Live readings are unavailable.');});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
$('#today').textContent=new Date().toLocaleDateString([], {weekday:'short',month:'short',day:'numeric',year:'numeric'});
render();refresh();setInterval(()=>{if(!document.hidden)refresh();},10000);setInterval(()=>{if(!document.hidden&&!demo)render();},3000);
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>console.warn('Offline shell unavailable'));
