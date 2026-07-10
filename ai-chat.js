/**
 * AI Chat — 数学建模复习系统
 * Single-file injector: CSS + HTML + Logic. Ref: simple-chat-ui pattern.
 */
(function(){
'use strict';

// ===== SYSTEM PROMPT (全站知识库) =====
var SYS = '你是数学建模复习系统的AI助教，已学完本网站所有知识点：\n'+
'一、插值与拟合：插值过所有点/拟合求最小误差/Runge现象/spline vs pchip/interp1 interp2 griddata/polyfit lsqcurvefit/正规方程β=(A^TA)^-1A^Ty\n'+
'二、蒙特卡洛：LLN+CLT/误差O(1/√N)/95%CI=±1.96σ/√N/维度无关/重要采样控制变量对偶变量分层采样QMC/π估计中子屏蔽叶片面积储油罐\n'+
'三、线性回归：OLS b=Sxy/Sxx/R²=1-SSE/SST/调整R²/t检验F检验/多元Y=Xβ+ε/Logistic ln(p/(1-p))=Xβ/逐步回归/VIF/GM(1,1)\n'+
'四、AI竞赛：CUMCM2025透明人为主导/三规则/四阶段提示工程/PCA建模tSNE可视化/团队分工/74h含提交/摘要≤1页/表标题上 图标题下\n'+
'规则：优先用知识库/公式用LaTeX/回答简洁/可给MATLAB或Python代码';

// ===== CSS =====
var CSS =
'#ai-btn{position:fixed;right:0;top:calc(50% + 80px);z-index:145;background:linear-gradient(135deg,#1a3a5c,var(--accent,#2d7fc1));color:#fff;border:none;border-radius:8px 0 0 8px;padding:10px 14px;font-family:var(--font);font-size:.82em;cursor:pointer;font-weight:600;opacity:.8;box-shadow:-2px 0 10px rgba(0,0,0,.15);transition:all .25s}'+
'#ai-btn:hover{opacity:1}'+
'#ai-panel{display:none;position:fixed;right:0;top:0;width:360px;height:100vh;z-index:146;flex-direction:column;background:var(--card-bg,#fef9ee);border-left:1px solid var(--card-border,#e5d5b5);box-shadow:-4px 0 24px rgba(0,0,0,.12);font-family:var(--font)}'+
'#ai-panel.show{display:flex}'+
'#ai-panel .hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:linear-gradient(135deg,#1a3a5c,var(--accent,#2d7fc1));color:#fff;flex-shrink:0}'+
'#ai-panel .hdr span{font-size:.95em;font-weight:700}'+
'#ai-panel .hdr .close-btn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:.82em;cursor:pointer;padding:5px 12px;border-radius:4px;font-weight:600;transition:background .15s}'+
'#ai-panel .hdr .close-btn:hover{background:rgba(255,255,255,.3)}'+
'#ai-panel .cfg{padding:14px 16px;border-bottom:1px solid var(--divider,#d9c9a0);flex-shrink:0;font-size:.82em;background:var(--paper-dark,#f3e8d0)}'+
'#ai-panel .cfg label{display:block;font-weight:600;color:var(--ink-light,#6b5f48);margin-top:6px;font-size:.9em}'+
'#ai-panel .cfg label:first-child{margin-top:0}'+
'#ai-panel .cfg input{width:100%;margin:3px 0 8px;padding:7px 8px;border:1px solid var(--card-border,#e5d5b5);border-radius:4px;font-size:.9em;background:var(--card-bg,#fef9ee);color:var(--ink,#3d3525);outline:none}'+
'#ai-panel .cfg .btns{display:flex;gap:8px;margin-top:4px}'+
'#ai-panel .cfg .btns button{padding:6px 16px;border:none;border-radius:4px;cursor:pointer;font-size:.85em;font-weight:600;color:#fff}'+
'#ai-panel .cfg .btns .save{background:var(--accent,#2d7fc1)}'+
'#ai-panel .cfg .btns .clear{background:#888}'+
'#ai-panel .cfg .note{margin-top:6px;font-size:.75em;color:var(--ink-light,#6b5f48)}'+
'#ai-panel .msgs{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px}'+
'#ai-panel .msgs .m{max-width:90%;padding:8px 12px;border-radius:8px;font-size:.85em;line-height:1.6;word-break:break-word}'+
'#ai-panel .msgs .m.u{align-self:flex-end;background:var(--accent,#2d7fc1);color:#fff}'+
'#ai-panel .msgs .m.a{align-self:flex-start;background:var(--code-bg,#ede0c5);color:var(--ink,#3d3525)}'+
'#ai-panel .msgs .typing{color:var(--ink-light);font-size:.8em;padding:4px 2px;font-style:italic}'+
'#ai-panel .inp{display:flex;gap:6px;padding:10px 14px;border-top:1px solid var(--divider,#d9c9a0);flex-shrink:0}'+
'#ai-panel .inp textarea{flex:1;padding:8px 10px;border:1px solid var(--card-border,#e5d5b5);border-radius:6px;resize:none;font-size:.85em;line-height:1.5;background:var(--card-bg,#fef9ee);color:var(--ink,#3d3525);outline:none;max-height:80px;font-family:inherit}'+
'#ai-panel .inp button{padding:8px 16px;background:var(--accent,#2d7fc1);color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:.85em;white-space:nowrap}'+
'#ai-panel .inp button:disabled{opacity:.5}'+
'@media print{#ai-btn,#ai-panel{display:none!important}}'+
'@media(max-width:768px){#ai-panel{width:100vw}#ai-btn{top:auto;bottom:80px}}';

// ===== HTML =====
var HTML =
'<button id="ai-btn">AI</button>'+
'<div id="ai-panel">'+
'<div class="hdr"><span>🤖 AI 学习助手</span><button class="close-btn" id="ai-close">关闭</button></div>'+
'<div class="cfg" id="ai-cfg">'+
'<label>API Key <span style="font-weight:400">🔒 仅存你本地</span></label>'+
'<input type="password" id="ai-key" placeholder="sk-...">'+
'<label>Base URL</label>'+
'<input type="text" id="ai-base" placeholder="https://api.openai.com/v1">'+
'<label>Model</label>'+
'<input type="text" id="ai-model" placeholder="gpt-4o">'+
'<div class="btns"><button class="save" id="ai-save">保存配置</button><button class="clear" id="ai-clear">清除</button></div>'+
'<p class="note">🔒 Key仅保存在你浏览器本地，其他用户无法看到或使用。</p>'+
'</div>'+
'<div class="msgs" id="ai-msgs"><div class="m a">👋 你好！我是数学建模AI助教。<br><br>请先在设置区输入 API Key 并保存，然后开始提问。</div></div>'+
'<div class="inp"><textarea id="ai-input" rows="1" placeholder="输入问题，Enter发送..."></textarea><button id="ai-send">发送</button></div>'+
'</div>';

// ===== INJECT =====
var style = document.createElement('style');
style.textContent = CSS;
document.head.appendChild(style);
var wrap = document.createElement('div');
wrap.innerHTML = HTML;
document.body.appendChild(wrap);

// ===== DOM REFS =====
var btn   = document.getElementById('ai-btn');
var panel = document.getElementById('ai-panel');
var close = document.getElementById('ai-close');
var msgs  = document.getElementById('ai-msgs');
var input = document.getElementById('ai-input');
var send  = document.getElementById('ai-send');
var keyEl = document.getElementById('ai-key');
var baseEl= document.getElementById('ai-base');
var modelEl=document.getElementById('ai-model');
var saveBtn=document.getElementById('ai-save');
var clearBtn=document.getElementById('ai-clear');

// ===== STATE =====
var busy = false;
var cfg = {};
try{ cfg = JSON.parse(localStorage.getItem('ai-cfg')||'{}'); }catch(e){}
if(!cfg.base) cfg.base = 'https://api.openai.com/v1';
if(!cfg.model) cfg.model = 'gpt-4o';
keyEl.value = cfg.key || '';
baseEl.value = cfg.base;
modelEl.value = cfg.model;

// ===== TOGGLE =====
function openPanel(){
  panel.style.display = 'flex';
  btn.style.display = 'none';
  setTimeout(function(){ input.focus(); }, 300);
}
function closePanel(){
  panel.style.display = 'none';
  btn.style.display = '';
}
btn.onclick = function(){
  if(panel.style.display === 'flex') closePanel(); else openPanel();
};
close.onclick = closePanel;
document.addEventListener('keydown', function(e){
  if(e.key === 'Escape' && panel.style.display === 'flex') closePanel();
});

// ===== SAVE / CLEAR =====
saveBtn.onclick = function(){
  cfg.key   = keyEl.value.trim();
  cfg.base  = baseEl.value.trim() || 'https://api.openai.com/v1';
  cfg.model = modelEl.value.trim() || 'gpt-4o';
  localStorage.setItem('ai-cfg', JSON.stringify(cfg));
  addMsg('a', '✅ 配置已保存！现在可以向我提问了。');
};
clearBtn.onclick = function(){
  cfg = {base:'https://api.openai.com/v1',model:'gpt-4o'};
  keyEl.value = ''; baseEl.value = cfg.base; modelEl.value = cfg.model;
  localStorage.removeItem('ai-cfg');
  addMsg('a', '🗑️ 配置已清除。');
};

// ===== CHAT =====
function addMsg(role, text){
  var el = document.createElement('div');
  el.className = 'm ' + role;
  el.innerHTML = text.replace(/\n/g,'<br>');
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function doSend(){
  if(busy) return;
  var txt = input.value.trim();
  if(!txt) return;
  if(!cfg.key){ addMsg('a','⚠️ 请先输入 API Key 并点击"保存配置"。'); return; }
  addMsg('u', txt);
  input.value = ''; input.style.height = 'auto';
  busy = true; send.disabled = true;

  // Typing indicator
  var typing = document.createElement('div');
  typing.className = 'typing'; typing.textContent = 'AI 思考中...';
  msgs.appendChild(typing); msgs.scrollTop = msgs.scrollHeight;

  var url = cfg.base.replace(/\/+$/,'') + '/chat/completions';
  fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json','Authorization':'Bearer '+cfg.key},
    body: JSON.stringify({
      model: cfg.model,
      messages: [{role:'system',content:SYS},{role:'user',content:txt}],
      stream: true,
      temperature: 0.7,
      max_tokens: 4096
    })
  }).then(function(res){
    if(!res.ok){
      return res.text().then(function(body){
        var msg = body;
        try{ var j=JSON.parse(body); msg=j.error?j.error.message:body; }catch(e){}
        throw new Error('HTTP '+res.status+': '+msg);
      });
    }
    typing.remove();
    var msgEl = document.createElement('div');
    msgEl.className = 'm a'; msgs.appendChild(msgEl);
    msgs.scrollTop = msgs.scrollHeight;

    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var buf = '';
    function read(){
      reader.read().then(function(r){
        if(r.done){ busy=false; send.disabled=false; return; }
        buf += decoder.decode(r.value, {stream:true});
        var lines = buf.split('\n'); buf = lines.pop() || '';
        for(var i=0; i<lines.length; i++){
          var line = lines[i].trim();
          if(!line || !line.startsWith('data: ')) continue;
          var d = line.slice(6);
          if(d === '[DONE]') continue;
          try{
            var j = JSON.parse(d);
            var c = j.choices&&j.choices[0]&&j.choices[0].delta&&j.choices[0].delta.content;
            if(c){ msgEl.textContent += c; msgs.scrollTop = msgs.scrollHeight; }
          }catch(e){}
        }
        read();
      }).catch(function(e){
        if(!msgEl.textContent) msgEl.textContent = '⚠️ 读取中断: '+e.message;
        busy=false; send.disabled=false;
      });
    }
    read();
  }).catch(function(e){
    typing.remove();
    var errMsg = e.message || e.toString();
    if(errMsg.indexOf('Failed to fetch')>=0 || errMsg.indexOf('NetworkError')>=0){
      addMsg('a','❌ 网络请求失败\n\n可能原因：\n1. Base URL 不可达\n2. 浏览器或网络阻止了请求（CORS）\n3. 请检查URL格式是否正确');
    } else {
      addMsg('a','❌ '+errMsg);
    }
    busy=false; send.disabled=false;
  });
}

send.onclick = doSend;
input.onkeydown = function(e){
  if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); doSend(); }
};
input.oninput = function(){
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 80) + 'px';
};

})();
