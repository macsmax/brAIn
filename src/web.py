"""Minimal web UI for browsing and editing brain memories."""

import json
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from .store import MemoryStore

store = MemoryStore()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>brAIn</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;max-width:900px;margin:0 auto;padding:20px}
h1{font-size:1.5em;margin-bottom:16px}h1 span{font-size:.6em;color:#8b949e}
.tabs{display:flex;gap:8px;margin-bottom:16px}
.tab{padding:6px 14px;border-radius:6px;border:1px solid #30363d;background:none;color:#c9d1d9;cursor:pointer}
.tab.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
input,textarea,select{background:#161b22;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:8px;width:100%;font-family:inherit}
textarea{resize:vertical;min-height:60px}
.row{display:flex;gap:8px;margin-bottom:8px}
.row>*{flex:1}
button{padding:8px 16px;border-radius:6px;border:none;background:#238636;color:#fff;cursor:pointer;font-size:.9em}
button:hover{background:#2ea043}
button.danger{background:#da3633}button.danger:hover{background:#f85149}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin-bottom:8px}
.card .meta{font-size:.75em;color:#8b949e;margin-top:6px}
.card .content{white-space:pre-wrap;word-break:break-word}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.7em;background:#30363d;margin-right:4px}
.search{margin-bottom:16px}
#status{position:fixed;top:10px;right:10px;padding:8px 14px;border-radius:6px;background:#238636;color:#fff;display:none;font-size:.85em}
.profile-row{display:flex;gap:8px;align-items:center;margin-bottom:6px}
.profile-row input{width:auto;flex:1}
.profile-row .key{width:120px;flex:none}
pre{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;overflow-x:auto;font-size:.85em;max-height:500px;overflow-y:auto}
</style>
</head>
<body>
<h1>&#129504; brAIn <span>local AI second brain</span></h1>
<div class="tabs">
<button class="tab active" onclick="showTab('memories')">Memories</button>
<button class="tab" onclick="showTab('profile')">Profile</button>
<button class="tab" onclick="showTab('add')">Add</button>
<button class="tab" onclick="showTab('export')">Export</button>
</div>

<div id="memories" class="panel">
<div class="row search">
<input id="q" placeholder="Search memories..." onkeyup="if(event.key==='Enter')search()">
<select id="cat-filter" onchange="search()"><option value="">All categories</option></select>
<button onclick="search()">Search</button>
</div>
<div id="results"></div>
</div>

<div id="profile" class="panel" style="display:none">
<div id="profile-list"></div>
<div class="row" style="margin-top:12px">
<input id="pk" placeholder="Key"><input id="pv" placeholder="Value">
<button onclick="setProfile()">Set</button>
</div>
</div>

<div id="add" class="panel" style="display:none">
<div class="row"><select id="new-cat"></select><input id="new-tags" placeholder="Tags (comma-separated)"></div>
<textarea id="new-content" placeholder="What to remember..." rows="4"></textarea>
<button style="margin-top:8px" onclick="addMemory()">Remember</button>
</div>

<div id="export" class="panel" style="display:none">
<button onclick="doExport()">Export to Markdown</button>
<pre id="export-out" style="margin-top:12px"></pre>
</div>

<div id="status"></div>

<script>
const API='';
const CATS=['identity','preferences','projects','people','workflows','knowledge','conversations'];
const catFilter=document.getElementById('cat-filter');
const newCat=document.getElementById('new-cat');
CATS.forEach(c=>{catFilter.innerHTML+=`<option value="${c}">${c}</option>`;newCat.innerHTML+=`<option value="${c}">${c}</option>`});

function showTab(id){document.querySelectorAll('.panel').forEach(p=>p.style.display='none');document.getElementById(id).style.display='';document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));event.target.classList.add('active');if(id==='memories')search();if(id==='profile')loadProfile()}

function flash(msg){const s=document.getElementById('status');s.textContent=msg;s.style.display='block';setTimeout(()=>s.style.display='none',2000)}

async function search(){
const q=document.getElementById('q').value;const cat=catFilter.value;
let url=API+'/api/memories?limit=50';if(cat)url+=`&category=${cat}`;if(q)url+=`&q=${encodeURIComponent(q)}`;
const r=await fetch(url).then(r=>r.json());
document.getElementById('results').innerHTML=r.map(m=>`<div class="card"><div class="content">${esc(m.content)}</div><div class="meta"><span class="badge">${m.category}</span>${m.tags?m.tags.split(',').map(t=>`<span class="badge">${t.trim()}</span>`).join(''):''}id: ${m.id} | ${m.created_at}${m.similarity!=null?` | sim: ${m.similarity}`:''}<button class="danger" style="float:right;padding:2px 8px;font-size:.75em" onclick="del('${m.id}')">forget</button></div></div>`).join('')||'<p style="color:#8b949e">No memories found.</p>'}

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}

async function del(id){if(!confirm('Forget this memory?'))return;await fetch(API+`/api/memories/${id}`,{method:'DELETE'});flash('Forgotten');search()}

async function loadProfile(){const p=await fetch(API+'/api/profile').then(r=>r.json());document.getElementById('profile-list').innerHTML=Object.entries(p).map(([k,v])=>`<div class="profile-row"><input class="key" value="${esc(k)}" readonly><input value="${esc(v)}" readonly></div>`).join('')||'<p style="color:#8b949e">No profile set.</p>'}

async function setProfile(){const k=document.getElementById('pk').value.trim(),v=document.getElementById('pv').value.trim();if(!k||!v)return;await fetch(API+'/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k,value:v})});flash('Saved');document.getElementById('pk').value='';document.getElementById('pv').value='';loadProfile()}

async function addMemory(){const cat=newCat.value,content=document.getElementById('new-content').value.trim(),tags=document.getElementById('new-tags').value.trim();if(!content)return;await fetch(API+'/api/memories',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category:cat,content,tags})});flash('Remembered');document.getElementById('new-content').value='';document.getElementById('new-tags').value=''}

async function doExport(){const md=await fetch(API+'/api/export').then(r=>r.text());document.getElementById('export-out').textContent=md}

search();
</script>
</body>
</html>"""


async def index(request):
    return HTMLResponse(HTML)


async def api_memories(request):
    q = request.query_params.get("q")
    cat = request.query_params.get("category")
    limit = int(request.query_params.get("limit", "50"))
    if q:
        results = store.recall(q, category=cat, limit=limit)
    else:
        results = store.list_memories(category=cat, limit=limit)
    return JSONResponse(results)


async def api_memories_create(request):
    body = await request.json()
    result = store.remember(body["category"], body["content"], body.get("tags", ""))
    return JSONResponse(result)


async def api_memories_delete(request):
    mid = request.path_params["id"]
    return JSONResponse(store.forget(mid))


async def api_profile_get(request):
    return JSONResponse(store.get_profile())


async def api_profile_set(request):
    body = await request.json()
    return JSONResponse(store.set_profile(body["key"], body["value"]))


async def api_export(request):
    md = store.export_markdown()
    return HTMLResponse(md, media_type="text/plain")


app = Starlette(routes=[
    Route("/", index),
    Route("/api/memories", api_memories, methods=["GET"]),
    Route("/api/memories", api_memories_create, methods=["POST"]),
    Route("/api/memories/{id}", api_memories_delete, methods=["DELETE"]),
    Route("/api/profile", api_profile_get, methods=["GET"]),
    Route("/api/profile", api_profile_set, methods=["POST"]),
    Route("/api/export", api_export),
])
