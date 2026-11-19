const $=s=>document.getElementById(s), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let session=location.hash.slice(1), data, evidence=[];
const option=(v,label)=>'<option value="'+esc(v)+'">'+esc(label)+'</option>';
const note=s=>$("note").textContent=s;
async function request(payload){const r=await fetch("../api",{method:payload?"POST":"GET",headers:{"X-LAN-Session":session,"Content-Type":"application/json"},body:payload?JSON.stringify(payload):undefined});if(!r.ok){let b=await r.json();throw Error(b.reason||"Ovládání vyžaduje otevření přes místní spouštěč nebo notebook.")}return r.json()}
const game=()=>data.config.games.find(g=>g.id===$("game").value), slot=()=>game().slots.find(s=>s.id===$("slot").value), signature=()=>game().id+"/"+slot().id;
const players=()=>Object.entries(data.state.players);
function setSlots(old){$("slot").innerHTML=game().slots.map(s=>option(s.id,s.title)).join("");if(game().slots.some(s=>s.id===old))$("slot").value=old;grid()}
function grid(){
 evidence=[];$("files").value="";$("replace").checked=false;$("transcript").hidden=true;
 const spec=slot(),old=data.state.matches[signature()];$("rule").textContent=spec.review||"Ověřené skóre zápasu: 200 × zabití − 100 × úmrtí.";
 $("rows").innerHTML='<table><thead><tr><th>Hraje</th><th>Hráč</th>'+spec.fields.map(f=>'<th>'+esc(data.config.labels[f])+'</th>').join("")+'</tr></thead><tbody>'+players().map(([id,p])=>'<tr data-p="'+esc(id)+'"><td><input type="checkbox" aria-label="Účast '+esc(p.public)+'" '+(!old||old.rows[id]?"checked":"")+'></td><td>'+esc(p.public)+'<small class="sub"> '+esc(p.aliases[0]||"")+'</small></td>'+spec.fields.map(f=>'<td><input data-f="'+esc(f)+'" aria-label="'+esc(data.config.labels[f]+' '+p.public)+'" type="number" min="'+(f==="place"?1:0)+'" value="'+esc(old?.rows[id]?.stats[f]??"")+'"></td>').join("")+'</tr>').join("")+'</tbody></table>';
 const ids=new Set(Object.entries(data.state.matches).filter(([k])=>k.startsWith(game().id+"/")).flatMap(([,m])=>Object.keys(m.rows)));
 $("awardrows").innerHTML=players().filter(([id])=>ids.has(id)).map(([id,p])=>'<label>'+esc(p.public)+'<input data-award="'+id+'" type="number" value="'+esc(data.state.awards[game().id]?.points[id]??"")+'"></label>').join("");
}
function playerFields(){const p=data.state.players[$("pid").value];$("public").value=p?.public||"";$("aliases").value=p?.aliases.join(", ")||""}
async function load(){const g=$("game").value,s=$("slot").value;data=await request();$("game").innerHTML=data.config.games.map(g=>option(g.id,g.name)).join("");if(data.config.games.some(x=>x.id===g))$("game").value=g;setSlots(s);
 $("pid").innerHTML=option("","Nový hráč")+players().map(([id,p])=>option(id,p.public)).join("");playerFields();
 $("changes").textContent=data.history.changes.map(r=>r[0]+" · "+r[2]).join(" | ");$("logs").textContent=data.history.processing.slice(0,5).map(r=>r[1]+" · "+r[2].slice(0,200)).join(" | ");
 $("rev").innerHTML=data.history.changes.filter(r=>r[0]<data.rev).map(r=>option(r[0],r[0]+" · "+r[2])).join("");
 $("sync").textContent="Revize "+data.rev+" · "+(data.online?"Online přenos nastaven":"Místní provoz");$("engine").options[1].disabled=!data.openai}
const checked=()=>Array.from($("rows").querySelectorAll("tr[data-p]")).filter(r=>r.querySelector("input").checked);
const common=()=>({rev:data.rev,game:game().id,slot:slot().id,expected:checked().map(r=>r.dataset.p)});
async function mutate(action,extra={}){let r=await request({action,...common(),...extra});if(!r.ok)throw Error(r.reason);await load();note((r.publication||"Uloženo")+" · revize "+data.rev)}
function act(id,fn){$(id).onclick=async()=>{const b=$(id);b.disabled=true;try{await fn()}catch(e){note(e.message)}finally{b.disabled=false}}}
$("game").onchange=()=>setSlots();$("slot").onchange=grid;$("pid").onchange=playerFields;
act("save",async()=>{const rows=checked().map(tr=>({nick:data.state.players[tr.dataset.p].public,stats:Object.fromEntries(Array.from(tr.querySelectorAll("[data-f]"),el=>[el.dataset.f,el.value===""?null:Number(el.value)]))}));
await mutate("match",{rows,replace:$("replace").checked,digests:evidence})});
act("read",async()=>{const fs=Array.from($("files").files);if(!fs.length||fs.length>3||fs.some(f=>f.size>8388608))throw Error("Vyberte 1–3 obrázky do 8 MiB.");
 note("Čtení snímků…");const files=await Promise.all(fs.map(f=>new Promise((ok,no)=>{const r=new FileReader();r.onload=()=>ok(r.result.split(",")[1]);r.onerror=no;r.readAsDataURL(f)})));
 const r=await request({action:"process",...common(),files,engine:$("engine").value});if(r.ok){await load();note(r.publication+" · revize "+r.rev);return}
 evidence=r.digests||[];$("raw").textContent=JSON.stringify(r.data,null,2);$("transcript").hidden=!r.data;
 const norm=s=>String(s??"").normalize("NFKC").trim().toLowerCase();
 for(const line of r.data?.rows||[]){let p=players().find(([,p])=>[p.public,...p.aliases].some(a=>norm(a)===norm(line.nick)));if(p){const tr=$("rows").querySelector('[data-p="'+p[0]+'"]');for(const el of tr.querySelectorAll("[data-f]"))el.value=line.stats[el.dataset.f]??""}}
 note("Ke kontrole · "+r.reason)});
act("cancel",()=>confirm("Zrušit vybraný zápas? Změna zůstane v historii.")&&mutate("cancel",{key:signature()}));
act("restore",()=>confirm("Obnovit zvolenou revizi hráčů, zápasů a LAN bodů?")&&mutate("restore",{target:Number($("rev").value)}));
act("player",()=>mutate("player",{pid:$("pid").value,public:$("public").value,aliases:$("aliases").value.split(",")}));
act("award",()=>mutate("award",{source:$("source").value,points:Object.fromEntries(Array.from($("awardrows").querySelectorAll("input"),el=>[el.dataset.award,el.value===""?null:Number(el.value)]))}));
act("publish",()=>mutate("publish"));
(async()=>{try{if(!session)session=(await (await fetch("../session")).json()).token;if(location.hash)history.replaceState(null,"",location.pathname);await load()}catch(e){note(e.message)}})();
