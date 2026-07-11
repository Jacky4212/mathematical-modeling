/**
 * AI Chat — 数学建模复习系统
 * Single-file injector: CSS + HTML + Logic. Ref: simple-chat-ui pattern.
 */
(function(){
'use strict';

// ===== SYSTEM PROMPT =====
// Base role instruction. When RAG is active, knowledge chunks are appended dynamically.
var SYS_BASE =
'你是"数学建模复习系统"的AI助教。你的知识覆盖数学建模的四大领域：\n'+
'（1）综合评价方法（AHP/TOPSIS/熵值法/CRITIC/模糊评价/灰色关联/DEA/RSR/耦合协调度/PCA等）\n'+
'（2）预测方法（GM(1,1)/ARIMA/SARIMA/GARCH/VAR/马尔可夫/Logistic/DID/PSM/BP神经网络/集成学习等）\n'+
'（3）优化规划方法（单纯形法/内点法/分支定界/动态规划/GA/PSO/模拟退火/蒙特卡洛/图论优化等）\n'+
'（4）统计与机器学习（相关分析/T检验/ANOVA/卡方检验/线性回归/Ridge/Lasso/逻辑回归/聚类/决策树/SVM/KNN/朴素贝叶斯/信效度分析/中介效应等）\n'+
'\n'+
'回答规范：\n'+
'- 数学公式使用LaTeX格式（行内$...$，块级$$...$$）\n'+
'- 优先给出Python代码示例（使用numpy/scipy/sklearn/statsmodels）\n'+
'- 每种方法说明：适用场景、关键假设、优缺点\n'+
'- 回答简洁准确，必要时列出对比表格\n'+
'- 如果问题涉及模型选择，给出推荐理由和备选方案';

// Fallback SYS when RAG is not available (includes condensed knowledge)
var SYS = SYS_BASE;

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
'#ai-panel .msgs .m.a h3,#ai-panel .msgs .m.a h4{margin:8px 0 4px;font-size:.95em}'+
'#ai-panel .msgs .m.a pre{background:#2d2a26;color:#ece6da;padding:10px 12px;border-radius:4px;overflow-x:auto;margin:6px 0;font-size:.82em;line-height:1.5}'+
'#ai-panel .msgs .m.a pre code{background:none;color:inherit;padding:0;font-size:1em}'+
'#ai-panel .msgs .m.a code{font-family:"Cascadia Code","JetBrains Mono","Consolas",monospace;font-size:.85em;background:rgba(0,0,0,.08);padding:1px 5px;border-radius:3px}'+
'#ai-panel .msgs .m.a ul{margin:4px 0;padding-left:18px}'+
'#ai-panel .msgs .m.a li{margin:2px 0}'+
'#ai-panel .msgs .m.a blockquote{border-left:3px solid var(--accent,#2d7fc1);margin:6px 0;padding:4px 10px;font-size:.9em;opacity:.85}'+
'#ai-panel .msgs .m.a hr{border:none;border-top:1px solid var(--divider,#d9c9a0);margin:8px 0}'+
'#ai-panel .msgs .m.a table{border-collapse:collapse;width:100%;margin:8px 0;font-size:.82em}'+
'#ai-panel .msgs .m.a th,#ai-panel .msgs .m.a td{border:1px solid var(--card-border,#e5d5b5);padding:6px 10px;text-align:left}'+
'#ai-panel .msgs .m.a th{background:var(--paper-dark,#f3e8d0);font-weight:600}'+
'#ai-panel .msgs .m.a td{background:var(--card-bg,#fef9ee)}'+
'#ai-panel .msgs .m.a p{margin:4px 0}'+
'#ai-panel .msgs .typing{color:var(--ink-light);font-size:.8em;padding:4px 2px;font-style:italic}'+
'#ai-panel .inp{display:flex;gap:6px;padding:10px 14px;border-top:1px solid var(--divider,#d9c9a0);flex-shrink:0}'+
'#ai-panel .inp textarea{flex:1;padding:8px 10px;border:1px solid var(--card-border,#e5d5b5);border-radius:6px;resize:none;font-size:.85em;line-height:1.5;background:var(--card-bg,#fef9ee);color:var(--ink,#3d3525);outline:none;max-height:80px;font-family:inherit}'+
'#ai-panel .inp button{padding:8px 16px;background:var(--accent,#2d7fc1);color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:.85em;white-space:nowrap}'+
'#ai-panel .inp button:disabled{opacity:.5}'+
'.dark-mode #ai-panel .msgs .m.a code{background:rgba(255,255,255,.1)}'+
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
var chatHistory = [];  // conversation memory: [{role, content}, ...]
var cfg = {};
try{ cfg = JSON.parse(localStorage.getItem('ai-cfg')||'{}'); }catch(e){}
if(!cfg.base) cfg.base = 'https://api.openai.com/v1';
if(!cfg.model) cfg.model = 'gpt-4o';
keyEl.value = cfg.key || '';
baseEl.value = cfg.base;
modelEl.value = cfg.model;

// ===== RAG INIT =====
var ragReady = false;
(function initRAG(){
  if(typeof RAGRetriever === 'undefined'){
    console.log('[AI Chat] RAGRetriever not found, running without knowledge base');
    return;
  }
  RAGRetriever.init('knowledge-chunks.json?v=1').then(function(){
    ragReady = true;
    console.log('[AI Chat] RAG ready — '+RAGRetriever.getChunkCount()+' chunks');
  }).catch(function(e){
    console.warn('[AI Chat] RAG init failed:', e.message);
  });
})();

// ===== TOGGLE =====
var themeBtn = document.querySelector('.theme-toggle');
function openPanel(){
  panel.style.display = 'flex';
  btn.style.display = 'none';
  if(themeBtn) themeBtn.style.display = 'none';
  setTimeout(function(){ input.focus(); }, 300);
}
function closePanel(){
  panel.style.display = 'none';
  btn.style.display = '';
  if(themeBtn) themeBtn.style.display = '';
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
  el.innerHTML = renderMD(text);
  msgs.appendChild(el);
  if(window.MathJax && MathJax.typesetPromise){
    MathJax.typesetPromise([el]).catch(function(){});
  }
  msgs.scrollTop = msgs.scrollHeight;
}

function renderMD(t){
  var blocks = [];
  var B = '\x00B'; // placeholder prefix

  // 1) Save code blocks first (before math, so $ inside code is preserved)
  t = t.replace(/```(\w*)\n([\s\S]*?)```/g, function(_, lang, code){
    blocks.push({type:'code', html:'<pre><code>' +
      code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n$/,'') +
      '</code></pre>'});
    return B + (blocks.length-1) + B;
  });

  // 2) Save LaTeX math blocks
  // Display math: $$ ... $$
  t = t.replace(/\$\$([\s\S]*?)\$\$/g, function(_, math){
    blocks.push({type:'math', html:'<span class="math display">$$' + math + '$$</span>'});
    return B + (blocks.length-1) + B;
  });
  // Inline math: $...$ (won't match inside code blocks — already saved)
  t = t.replace(/\$(.+?)\$/g, function(_, math){
    blocks.push({type:'math', html:'<span class="math inline">$' + math + '$</span>'});
    return B + (blocks.length-1) + B;
  });

  // 3) Fix broken table rows: newlines inside cells break GFM table parsing
  //    Strategy: if a line starts with | but doesn't end with |, keep joining
  //    subsequent lines until we get a | at line end.
  var lines = t.split('\n');
  var merged = [];
  var buf = '';
  for(var i = 0; i < lines.length; i++){
    var line = lines[i];
    if(buf){
      // We're inside a broken table row — accumulate until line ends with |
      buf += ' ' + line;
      if(/\|$/.test(line)){
        merged.push(buf);
        buf = '';
      }
    } else if(/^\|.*[^|]$/.test(line)){
      // Table row starts with | but doesn't end with | → start accumulating
      buf = line;
    } else {
      merged.push(line);
    }
  }
  if(buf) merged.push(buf);  // safety: flush any unclosed buffer
  t = merged.join('\n');

  // 4) Normalize whitespace: collapse 3+ blank lines, trim line ends
  t = t.replace(/[ \t]+$/gm, '');      // trim trailing spaces per line
  t = t.replace(/\n{3,}/g, '\n\n');    // collapse excessive blank lines

  // 5) Use marked.js for full GFM markdown → HTML
  var html;
  if(typeof marked !== 'undefined' && marked.parse){
    html = marked.parse(t, {gfm: true, breaks: true});
  } else {
    html = t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }

  // 4) Restore all saved blocks (code + math)
  html = html.replace(new RegExp(B + '(\\d+)' + B, 'g'), function(_, i){
    return blocks[parseInt(i)].html;
  });

  return html;
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

  // ===== RAG RETRIEVAL =====
  var ragContext = '';
  if(ragReady && typeof RAGRetriever !== 'undefined'){
    var results = RAGRetriever.retrieve(txt, 3);
    if(results.length > 0){
      ragContext = RAGRetriever.buildContext(results, 1500);
      // Show retrieval indicator
      typing.textContent = '📚 检索到 ' + results.length + ' 条相关知识，AI 思考中...';
      // Add source note (collapsed)
      var srcNote = '📚 **已检索相关知识库** (' + results.length + '条匹配)\n';
      var topKw = [];
      for(var ri=0; ri<Math.min(results.length,3); ri++){
        if(results[ri].matchedKeywords.length > 0){
          topKw = topKw.concat(results[ri].matchedKeywords.slice(0,3));
        }
      }
      if(topKw.length > 0){
        srcNote += '> 匹配关键词：' + topKw.slice(0,6).join('、') + '\n';
      }
      srcNote += '> 来源：' + results.map(function(r){return r.chunk.title;}).slice(0,3).join('、');
      // Add a small source indicator message
      var srcEl = document.createElement('div');
      srcEl.className = 'm a';
      srcEl.innerHTML = renderMD(srcNote);
      srcEl.style.fontSize = '0.8em';
      srcEl.style.opacity = '0.75';
      msgs.insertBefore(srcEl, typing);
      msgs.scrollTop = msgs.scrollHeight;
    }
  }

  // Build messages: system + history + current user msg
  var systemMsg = SYS;
  if(ragContext){
    systemMsg = SYS + '\n\n' + ragContext + '\n\n请基于以上内部知识库内容回答用户问题。如果知识库中有相关信息，优先使用知识库中的内容；如果知识库中没有相关信息，可以使用你自己的知识。';
  }
  var messages = [{role:'system', content:systemMsg}];
  // Append recent history (last 30 messages = 15 exchanges, avoid token bloat)
  var recentHistory = chatHistory.slice(-30);
  messages = messages.concat(recentHistory);
  messages.push({role:'user', content:txt});

  var url = cfg.base.replace(/\/+$/,'') + '/chat/completions';
  fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json','Authorization':'Bearer '+cfg.key},
    body: JSON.stringify({
      model: cfg.model,
      messages: messages,
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
    var rawText = '';

    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var buf = '';
    function read(){
      reader.read().then(function(r){
        if(r.done){
          // Stream done — render accumulated text
          msgEl.innerHTML = renderMD(rawText);
          // Re-render LaTeX with MathJax
          if(window.MathJax && MathJax.typesetPromise){
            MathJax.typesetPromise([msgEl]).catch(function(){});
          }
          msgs.scrollTop = msgs.scrollHeight;
          // Save to conversation history
          chatHistory.push({role:'user', content:txt});
          chatHistory.push({role:'assistant', content:rawText});
          // Limit history to last 40 messages (20 exchanges)
          if(chatHistory.length > 40) chatHistory = chatHistory.slice(-40);
          busy=false; send.disabled=false; return;
        }
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
            if(c){
              rawText += c;
              // Show raw text during streaming (no markdown yet — avoids broken partial render)
              msgEl.textContent = rawText;
              msgs.scrollTop = msgs.scrollHeight;
            }
          }catch(e){}
        }
        read();
      }).catch(function(e){
        if(!rawText) msgEl.innerHTML = '⚠️ 读取中断: '+e.message;
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
