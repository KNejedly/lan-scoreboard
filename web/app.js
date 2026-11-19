"use strict";
const $ = id => document.getElementById(id);
const esc = v => String(v ?? "—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number = n => n == null ? "—" : Number(n).toLocaleString("cs-CZ");
const when = s => s ? new Date(s).toLocaleString("cs-CZ",{dateStyle:"short",timeStyle:"short"}) : "Čeká se na první zápis";
const dataURL = document.querySelector('meta[name="lan-feed"]')?.content || "state.json";
const cache = "pivni-burza-v1:"+new URL(dataURL,location.href).href;
let data, view="home", tv=new URLSearchParams(location.search).has("tv"), paused=false, page=0;
const title = g => g.count===0 ? "Připraveno" : g.count===g.planned ? "Dohráno" : "Probíhá";
function table(head,rows){
 const heading=head.map(h=>'<th>'+esc(h)+'</th>').join('');
 const body=rows.map(row=>'<tr>'+row.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join('');
 return '<table><thead><tr>'+heading+'</tr></thead><tbody>'+body+'</tbody></table>';
}
function board(short){
 const rows=data.board.slice(short?0:(tv?page*12:0),short?5:(tv?(page+1)*12:undefined));
 return '<section class="panel"><h2>Celkové pořadí</h2>'+(!data.hasAwards?'<p class="hint">Čeká se na schválené LAN body. Herní skóre najdete u jednotlivých disciplín.</p>':'')+table(["Poř.","Hráč","Posun","LAN body"],rows.map(r=>[number(r.rank),'<span class="'+(r.rank===1?'leader':'')+'">'+esc(r.name)+'</span>',r.delta?'<span class="'+(r.delta>0?'up':'down')+'">'+(r.delta>0?'↑ ':'↓ ')+Math.abs(r.delta)+'</span>':'—',number(r.points)]))+(short?'<button class="more" data-open="board">Všichni hráči ('+data.players+')</button>':'')+'</section>'}
function history(matches,brief=false){return matches.length?matches.map(m=>'<div class="recent"><strong>'+esc(m.title)+'</strong><p class="muted">'+esc(m.game)+' · '+esc(when(m.at))+'</p><p>'+m.rows.filter(r=>r.rank===1).map(r=>esc(r.name)+' · '+number(r.value)).join(' / ')+'</p>'+(!brief?'<details><summary>Výsledky zápasu</summary>'+table(["Poř.","Hráč","Statistiky"],m.rows.map(r=>[number(r.rank),esc(r.name),Object.entries(r.stats).map(([k,v])=>esc(k)+' '+number(v)).join(' · ')+(r.score!=null?' · Skóre '+number(r.score):'')]))+'</details>':'')+'</div>').join(''):'<p class="muted">První dokončený zápas se zobrazí po zápisu výsledku.</p>'}
function card(g){return '<button class="game '+esc(g.color)+'" data-open="'+esc(g.id)+'"><span class="gtop"><span class="mark">'+esc(g.mark)+'</span><span class="tag">'+title(g)+'</span></span><h3>'+esc(g.name)+'</h3><span class="sub">'+esc(g.genre)+'</span><span class="gfoot">'+g.count+' / '+g.planned+' zápasů'+(g.count?'<br>'+g.standings.slice(0,3).map(r=>esc(r.name)+' '+number(r.value)).join(' · ')+'<br>Poslední: '+esc(g.history[0].title):' · Detail hry')+'</span></button>'}
function render(){
 document.body.classList.toggle("tv",tv);$("tvbar").hidden=!tv;
 if(!data)return;
 $("ng").textContent=data.games.length;$("np").textContent=data.players;$("nm").textContent=data.recent.length;$("updated").textContent="Poslední zápis · "+when(data.updated);
 document.querySelectorAll("[data-view]").forEach(b=>b.setAttribute("aria-pressed",String(view===b.dataset.view)));
 let html;
 if(view==="home") html='<h2>Disciplíny</h2><div class="grid">'+data.games.map(card).join("")+'</div><div class="panels">'+board(true)+'<section class="panel"><h2>Poslední výsledky</h2>'+history(data.recent.slice(0,3),true)+'</section></div>';
 else if(view==="board")html=board(false);
 else if(view==="history")html='<section class="panel"><h2>Zápasy</h2>'+history(data.recent)+'</section>';
 else {const g=data.games.find(g=>g.id===view);if(!g){view="home";return render()}
 html='<button class="back" data-open="home">Zpět na přehled</button><section class="panel"><p class="micro">'+title(g)+' · '+g.count+' / '+g.planned+' zápasů</p><h2>'+esc(g.name)+'</h2>'+(g.provisional?'<p class="hint">Dílčí výsledky disciplíny. Konečné hodnocení potvrzuje pořadatel.</p>':'')+(g.standings.length?table(["Poř.","Hráč",g.metric],g.standings.map(r=>[number(r.rank),esc(r.name),number(r.value)])):'<p class="muted">Čeká se na první výsledek.</p>')+'<h3>Odehrané zápasy</h3>'+history(g.history,tv)+'</section>'}
 $("content").innerHTML=html;
}
function select(v){view=v;page=0;render()}
document.addEventListener("click",e=>{const b=e.target.closest("[data-view],[data-open]");if(b)select(b.dataset.view||b.dataset.open)});
async function refresh(){
 try{const res=await fetch(dataURL+(dataURL.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store",signal:AbortSignal.timeout(8000)});if(!res.ok)throw Error();
 const d=await res.json();if(d.schema!==1||d.tournament!=="lan-2026-11"||!Array.isArray(d.games)||!Array.isArray(d.board)||!Array.isArray(d.recent))throw Error();
 if(!data||JSON.stringify(data)!==JSON.stringify(d)){data=d;render();$("content").classList.remove("change");void $("content").offsetWidth;$("content").classList.add("change");try{localStorage.setItem(cache,JSON.stringify(d))}catch{}}
 $("live").textContent="Připojeno · obnova 5 s";$("live").className="";
 }catch{$("live").textContent=data?"Výpadek · poslední známá data":"Zdroj je nedostupný";$("live").className="off"}
 finally{document.body.dataset.connection=$("live").textContent;setTimeout(refresh,5000)}
}
function advance(){if(!data)return;if(view==="board"&&(page+1)*12<data.board.length){page++;return render()}const list=["board",...data.games.map(g=>g.id)];select(list[(list.indexOf(view)+1)%list.length])}
$("tv").onclick=()=>{tv=true;select("board");document.documentElement.requestFullscreen?.().catch(()=>{})};
$("exit").onclick=()=>{tv=false;select("home");if(document.fullscreenElement)document.exitFullscreen().catch(()=>{})};
document.addEventListener("fullscreenchange",()=>{$("full").textContent=document.fullscreenElement?"Opustit celou obrazovku":"Celá obrazovka"});
$("full").onclick=()=>{if(document.fullscreenElement){document.exitFullscreen()}else{document.documentElement.requestFullscreen?.().catch(()=>{$("full").textContent="Použijte F11"})}};$("next").onclick=advance;
$("pause").onclick=()=>{paused=!paused;$("pause").textContent=paused?"Pokračovat ve střídání":"Pozastavit střídání"};
setInterval(()=>{if(tv&&!paused)advance()},14000);
if(tv)view="board";try{let d=JSON.parse(localStorage.getItem(cache));if(d?.schema===1&&d.tournament==="lan-2026-11")data=d}catch{}render();refresh();
