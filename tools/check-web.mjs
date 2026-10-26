import {readFile,access} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
for(const file of ['public/index.html','public/styles.css','public/app.js','public/sw.js','public/manifest.webmanifest','public/icons/icon-192.png','public/icons/icon-512.png']) await access(file);
for(const file of ['public/app.js','public/sw.js','api/monitoring.js','api/session.js','lib/firebase.js','lib/auth.js'])execFileSync(process.execPath,['--check',file]);
const manifest=JSON.parse(await readFile('public/manifest.webmanifest','utf8'));
if(manifest.display!=='standalone' || manifest.icons.length<2)throw new Error('Invalid PWA manifest');
console.log('Web build verified: static assets, JavaScript, API modules and PWA manifest.');
