// The build embeds only public web assets and a verifier for a scoped write token.
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","Access-Control-Allow-Origin":"*"}});
async function hash(value){return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(value))),n=>n.toString(16).padStart(2,"0")).join("")}
export default {async fetch(request,env){
 const path=new URL(request.url).pathname;
 if((path==="/state.json"||path==="/qa-state.json")&&request.method==="PUT"){
   const token=request.headers.get("Authorization")||"";
   if(!token.startsWith("Bearer ")||await hash(token.slice(7))!==WRITE_VERIFIER)return json({error:"Přístup zamítnut."},403);
   const raw=await request.text();if(raw.length>600000)return json({error:"Příliš velký přehled."},413);
   let body;try{body=JSON.parse(raw)}catch{return json({error:"Neplatný JSON."},400)}
   if(body.schema!==1||body.tournament!=="lan-2026-11"||!Number.isSafeInteger(body.revision)||!Array.isArray(body.games)||!Array.isArray(body.board)||!Array.isArray(body.recent))return json({error:"Neplatný přehled."},422);
   if(!env.BUCKET)return json({error:"Úložiště není připojeno."},503);
   const old=await env.BUCKET.get(path.slice(1));
   const current=old?await old.text():"";
   if(current===raw)return json({saved:true});
   if(request.headers.get("If-Match")!==(current?await hash(current):"empty"))return json({error:"Novější vzdálený stav. Sjednoťte databáze."},409);
   const stored=await env.BUCKET.put(path.slice(1),raw,{onlyIf:old?{etagMatches:old.etag}:{etagDoesNotMatch:"*"}});
   return stored?json({saved:true}):json({error:"Souběžný zápis."},409);
 }
 if(request.method!=="GET"&&request.method!=="HEAD")return json({error:"Metoda není povolena."},405);
 if(path==="/state.json"||path==="/qa-state.json"){
   if(!env.BUCKET)return json({error:"Úložiště není připojeno."},503);
   const obj=await env.BUCKET.get(path.slice(1));if(!obj&&path==="/qa-state.json")return json({error:"Prázdné testovací úložiště."},404);
   const raw=obj?await obj.text():INITIAL;
   return new Response(request.method==="HEAD"?null:raw,{headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","Access-Control-Allow-Origin":"*","X-LAN-Digest":obj?await hash(raw):"empty","Access-Control-Expose-Headers":"X-LAN-Digest"}});
 }
 const asset=ASSETS[path==="/"?"index.html":path.slice(1)];if(!asset)return json({error:"Nenalezeno."},404);
 return new Response(request.method==="HEAD"?null:Uint8Array.from(atob(asset[1]),c=>c.charCodeAt(0)),{headers:{"Content-Type":asset[0],"Cache-Control":"no-cache","X-Content-Type-Options":"nosniff"}});
}};
