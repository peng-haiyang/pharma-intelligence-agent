// Local HTTP adapter for the exact bundled Worker; request bodies are streamed.
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {Readable} from 'node:stream';
const source=await readFile(new URL('../dist-hosted/server/index.js',import.meta.url),'utf8');
const {default:worker}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const server=createServer(async(req,res)=>{
 try{
  const method=req.method||'GET';
  const init={method,headers:req.headers};
  if(!['GET','HEAD'].includes(method)){init.body=Readable.toWeb(req);init.duplex='half';}
  const result=await worker.fetch(new Request(`http://127.0.0.1:8766${req.url}`,init));
  res.writeHead(result.status,Object.fromEntries(result.headers));
  if(result.body){const stream=Readable.fromWeb(result.body);stream.on('error',()=>res.destroy());stream.pipe(res);res.on('close',()=>stream.destroy());}else res.end();
 }catch{res.writeHead(500);res.end('Local preview failed');}
});
server.listen(8766,'127.0.0.1',()=>console.log('Live Worker preview: http://127.0.0.1:8766'));
