import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const port=Number(process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{
  if(req.url==='/health'){res.writeHead(200,{'content-type':'application/json'});return res.end(JSON.stringify({ok:true,app:'agronexo-demo'}));}
  const clean=decodeURIComponent((req.url||'/').split('?')[0]);
  let file=path.join(root,clean==='/'?'index.html':clean);
  if(!file.startsWith(root)){res.writeHead(403);return res.end('Forbidden');}
  fs.stat(file,(err,stat)=>{if(err||!stat.isFile()) file=path.join(root,'index.html');fs.readFile(file,(e,data)=>{if(e){res.writeHead(500);return res.end('Error');}res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream','cache-control':'no-store','x-content-type-options':'nosniff'});res.end(data);});});
});
server.listen(port,'127.0.0.1',()=>console.log(`AgroNexo listening on http://127.0.0.1:${port}`));
