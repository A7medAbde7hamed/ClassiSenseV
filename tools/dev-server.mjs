import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import monitoring from '../api/monitoring.js';
import session from '../api/session.js';
const root=path.resolve('public');
const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.png':'image/png','.webmanifest':'application/manifest+json'};
http.createServer(async(req,res)=>{
  res.status=n=>(res.statusCode=n,res);
  res.json=value=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));};
  const url=new URL(req.url,'http://localhost');
  if (url.pathname.startsWith('/api/')) {
    let body='';for await(const chunk of req){body+=chunk;if(body.length>4096){res.statusCode=413;res.end();return;}}
    req.body=body;
    return (url.pathname==='/api/monitoring'?monitoring:url.pathname==='/api/session'?session:(_req,r)=>r.status(404).json({error:'Not found'}))(req,res);
  }
  const file=path.resolve(root,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));
  if(!file.startsWith(root+path.sep)){res.statusCode=403;return res.end();}
  try {const data=await readFile(file);res.setHeader('Content-Type',types[path.extname(file)] || 'application/octet-stream');res.end(data);}
  catch {res.statusCode=404;res.end('Not found');}
}).listen(Number(process.env.PORT || (process.argv.includes('--port') ? process.argv[process.argv.indexOf('--port')+1] : 3000)),'0.0.0.0',()=>console.log('ClassiSense preview ready'));
