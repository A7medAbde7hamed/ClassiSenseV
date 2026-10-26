const CACHE='classisense-shell-v1';
const ASSETS=['/','/index.html','/styles.css','/fonts.css','/app.js','/manifest.webmanifest','/icons/mark.svg','/icons/icon-192.png','/icons/icon-512.png','/icons/maskable-512.png'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET' || url.origin!==self.location.origin || url.pathname.startsWith('/api/'))return;
 if(event.request.mode==='navigate'){
  event.respondWith(fetch(event.request).catch(()=>caches.match('/index.html')));return;
 }
 if(ASSETS.includes(url.pathname))event.respondWith(caches.match(event.request).then(cached=>cached || fetch(event.request)));
});
