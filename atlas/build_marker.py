#!/usr/bin/env python3
"""Phase 2 擺點工具：載入部位底圖與現有座標，人工拖曳紅點校正，匯出 §6 格式 JSON。
自足單檔（底圖 base64 內嵌），可發成 Artifact 在瀏覽器直接用。
用法：python3 atlas/build_marker.py [座標JSON路徑]（預設 data/atlas-coords/二二部位.json）"""
import json, base64, sys
from pathlib import Path

TEMPLATE = r'''<div id="marker">
<style>
  #marker{--paper:#f4f1ea;--panel:#fffdf7;--ink:#26221c;--soft:#6b6459;--faint:#9a9184;
    --line:#e2dccd;--jade:#3f7d73;--jade-d:#2f6259;--cinnabar:#c8442e;--cinnabar-soft:#f2ddd7;
    font-family:"Noto Sans TC","PingFang TC",system-ui,sans-serif;color:var(--ink);background:var(--paper);
    max-width:1060px;margin:0 auto;padding:20px 16px 60px;line-height:1.55}
  #marker *{box-sizing:border-box}
  #marker .kicker{font-size:.72rem;letter-spacing:.2em;color:var(--jade-d);font-weight:700;text-transform:uppercase;margin:0 0 5px}
  #marker h1{font-size:1.4rem;font-weight:900;margin:0 0 6px}
  #marker .lede{color:var(--soft);font-size:.86rem;margin:0 0 14px;max-width:66ch}
  #marker .lede b{color:var(--cinnabar)}
  #marker .grid{display:grid;grid-template-columns:1.35fr .9fr;gap:18px;align-items:start}
  @media(max-width:720px){#marker .grid{grid-template-columns:1fr}}
  #marker .figure{position:relative;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--panel);touch-action:none}
  #marker .figure img{display:block;width:100%;height:auto;user-select:none;-webkit-user-drag:none}
  #marker .pt{position:absolute;width:18px;height:18px;border-radius:50%;transform:translate(-50%,-50%);
    background:var(--cinnabar);border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45);cursor:grab}
  #marker .pt.sel{width:22px;height:22px;box-shadow:0 0 0 3px var(--jade),0 1px 5px rgba(0,0,0,.45);z-index:5}
  #marker .pt.dragging{cursor:grabbing}
  #marker .ptlab{position:absolute;transform:translate(-50%,-160%);background:var(--ink);color:var(--paper);
    font-size:.7rem;font-weight:700;padding:1px 6px;border-radius:5px;white-space:nowrap;pointer-events:none;z-index:6}
  #marker .side h2{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:0 0 8px}
  #marker .row{display:flex;align-items:center;gap:8px;padding:7px 9px;border:1px solid var(--line);border-radius:9px;
    margin-bottom:6px;cursor:pointer;background:var(--panel);font-size:.86rem}
  #marker .row.sel{border-color:var(--cinnabar);background:var(--cinnabar-soft)}
  #marker .row .nm{font-weight:700;flex:1}
  #marker .row .co{font-size:.72rem;color:var(--faint);font-variant-numeric:tabular-nums}
  #marker .row .badge{font-size:.66rem;color:#fff;background:var(--jade);border-radius:10px;padding:0 6px}
  #marker .row.todo .badge{background:var(--faint)}
  #marker .actions{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
  #marker button{font-family:inherit;font-size:.84rem;border:1px solid var(--line);background:var(--panel);
    color:var(--ink);border-radius:9px;padding:7px 13px;cursor:pointer}
  #marker button.primary{background:var(--jade-d);color:#fff;border-color:var(--jade-d);font-weight:700}
  #marker textarea{width:100%;margin-top:10px;height:130px;font-family:ui-monospace,monospace;font-size:.72rem;
    border:1px solid var(--line);border-radius:9px;padding:8px;background:var(--panel);color:var(--ink);resize:vertical}
  #marker .hint{font-size:.76rem;color:var(--faint);margin-top:8px;line-height:1.6}
  @media(prefers-color-scheme:dark){#marker{--paper:#14130f;--panel:#1c1a15;--ink:#e9e4d8;--soft:#a89f90;
    --faint:#7a7264;--line:#2c2921;--jade:#5aa89b;--jade-d:#7cc4b6;--cinnabar:#e0685a;--cinnabar-soft:#2a1815}}
</style>
<p class="kicker">董氏奇穴地圖 · 擺點工具 Phase 2</p>
<h1 id="rtitle">擺點校正</h1>
<p class="lede">紅點已帶入目前座標。<b>直接拖曳紅點</b>到正確位置，或先點右側清單選穴、再點圖上位置。全部擺好按「匯出 JSON」，把內容存回 <code>__FNAME__</code> 再重跑 build_atlas.py。</p>
<div class="grid">
  <div class="figure" id="figure">
    <img id="img" alt="部位底圖" />
    <div id="dots"></div>
  </div>
  <div class="side">
    <h2 id="rlabel"></h2>
    <div id="list"></div>
    <div class="actions">
      <button class="primary" id="exportBtn">⤓ 匯出 JSON</button>
      <button id="dlBtn">下載檔案</button>
      <button id="resetBtn">還原</button>
    </div>
    <textarea id="out" readonly placeholder="按「匯出 JSON」後這裡會出現內容，可全選複製…"></textarea>
    <p class="hint">提示：拖曳時放大瀏覽器可擺更準；座標以圖片相對比例(0–1)儲存，換底圖尺寸也不會跑掉。</p>
  </div>
</div>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
(function(){
  var coord=JSON.parse(document.getElementById('data').textContent);
  var IMG="__IMG__";
  var orig=JSON.parse(JSON.stringify(coord.points));
  document.getElementById('img').src=IMG;
  document.getElementById('rtitle').textContent=coord.region+' 擺點校正';
  document.getElementById('rlabel').textContent=coord.region+'（'+coord.points.length+' 穴）';
  var figure=document.getElementById('figure'), dotsWrap=document.getElementById('dots'), listWrap=document.getElementById('list');
  var sel=-1, dragging=-1, placed=coord.points.map(function(){return true;});
  var dotEls=[], labEls=[];
  coord.points.forEach(function(p,i){
    var d=document.createElement('div'); d.className='pt'; d.dataset.i=i;
    var l=document.createElement('div'); l.className='ptlab'; l.textContent=p.name;
    dotsWrap.appendChild(d); dotsWrap.appendChild(l); dotEls.push(d); labEls.push(l);
    d.addEventListener('pointerdown',function(e){ e.preventDefault(); dragging=i; setSel(i); d.classList.add('dragging'); d.setPointerCapture(e.pointerId); });
  });
  figure.addEventListener('pointermove',function(e){ if(dragging<0)return; place(dragging,e); });
  figure.addEventListener('pointerup',function(e){ if(dragging<0)return; dotEls[dragging].classList.remove('dragging'); dragging=-1; });
  // 點圖：把選中的穴移到該處（拖曳的替代）
  figure.addEventListener('click',function(e){ if(e.target.classList.contains('pt'))return; if(sel<0)return; place(sel,e); });
  function place(i,e){
    var r=figure.getBoundingClientRect();
    var x=Math.min(1,Math.max(0,(e.clientX-r.left)/r.width));
    var y=Math.min(1,Math.max(0,(e.clientY-r.top)/r.height));
    coord.points[i].x=Math.round(x*1e4)/1e4; coord.points[i].y=Math.round(y*1e4)/1e4;
    placed[i]=true; render();
  }
  function setSel(i){ sel=i; render(); }
  function render(){
    coord.points.forEach(function(p,i){
      dotEls[i].style.left=(p.x*100)+'%'; dotEls[i].style.top=(p.y*100)+'%';
      dotEls[i].classList.toggle('sel',i===sel);
      labEls[i].style.left=(p.x*100)+'%'; labEls[i].style.top=(p.y*100)+'%';
      labEls[i].style.display=(i===sel)?'block':'none';
    });
    listWrap.innerHTML='';
    coord.points.forEach(function(p,i){
      var row=document.createElement('div'); row.className='row'+(i===sel?' sel':'');
      row.innerHTML='<span class="nm">'+p.name+'</span><span class="co">'+p.x.toFixed(3)+', '+p.y.toFixed(3)+'</span><span class="badge">'+p.code+'</span>';
      row.onclick=function(){ setSel(i); };
      listWrap.appendChild(row);
    });
  }
  function exportJSON(){
    var o=Object.assign({},coord);
    o.note=(coord.note||'').replace('目測佔位','人工校正')+'（擺點工具校正）';
    return JSON.stringify(o,null,2);
  }
  document.getElementById('exportBtn').onclick=function(){ document.getElementById('out').value=exportJSON(); document.getElementById('out').select(); };
  document.getElementById('dlBtn').onclick=function(){
    var blob=new Blob([exportJSON()],{type:'application/json'});
    var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='__FNAME__'; a.click();
  };
  document.getElementById('resetBtn').onclick=function(){ coord.points.forEach(function(p,i){p.x=orig[i].x;p.y=orig[i].y;}); render(); };
  render();
})();
</script>
</div>'''

ROOT = Path(__file__).resolve().parent.parent
coord_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data/atlas-coords/二二部位.json'
coord = json.loads(coord_path.read_text())
img = (ROOT / coord['base_image']).read_bytes()
img_b64 = 'data:image/png;base64,' + base64.b64encode(img).decode()
payload = json.dumps(coord, ensure_ascii=False)

html = TEMPLATE.replace('__PAYLOAD__', payload).replace('__IMG__', img_b64)\
              .replace('__FNAME__', coord_path.name)
out = ROOT / 'atlas/marker.html'
out.write_text(html)
print('寫入', out, len(html), 'bytes；穴數', len(coord['points']))
