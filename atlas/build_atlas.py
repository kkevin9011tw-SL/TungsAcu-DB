#!/usr/bin/env python3
"""Phase 1 垂直切片：把董氏奇穴地圖產成自足單檔 HTML（給 Artifact/靜態部署）。
全身層(13 部位標穴數) → 手部層(二二手背 7 穴，hover 顯名、側欄) → 連回穴位頁(佔位)。
座標為目測佔位，待顥軒校正。"""
import csv, json, base64, collections
from pathlib import Path

TEMPLATE = r'''<div id="atlas">
<style>
  #atlas{--paper:#f4f1ea;--panel:#fffdf7;--ink:#26221c;--soft:#6b6459;--faint:#9a9184;
    --line:#e2dccd;--jade:#3f7d73;--jade-d:#2f6259;--cinnabar:#c8442e;--cinnabar-soft:#f2ddd7;
    --focus:#3f7d73;font-family:"Noto Sans TC","PingFang TC",system-ui,sans-serif;
    color:var(--ink);background:var(--paper);max-width:1000px;margin:0 auto;padding:22px 18px 70px;line-height:1.6}
  #atlas *{box-sizing:border-box}
  #atlas .kicker{font-size:.72rem;letter-spacing:.22em;color:var(--jade-d);font-weight:700;text-transform:uppercase;margin:0 0 6px}
  #atlas h1{font-size:1.55rem;font-weight:900;margin:0 0 6px;letter-spacing:-.01em}
  #atlas .lede{color:var(--soft);font-size:.9rem;margin:0 0 4px;max-width:60ch}
  #atlas .warn{display:inline-block;font-size:.72rem;color:var(--cinnabar);background:var(--cinnabar-soft);
    border:1px solid #e6c5bd;border-radius:20px;padding:2px 10px;margin:8px 0 2px}
  #atlas .stage{margin-top:16px;position:relative}
  /* ---- 全身層 ---- */
  #atlas .bodywrap{position:relative;width:100%;max-width:440px;margin:6px auto 0;aspect-ratio:5/7}
  #atlas .bodywrap svg{position:absolute;inset:0;width:100%;height:100%}
  #atlas .hot{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;
    align-items:center;gap:2px;background:none;border:none;cursor:pointer;font-family:inherit}
  #atlas .hot .dot{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;
    font-size:.82rem;font-weight:800;font-variant-numeric:tabular-nums;
    background:var(--panel);border:1.5px solid var(--jade);color:var(--jade-d);transition:transform .12s,box-shadow .12s}
  #atlas .hot .lab{font-size:.68rem;color:var(--soft);white-space:nowrap}
  #atlas .hot:hover .dot,#atlas .hot:focus-visible .dot{transform:scale(1.18);box-shadow:0 3px 10px rgba(63,125,115,.35);outline:none}
  #atlas .hot.ready .dot{border-color:var(--cinnabar);color:#fff;background:var(--cinnabar)}
  #atlas .hot.ready .lab{color:var(--cinnabar);font-weight:700}
  #atlas .extra{text-align:center;margin-top:10px}
  #atlas .extra button{font-family:inherit;font-size:.8rem;border:1px dashed var(--line);background:var(--panel);
    color:var(--soft);border-radius:20px;padding:4px 12px;cursor:pointer}
  /* ---- 手部層 ---- */
  #atlas .handhead{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px}
  #atlas .back{font-family:inherit;font-size:.84rem;border:1px solid var(--line);background:var(--panel);
    color:var(--ink);border-radius:9px;padding:6px 12px;cursor:pointer}
  #atlas .back:hover{border-color:var(--jade)}
  #atlas .handgrid{display:grid;grid-template-columns:1.3fr 1fr;gap:18px;align-items:start}
  @media(max-width:680px){#atlas .handgrid{grid-template-columns:1fr}}
  #atlas .figure{position:relative;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--panel)}
  #atlas .figure img{display:block;width:100%;height:auto}
  #atlas .pt{position:absolute;width:16px;height:16px;border-radius:50%;transform:translate(-50%,-50%);
    background:var(--cinnabar);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);pointer-events:none;transition:transform .1s}
  #atlas .pt.on{transform:translate(-50%,-50%) scale(1.55);z-index:3}
  #atlas .ptlabel{position:absolute;transform:translate(-50%,-140%);background:var(--ink);color:var(--paper);
    font-size:.76rem;font-weight:700;padding:2px 8px;border-radius:6px;white-space:nowrap;pointer-events:none;z-index:4;opacity:0;transition:opacity .1s}
  #atlas .ptlabel.on{opacity:1}
  #atlas .hit{position:absolute;inset:0;cursor:crosshair}
  /* ---- 側欄 ---- */
  #atlas .panel{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:16px 18px;min-height:180px}
  #atlas .panel .empty{color:var(--faint);font-size:.88rem}
  #atlas .panel h3{margin:0 0 2px;font-size:1.15rem;font-weight:800}
  #atlas .panel .code{font-size:.76rem;color:var(--jade-d);font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:.03em}
  #atlas .panel .field{margin-top:12px}
  #atlas .panel .field .t{font-size:.68rem;font-weight:700;letter-spacing:.1em;color:var(--faint);text-transform:uppercase;margin-bottom:3px}
  #atlas .panel .field .v{font-size:.88rem;color:var(--ink)}
  #atlas .tags{display:flex;flex-wrap:wrap;gap:5px}
  #atlas .tags span{font-size:.76rem;background:var(--cinnabar-soft);color:#8a3223;border-radius:6px;padding:1px 8px}
  #atlas .more{display:inline-block;margin-top:14px;font-size:.84rem;font-weight:700;color:var(--jade-d);text-decoration:none;border-bottom:2px solid var(--jade)}
  #atlas .disc{margin-top:26px;font-size:.76rem;color:var(--faint);border-top:1px solid var(--line);padding-top:12px;line-height:1.7}
  #atlas .hidden{display:none}
  @media(prefers-color-scheme:dark){#atlas{--paper:#14130f;--panel:#1c1a15;--ink:#e9e4d8;--soft:#a89f90;
    --faint:#7a7264;--line:#2c2921;--jade:#5aa89b;--jade-d:#7cc4b6;--cinnabar:#e0685a;--cinnabar-soft:#2a1815;--focus:#5aa89b}
    #atlas .tags span{color:#e7b3a8}}
  #atlas[data-theme="dark"]{--paper:#14130f;--panel:#1c1a15;--ink:#e9e4d8;--soft:#a89f90;--faint:#7a7264;
    --line:#2c2921;--jade:#5aa89b;--jade-d:#7cc4b6;--cinnabar:#e0685a;--cinnabar-soft:#2a1815;--focus:#5aa89b}
  #atlas[data-theme="dark"] .tags span{color:#e7b3a8}
  #atlas[data-theme="light"]{--paper:#f4f1ea;--panel:#fffdf7;--ink:#26221c;--soft:#6b6459;--faint:#9a9184;
    --line:#e2dccd;--jade:#3f7d73;--jade-d:#2f6259;--cinnabar:#c8442e;--cinnabar-soft:#f2ddd7;--focus:#3f7d73}
</style>

<p class="kicker">董氏奇穴 · 互動人體地圖 · Phase 1 原型</p>
<h1 id="title">選部位</h1>
<p class="lede" id="sub">滑到部位看穴數，點紅色的「手掌」進入手背示範。此為引擎原型，穴位座標為目測佔位、待醫師校正。</p>

<div class="stage">
  <!-- 全身層 -->
  <div id="bodyLayer">
    <div class="bodywrap" id="bodywrap">
      <svg viewBox="0 0 500 700" aria-hidden="true">
        <g fill="none" stroke="var(--jade)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" opacity="0.55">
          <circle cx="250" cy="48" r="34"/>
          <path d="M250 82 L250 96 M214 120 Q250 104 286 120 L300 128"/>
          <path d="M205 128 Q250 112 295 128 L318 230 Q322 300 300 360 L285 470 M215 470 L200 360 Q178 300 182 230 Z"/>
          <path d="M205 132 L150 210 L120 330 L108 430"/>
          <path d="M295 132 L350 210 L380 330 L392 430"/>
          <path d="M250 360 L250 430 M232 462 L214 470 L196 560 L182 660 L176 690 M268 462 L286 470 L304 560 L318 660 L324 690"/>
        </g>
      </svg>
      <div id="hots"></div>
    </div>
    <div class="extra" id="extraWrap"></div>
  </div>

  <!-- 手部層 -->
  <div id="handLayer" class="hidden">
    <div class="handhead">
      <button class="back" id="backBtn">← 回全身</button>
      <div><strong id="handTitle"></strong> <span style="color:var(--faint);font-size:.8rem" id="handSub"></span></div>
    </div>
    <div class="handgrid">
      <div class="figure" id="figure">
        <img id="handImg" alt="手背底圖" />
        <div id="dots"></div>
        <div class="ptlabel" id="ptLabel"></div>
        <div class="hit" id="hit"></div>
      </div>
      <div class="panel" id="panel"><div class="empty">滑鼠移到手背上的紅點看穴名，點一下看定位與主治。</div></div>
    </div>
  </div>
</div>

<div class="disc" id="disc"></div>

<script id="data" type="application/json">__PAYLOAD__</script>
<script>
(function(){
  var D=JSON.parse(document.getElementById('data').textContent);
  var IMG="__IMG__", PURL="__PURL__";
  var atlas=document.getElementById('atlas');
  // 全身層 hotspots
  var hots=document.getElementById('hots'), extra=document.getElementById('extraWrap');
  D.regions.forEach(function(r){
    if(r.x===0&&r.y===0){ // 增補：放底部 chip
      var b=document.createElement('button');
      b.textContent='＋ '+r.label+'（'+r.n+' 穴，座標待補）';
      b.onclick=function(){toast(r.label);};
      extra.appendChild(b); return;
    }
    var btn=document.createElement('button');
    btn.className='hot'+(r.ready?' ready':'');
    btn.style.left=(r.x*100)+'%'; btn.style.top=(r.y*100)+'%';
    btn.innerHTML='<span class="dot">'+r.n+'</span><span class="lab">'+r.label+'</span>';
    btn.onclick=function(){ r.ready?openHand():toast(r.label); };
    hots.appendChild(btn);
  });
  function toast(name){
    var s=document.getElementById('sub');
    s.textContent='「'+name+'」的穴位座標尚未標記（Phase 2 補齊）。目前僅「手掌」部位可進入示範。';
  }
  // 手部層
  var bodyLayer=document.getElementById('bodyLayer'), handLayer=document.getElementById('handLayer');
  var hand=D.hand, dots=document.getElementById('dots'), hit=document.getElementById('hit');
  var ptLabel=document.getElementById('ptLabel'), panel=document.getElementById('panel');
  document.getElementById('handImg').src=IMG;
  document.getElementById('handTitle').textContent=hand.region+' · 手背示範';
  document.getElementById('handSub').textContent='（'+hand.points.length+' 穴，座標目測佔位）';
  var dotEls=hand.points.map(function(p){
    var d=document.createElement('div'); d.className='pt';
    d.style.left=(p.x*100)+'%'; d.style.top=(p.y*100)+'%'; dots.appendChild(d); return d;
  });
  function nearest(mx,my,rect){
    var best=-1,bd=1e9;
    hand.points.forEach(function(p,i){
      var dx=p.x*rect.width-mx, dy=p.y*rect.height-my, dd=dx*dx+dy*dy;
      if(dd<bd){bd=dd;best=i;}
    });
    return best;
  }
  var cur=-1;
  hit.addEventListener('mousemove',function(e){
    var rect=hit.getBoundingClientRect();
    var i=nearest(e.clientX-rect.left,e.clientY-rect.top,rect);
    if(i!==cur){ setHover(i); }
  });
  hit.addEventListener('mouseleave',function(){ setHover(-1); });
  hit.addEventListener('click',function(e){
    var rect=hit.getBoundingClientRect();
    var i=nearest(e.clientX-rect.left,e.clientY-rect.top,rect);
    select(i);
  });
  function setHover(i){
    cur=i;
    dotEls.forEach(function(d,j){ d.classList.toggle('on',j===i); });
    if(i<0){ ptLabel.classList.remove('on'); return; }
    var p=hand.points[i];
    ptLabel.textContent=p.name; ptLabel.style.left=(p.x*100)+'%'; ptLabel.style.top=(p.y*100)+'%';
    ptLabel.classList.add('on');
  }
  function select(i){
    var p=hand.points[i];
    var tags=(p.indications||'').split(/[,，、]/).filter(Boolean).slice(0,10)
      .map(function(t){return '<span>'+t+'</span>';}).join('');
    var link=PURL?('<a class="more" href="'+PURL+encodeURIComponent(p.code)+'" target="_blank" rel="noopener">看完整內容 →</a>')
      :'<span class="more" style="border-color:var(--faint);color:var(--faint)">看完整內容 →（部署後連回穴位頁）</span>';
    panel.innerHTML='<div class="code">'+p.code+'</div><h3>'+p.name+'</h3>'+
      '<div class="field"><div class="t">取穴定位</div><div class="v">'+p.location+'…</div></div>'+
      '<div class="field"><div class="t">主治關鍵字</div><div class="tags">'+tags+'</div></div>'+link;
  }
  function openHand(){ bodyLayer.classList.add('hidden'); handLayer.classList.remove('hidden');
    document.getElementById('title').textContent='二二部位 · 找穴位';
    document.getElementById('sub').textContent='滑到紅點看穴名，點一下看定位與主治；密集區靠「最近點」感應，不必精準對準。'; }
  document.getElementById('backBtn').onclick=function(){
    handLayer.classList.add('hidden'); bodyLayer.classList.remove('hidden');
    document.getElementById('title').textContent='選部位';
    document.getElementById('sub').textContent='滑到部位看穴數，點紅色的「手掌」進入手背示範。此為引擎原型，穴位座標為目測佔位、待醫師校正。';
    setHover(-1); panel.innerHTML='<div class="empty">滑鼠移到手背上的紅點看穴名，點一下看定位與主治。</div>'; };
  // 免責
  document.getElementById('disc').innerHTML=hand.note+
    '　本頁為導航原型、非醫療建議；穴位資料取自資料庫，位置與內容正式上線前須經醫師逐筆確認。';
  // 主題同步
  var root=document.documentElement;
  function sync(){ var t=root.getAttribute('data-theme'); t?atlas.setAttribute('data-theme',t):atlas.removeAttribute('data-theme'); }
  sync(); new MutationObserver(sync).observe(root,{attributes:true,attributeFilter:['data-theme']});
})();
</script>
</div>'''

ROOT = Path(__file__).resolve().parent.parent
g = lambda r, k: (r.get(k) or r.get('﻿' + k) or '').strip()

# 1) 各部位穴數（真實，取自 穴位表.csv）
rows = list(csv.DictReader(open(ROOT / 'data/穴位表.csv')))
counts = collections.Counter(g(r, '部位') for r in rows)

# 2) 手部座標切片（§6 格式）
coord = json.loads((ROOT / 'data/atlas-coords/二二部位.json').read_text())

# 3) 底圖 base64 內嵌
img = (ROOT / coord['base_image']).read_bytes()
img_b64 = 'data:image/png;base64,' + base64.b64encode(img).decode()

# 全身層 13 部位：body 概略座標(相對 0-1，示意佔位) + 是否已可下鑽
REGIONS = [
    ('十十部位', '頭面', 0.50, 0.07, False),
    ('九九部位', '耳朵', 0.585, 0.085, False),
    ('胸腹部位', '胸腹', 0.50, 0.30, False),
    ('十一部位', '背腰', 0.50, 0.44, False),
    ('四四部位', '上臂', 0.30, 0.30, False),
    ('三三部位', '前臂', 0.245, 0.44, False),
    ('二二部位', '手掌', 0.205, 0.57, True),
    ('一一部位', '手指', 0.175, 0.66, False),
    ('八八部位', '大腿', 0.42, 0.66, False),
    ('七七部位', '小腿', 0.40, 0.82, False),
    ('六六部位', '腳掌', 0.385, 0.95, False),
    ('五五部位', '腳趾', 0.45, 0.965, False),
    ('維傑增補穴位', '增補', 0.0, 0.0, False),
]
regions_data = [{'key': k, 'label': lab, 'x': x, 'y': y, 'n': counts.get(k, 0), 'ready': rd}
                for (k, lab, x, y, rd) in REGIONS]

payload = json.dumps({'regions': regions_data, 'hand': coord}, ensure_ascii=False)

# 部署後把穴位頁基底網址填這裡（app.py 用 st.query_params，可 ?point=<穴號>）
POINT_URL_BASE = ''  # e.g. 'https://tungsacu.example/?point='

html = TEMPLATE.replace('__PAYLOAD__', payload).replace('__IMG__', img_b64).replace('__PURL__', POINT_URL_BASE)
out = ROOT / 'atlas/index.html'
out.write_text(html)
print('寫入', out, len(html), 'bytes（含底圖 base64）')
