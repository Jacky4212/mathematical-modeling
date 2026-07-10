/**
 * AI Chat Assistant — 数学建模复习系统
 * Fixed panel on right side, API-key based, with embedded site knowledge base.
 */
(function(){
'use strict';

// ========== CONFIG ==========
var PANEL_WIDTH = 340;
var DEFAULT_MODEL = 'gpt-4o';
var DEFAULT_BASE  = 'https://api.openai.com/v1';

// ========== KNOWLEDGE BASE (系统提示词) ==========
var SYSTEM_PROMPT =
'你是「数学建模复习系统」的AI助教，专门辅导大学生准备数学建模竞赛（国赛CUMCM/美赛MCM）。' +
'你已完整学习了本网站的全部知识点，请基于这些内容回答用户问题。\n\n' +

'## 一、插值与拟合\n' +
'- 插值要求曲线严格经过所有已知数据点；拟合不要求经过所有点，追求整体误差最小。\n' +
'- 选型：数据精确无噪声→插值；数据有噪声→拟合。\n' +
'- MATLAB 1D插值：interp1(x,y,xi,\'method\')，method包括nearest/linear/spline/pchip。\n' +
'- Runge现象：高次多项式插值等距节点时在区间两端产生剧烈振荡。解决方案：分段低次插值(spline/pchip)或Chebyshev节点。\n' +
'- Spline：C²连续的三次样条，光滑但可能过冲；PCHIP：保形分段Hermite，保持单调性，无振荡。\n' +
'- 2D插值：interp2()用于规则网格，griddata()用于散乱数据点。\n' +
'- 最小二乘拟合：min Σ[y_i - f(x_i)]²。多项式拟合用polyfit/polyval。\n' +
'- 非线性拟合：lsqcurvefit(fun,x0,xdata,ydata)，需提供合理初值。\n' +
'- 正规方程：β = (A^T A)^(-1) A^T y，MATLAB中用 A\\y 求解。\n' +
'- MATLAB绘图：plot(x,y,\'选项\')、plot3、mesh、surf、meshgrid生成网格。\n\n' +

'## 二、蒙特卡洛方法(Monte Carlo)\n' +
'- 核心：用随机采样+统计模拟逼近数学量（积分、期望、概率）。\n' +
'- 理论基础：大数定律（依概率收敛）保证一致性；中心极限定理给出误差分布 ~ N(0,1)。\n' +
'- 收敛速率：O(1/√N)，与维数d无关——这是MC在高维问题中的核心竞争力。\n' +
'- 误差：标准误 ≈ σ/√N，95%置信区间 = ±1.96σ/√N。"平方根瓶颈"：精度提高10倍需100倍样本。\n' +
'- MC积分：∫_a^b f(x)dx ≈ (b-a)·(1/N)·Σf(x_i)，x_i~U(a,b)。\n' +
'- 高维积分：维度≥4时MC开始超越确定性格点法。确定性方法受"维度灾难"影响，误差O(N^(-2/d))随d恶化。\n' +
'- 减方差技术：重要性采样(重要区域多采样)、控制变量法(减去已知积分)、对偶变量法(负相关降方差，理想情况减半)、分层采样、QMC(低差异序列Sobol/Halton)。\n' +
'- QMC理论速率约O((ln N)^d/N)，但极高维时ln^d N因子可能抵消优势。\n' +
'- 经典应用：π估计(投点法)、中子屏蔽模拟、叶片面积估计(射线法)、储油罐标定(2010A题)。\n\n' +

'## 三、线性回归\n' +
'- 一元回归：y = a + bx + ε，ε~N(0,σ²)。OLS估计：b = Sxy/Sxx，a = ȳ - b·x̄。\n' +
'- Sxx = Σ(x_i - x̄)²，Sxy = Σ(x_i - x̄)(y_i - ȳ)，Syy = Σ(y_i - ȳ)²。\n' +
'- R² = SSR/SST = 1 - SSE/SST，衡量模型解释的变异比例。调整R²惩罚自变量数量。\n' +
'- 显著性检验：t检验(H₀: b=0)检验单个系数，F检验(H₀: 所有系数=0)检验整体。\n' +
'- 多元回归：Y = Xβ + ε，β̂ = (X^T X)^(-1) X^T Y。\n' +
'- 多重共线性：VIF_j = 1/(1-R_j²)，VIF>10表示严重共线性。解决方案：删除变量、岭回归、主成分回归。\n' +
'- Logistic回归：ln(p/(1-p)) = Xβ，用于二分类问题，参数用极大似然估计。\n' +
'- 逐步回归：前向(逐个加入)/后向(逐个剔除)/双向，但有争议(过度拟合、p值不准确)。替代：LASSO、弹性网。\n' +
'- 灰色预测GM(1,1)：适用于小样本、贫信息系统。白化方程 dx^(1)/dt + ax^(1) = b。\n' +
'- GM(1,1)要求数据呈指数趋势，级比σ(k)∈(e^(-2/(n+1)), e^(2/(n+1)))为合格。\n\n' +

'## 四、AI与数学建模竞赛\n' +
'- 2025年CUMCM首次发布AI使用规范。核心原则：透明、人为主导。\n' +
'- 三条规则：①核心建模必须独立完成；②所有AI使用必须标注(正文+AI使用详情PDF)；③未使用AI须声明。\n' +
'- AI工具须在参考文献以格式列出：[编号]工具名称,版本/型号,开发机构/公司,使用日期。\n' +
'- 四阶段提示工程框架：①问题理解与建模思路；②模型构建与创新设计；③数据处理；④模型求解与深度分析。\n' +
'- PCA用于特征提取与建模，t-SNE/UMAP仅用于可视化（不可作为模型输入）。\n' +
'- 团队分工：建模手(模型设计)、编程手(代码实现)、写作手(论文撰写)。\n' +
'- 74小时时间分配(含提交)：前48h完成模型求解，Day1选题+建模，Day2求解+分析，Day3撰写+修订。\n' +
'- 论文结构：摘要(<=1页,约500-700字)→问题重述→假设→符号说明→模型建立与求解(核心50-60%)→结果分析→评价改进→参考文献→附录。\n' +
'- 表标题在表上方，图标题在图下方。\n\n' +

'## 回答规则\n' +
'1. 优先使用上述知识库内容回答问题，引用具体知识点。\n' +
'2. 当知识库不足以回答时，结合你的通用知识补充，并说明哪些来自知识库、哪些来自通用知识。\n' +
'3. 数学公式请用LaTeX格式($...$或$$...$$)。\n' +
'4. 回答简洁有条理，适合竞赛备考场景。\n' +
'5. 如果用户询问代码，给出MATLAB或Python可运行示例。';

// ========== CSS INJECTION ==========
var CSS = [
'#ai-chat-toggle{transition:right .35s cubic-bezier(.4,0,.2,1)}',
'#ai-chat-toggle:hover{opacity:1!important;box-shadow:-4px 0 16px rgba(0,0,0,.3)!important}',
'#ai-chat-toggle.active{right:'+PANEL_WIDTH+'px!important}',
'#ai-chat-panel{position:fixed;right:-'+(PANEL_WIDTH+10)+'px;top:0;width:'+PANEL_WIDTH+'px;height:100vh;',
  'z-index:140;background:var(--card-bg,#fef9ee);border-left:1px solid var(--card-border,#e5d5b5);',
  'display:flex;flex-direction:column;transition:right .35s cubic-bezier(.4,0,.2,1);',
  'box-shadow:-4px 0 24px rgba(0,0,0,.1)}',
'#ai-chat-panel.open{right:0}',
'#ai-chat-panel .chat-header{display:flex;align-items:center;justify-content:space-between;',
  'padding:14px 16px;border-bottom:1px solid var(--card-border,#e5d5b5);',
  'background:linear-gradient(135deg,#1a3a5c,var(--accent,#2d7fc1));color:#fff;flex-shrink:0}',
'#ai-chat-panel .chat-header .title{font-size:.95em;font-weight:700}',
'#ai-chat-panel .chat-header .close-btn{background:none;border:none;color:#fff;font-size:1.3em;',
  'cursor:pointer;padding:0 4px;line-height:1;opacity:.8;transition:opacity .15s}',
'#ai-chat-panel .chat-header .close-btn:hover{opacity:1}',
'#ai-chat-panel .chat-settings{padding:10px 14px;border-bottom:1px solid var(--divider,#d9c9a0);flex-shrink:0;',
  'font-size:.78em;background:var(--paper-dark,#f3e8d0)}',
'#ai-chat-panel .chat-settings input,#ai-chat-panel .chat-settings select{width:100%;margin:3px 0 6px;',
  'padding:6px 8px;border:1px solid var(--card-border,#e5d5b5);border-radius:4px;',
  'font-size:.85em;background:var(--card-bg,#fef9ee);color:var(--ink,#3d3525);outline:none}',
'#ai-chat-panel .chat-settings label{font-weight:600;color:var(--ink-light,#6b5f48)}',
'#ai-chat-panel .chat-settings .save-btn{padding:6px 14px;background:var(--accent,#2d7fc1);color:#fff;',
  'border:none;border-radius:4px;cursor:pointer;font-size:.82em;font-weight:600;transition:opacity .15s}',
'#ai-chat-panel .chat-settings .save-btn:hover{opacity:.85}',
'#ai-chat-panel .chat-settings .row{display:flex;gap:8px;align-items:center}',
'#ai-chat-panel .chat-msgs{flex:1;overflow-y:auto;padding:12px 14px;display:flex;flex-direction:column;gap:10px}',
'#ai-chat-panel .chat-msgs .msg{max-width:92%;padding:8px 12px;border-radius:8px;font-size:.85em;',
  'line-height:1.6;word-break:break-word;animation:fadeIn .2s ease}',
'@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}',
'#ai-chat-panel .chat-msgs .msg.user{align-self:flex-end;background:var(--accent,#2d7fc1);color:#fff}',
'#ai-chat-panel .chat-msgs .msg.assistant{align-self:flex-start;background:var(--code-bg,#ede0c5);',
  'color:var(--ink,#3d3525)}',
'#ai-chat-panel .chat-msgs .msg.assistant p{margin:4px 0}',
'#ai-chat-panel .chat-input-wrap{display:flex;gap:6px;padding:10px 14px;border-top:1px solid var(--divider,#d9c9a0);',
  'flex-shrink:0}',
'#ai-chat-panel .chat-input-wrap textarea{flex:1;padding:8px 10px;border:1px solid var(--card-border,#e5d5b5);',
  'border-radius:6px;resize:none;font-size:.85em;line-height:1.5;outline:none;',
  'background:var(--card-bg,#fef9ee);color:var(--ink,#3d3525);max-height:80px}',
'#ai-chat-panel .chat-input-wrap button{padding:8px 14px;background:var(--accent,#2d7fc1);color:#fff;',
  'border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:.85em;transition:opacity .15s;',
  'align-self:flex-end;white-space:nowrap}',
'#ai-chat-panel .chat-input-wrap button:hover{opacity:.85}',
'#ai-chat-panel .chat-input-wrap button:disabled{opacity:.5;cursor:not-allowed}',
'#ai-chat-panel .typing{color:var(--ink-light,#6b5f48);font-size:.8em;padding:4px 12px;font-style:italic}',
'@media print{#ai-chat-toggle,#ai-chat-panel{display:none}}',
'@media(max-width:768px){#ai-chat-toggle{top:auto;bottom:80px}#ai-chat-panel{width:100vw;right:-110vw}',
  '#ai-chat-panel.open{right:0}}',
'body.ai-chat-open .main-wrap{margin-right:'+PANEL_WIDTH+'px}',
'@media(max-width:768px){body.ai-chat-open .main-wrap{margin-right:0}}'
].join('\n');

// ========== HTML INJECTION ==========
var HTML = [
'<div id="ai-chat-panel">',
'  <div class="chat-header">',
'    <span class="title">🤖 AI 学习助手</span>',
'    <button class="close-btn" id="chat-close">×</button>',
'  </div>',
'  <div class="chat-settings" id="chat-settings">',
'    <label>API Key <span style="font-weight:400;font-size:.85em;color:var(--ink-light)">🔒 仅存你本地</span></label>',
'    <input type="password" id="api-key" placeholder="sk-...">',
'    <label>Base URL <span style="font-weight:400;font-size:.9em">(默认 OpenAI)</span></label>',
'    <input type="text" id="api-base" placeholder="'+DEFAULT_BASE+'">',
'    <div class="row">',
'      <input type="text" id="api-model" placeholder="模型: '+DEFAULT_MODEL+'" style="flex:1;margin:3px 0">',
'      '<button class="save-btn" id="save-config">保存</button>',
'      <button class="save-btn" id="clear-config" style="background:#888">清除</button>',
'    </div>',
'    <p style="margin:6px 0 0;font-size:.75em;color:var(--ink-light)">',
'    🔒 Key仅保存在你浏览器本地，其他用户看不到也无法使用。</p>',
'  </div>',
'  <div class="chat-msgs" id="chat-msgs">',
'    <div class="msg assistant">👋 你好！我是数学建模AI助教，已学习本网站全部知识点（插值与拟合、蒙特卡洛、线性回归、AI与建模竞赛策略）。<br><br>请先输入你的 API Key 并保存，然后开始提问。</div>',
'  </div>',
'  <div class="chat-input-wrap">',
'    <textarea id="chat-input" rows="1" placeholder="输入问题，回车发送..." onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();document.getElementById(\'chat-send\').click()}"></textarea>',
'    '<button id="chat-send">发送</button>',
'  </div>',
'</div>'
].join('\n');

// ========== DOM INIT ==========
var styleEl = document.createElement('style');
styleEl.textContent = CSS;
document.head.appendChild(styleEl);

var div = document.createElement('div');
div.innerHTML = HTML;
document.body.appendChild(div);

// ========== STATE ==========
var isOpen = false;
var isBusy = false;
var apiKey  = localStorage.getItem('ai-chat-key')  || '';
var apiBase = localStorage.getItem('ai-chat-base') || '';
var apiModel= localStorage.getItem('ai-chat-model')|| '';

// ========== DOM REFS ==========
var toggleBtn  = document.getElementById('ai-chat-toggle');
var panel      = document.getElementById('ai-chat-panel');
var closeBtn   = document.getElementById('chat-close');
var msgsEl     = document.getElementById('chat-msgs');
var inputEl    = document.getElementById('chat-input');
var sendBtn    = document.getElementById('chat-send');
var keyInput   = document.getElementById('api-key');
var baseInput  = document.getElementById('api-base');
var modelInput = document.getElementById('api-model');
var saveBtn    = document.getElementById('save-config');
var clearBtn   = document.getElementById('clear-config');

// Init inputs
keyInput.value   = apiKey;
baseInput.value  = apiBase;
modelInput.value = apiModel;

// ========== TOGGLE ==========
function openPanel(){
  isOpen = true;
  panel.classList.add('open');
  toggleBtn.classList.add('active');
  document.body.classList.add('ai-chat-open');
  setTimeout(function(){ inputEl.focus(); }, 400);
}
function closePanel(){
  isOpen = false;
  panel.classList.remove('open');
  toggleBtn.classList.remove('active');
  document.body.classList.remove('ai-chat-open');
}
// Toggle handled by inline onclick on #ai-chat-toggle in HTML
toggleBtn.addEventListener('click', function(){
  isOpen = !isOpen;
  if(isOpen){ setTimeout(function(){ inputEl.focus(); }, 400); }
});
closeBtn.addEventListener('click', function(){ closePanel(); });

// Close on Escape
document.addEventListener('keydown', function(e){
  if(e.key === 'Escape' && panel.classList.contains('open')){ closePanel(); }
});

// Close on click outside
document.addEventListener('click', function(e){
  if(panel.classList.contains('open') && !panel.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)){
    closePanel();
  }
});

// ========== SAVE / CLEAR CONFIG ==========
saveBtn.addEventListener('click', function(){
  apiKey  = keyInput.value.trim();
  apiBase = baseInput.value.trim();
  apiModel= modelInput.value.trim();
  localStorage.setItem('ai-chat-key',  apiKey);
  localStorage.setItem('ai-chat-base', apiBase);
  localStorage.setItem('ai-chat-model',apiModel);
  addMsg('assistant', '✅ 配置已保存！现在可以向我提问了。');
});
clearBtn.addEventListener('click', function(){
  apiKey=''; apiBase=''; apiModel='';
  keyInput.value=''; baseInput.value=''; modelInput.value='';
  localStorage.removeItem('ai-chat-key');
  localStorage.removeItem('ai-chat-base');
  localStorage.removeItem('ai-chat-model');
  addMsg('assistant', '🗑️ 配置已清除。');
});

// ========== CHAT ==========
function addMsg(role, text){
  var el = document.createElement('div');
  el.className = 'msg ' + role;
  el.innerHTML = text.replace(/\n/g, '<br>');
  msgsEl.appendChild(el);
  msgsEl.scrollTop = msgsEl.scrollHeight;
}

function setTyping(show){
  var el = document.getElementById('typing-indicator');
  if(show && !el){
    el = document.createElement('div');
    el.id = 'typing-indicator';
    el.className = 'typing';
    el.textContent = 'AI 正在思考...';
    msgsEl.appendChild(el);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  } else if(!show && el){
    el.remove();
  }
}

function buildMessages(userMsg){
  return [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user',   content: userMsg }
  ];
}

function streamResponse(messages){
  setTyping(true);
  isBusy = true;
  sendBtn.disabled = true;

  var base  = apiBase  || DEFAULT_BASE;
  var model = apiModel || DEFAULT_MODEL;
  var url   = base.replace(/\/+$/, '') + '/chat/completions';

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + apiKey
    },
    body: JSON.stringify({
      model: model,
      messages: messages,
      stream: true,
      temperature: 0.7,
      max_tokens: 4096
    })
  }).then(function(res){
    if(!res.ok){
      return res.json().then(function(e){
        throw new Error('API错误 ' + res.status + ': ' + (e.error ? e.error.message : '请检查API Key和Base URL'));
      });
    }
    // Streaming
    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var msgEl = document.createElement('div');
    msgEl.className = 'msg assistant';
    msgsEl.appendChild(msgEl);
    setTyping(false);

    function read(){
      reader.read().then(function(result){
        if(result.done){
          isBusy = false;
          sendBtn.disabled = false;
          msgsEl.scrollTop = msgsEl.scrollHeight;
          return;
        }
        var chunk = decoder.decode(result.value, {stream: true});
        var lines = chunk.split('\n');
        for(var i = 0; i < lines.length; i++){
          var line = lines[i].trim();
          if(!line || !line.startsWith('data: ')) continue;
          var data = line.slice(6);
          if(data === '[DONE]') continue;
          try {
            var json = JSON.parse(data);
            var delta = json.choices && json.choices[0] && json.choices[0].delta;
            if(delta && delta.content){
              msgEl.textContent += delta.content;
              msgsEl.scrollTop = msgsEl.scrollHeight;
            }
          } catch(e){ /* skip malformed */ }
        }
        read();
      }).catch(function(e){
        if(!msgEl.textContent) msgEl.textContent = '❌ 读取响应失败: ' + e.message;
        isBusy = false;
        sendBtn.disabled = false;
      });
    }
    read();
  }).catch(function(e){
    setTyping(false);
    addMsg('assistant', '❌ 请求失败: ' + e.message + '\n\n请检查：\n1. API Key 是否正确\n2. Base URL 是否正确\n3. 网络连接是否正常\n4. 账户是否有可用额度');
    isBusy = false;
    sendBtn.disabled = false;
  });
}

function sendMsg(){
  if(isBusy) return;
  var text = inputEl.value.trim();
  if(!text) return;

  if(!apiKey){
    addMsg('assistant', '⚠️ 请先在上方输入 API Key 并点击"保存"。');
    return;
  }

  addMsg('user', text);
  inputEl.value = '';
  inputEl.style.height = 'auto';

  var messages = buildMessages(text);
  streamResponse(messages);
}

sendBtn.addEventListener('click', sendMsg);

// Auto-resize textarea
inputEl.addEventListener('input', function(){
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 80) + 'px';
});

// ========== DARK MODE SYNC ==========
// Panel uses CSS variables so it auto-adapts to dark mode — no extra code needed.

})();
