/**
 * 数学建模学习平台 — 公共脚本
 * 主题切换 / 侧边栏高亮 / 章节导航 / 缓存刷新
 */
(function(){
'use strict';

// ===== Cache buster (silent update — no forced reload) =====
var VERSION = '250721a';
if(localStorage.getItem('mm-ver') !== VERSION){
  localStorage.setItem('mm-ver', VERSION);
  // Clear old cache keys if any, but don't force reload
  console.log('[数学建模] 资源版本已更新至 ' + VERSION);
}

// ===== Sidebar current-page highlight =====
(function(){
  var p = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-nav a, .sidebar-nav .sub-link').forEach(function(a){
    if(a.getAttribute('href') === p) a.classList.add('current');
  });
})();

// ===== Theme toggle =====
(function(){
  var themeKey = 'mathmodel-theme';
  var d = localStorage.getItem(themeKey);
  if(d === 'dark'){
    document.body.classList.add('dark-mode');
    var btn = document.querySelector('.theme-toggle');
    if(btn) btn.textContent = '☀️';
  }

  window.toggleTheme = function(){
    var b = document.body;
    var btn = document.querySelector('.theme-toggle');
    b.classList.toggle('dark-mode');
    var isDark = b.classList.contains('dark-mode');
    if(btn) btn.textContent = isDark ? '☀️' : '🌙';
    localStorage.setItem(themeKey, isDark ? 'dark' : 'light');
  };
})();

// ===== Chapter nav panel =====
window.toggleChapterNav = function(){
  var panel = document.getElementById('chapterNav');
  if(panel) panel.classList.toggle('open');
};

// Click outside to close
document.addEventListener('click', function(e){
  var panel = document.getElementById('chapterNav');
  var btn = document.querySelector('.chapter-nav-toggle');
  if(panel && panel.classList.contains('open') && !panel.contains(e.target) && !btn.contains(e.target)){
    panel.classList.remove('open');
  }
});

/**
 * Auto-generate chapter-nav-panel content if the container is empty.
 * Pages with custom nav panels (e.g. 2023-国赛C题.html) are left untouched.
 *
 * To opt in, use an empty container:
 *   <div class="chapter-nav-panel" id="chapterNav"></div>
 *
 * The function also highlights the current page link automatically.
 */
(function(){
  var NAV_DATA = [
    { section: '核心方法', links: [
      { href: '插值与拟合.html',      num: '1',  text: '插值与拟合' },
      { href: '蒙特卡洛.html',        num: '2',  text: '蒙特卡洛方法' },
      { href: '线性回归.html',        num: '3',  text: '线性回归' },
      { href: 'AI与建模.html',        num: '4',  text: 'AI与数学建模' },
      { href: '主成分与因子分析.html', num: '5',  text: '主成分与因子分析' },
      { href: '时间序列.html',        num: '6',  text: '时间序列分析' },
      { href: '图与网络.html',        num: '7',  text: '图与网络' },
      { href: '数据处理.html',        num: '8',  text: '数据处理' },
      { href: '存储论.html',          num: '9',  text: '存储论' },
      { href: '灰色系统.html',        num: '10', text: '灰色系统' },
      { href: '模拟退火.html',        num: '11', text: '模拟退火算法' },
      { href: '排队论.html',          num: '12', text: '排队论' },
      { href: '神经网络模型.html',    num: '13', text: '神经网络模型' },
      { href: '常微分方程.html',      num: '14', text: '常微分方程建模' },
      { href: '偏微分方程.html',      num: '15', text: '偏微分方程建模' },
      { href: '卡尔曼滤波.html',      num: '16', text: '卡尔曼滤波' },
      { href: '遗传算法.html',        num: '17', text: '遗传算法' },
      { href: '聚类分析.html',        num: '18', text: '聚类分析' }
    ]},
    { section: '综合专题', links: [
      { href: '方法大全.html',        num: '★',  text: '方法大全（59种）' }
    ]},
    { section: '真题实战', links: [
      { href: '历年真题模拟分析.html', num: '📝', text: '历年真题模拟分析' }
    ]}
  ];

  function buildNavHTML() {
    var html = '<div class="nav-header">📐 目录导航</div>';
    for (var s = 0; s < NAV_DATA.length; s++) {
      var sec = NAV_DATA[s];
      html += '<div class="nav-section">' + sec.section + '</div>';
      for (var l = 0; l < sec.links.length; l++) {
        var link = sec.links[l];
        html += '<a href="' + link.href + '"><span class="num">' + link.num + '</span>' + link.text + '</a>';
      }
    }
    html += '<a href="index.html" style="border-top:1px solid var(--sidebar-border);margin-top:6px;padding-top:10px"><span class="num">⌂</span>返回首页</a>';
    return html;
  }

  function highlightCurrent(panel) {
    var path = window.location.pathname.split('/').pop() || 'index.html';
    panel.querySelectorAll('a, .nav-sub').forEach(function(a){
      if(a.getAttribute('href') === path) a.classList.add('current');
    });
  }

  // On DOM ready, fill empty panels and highlight
  function initPanel() {
    var panel = document.getElementById('chapterNav');
    if(!panel) return;

    // Only auto-fill if the panel is empty (or contains only whitespace)
    var trimmed = panel.innerHTML.trim();
    if(!trimmed || trimmed === '') {
      panel.innerHTML = buildNavHTML();
    }

    highlightCurrent(panel);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initPanel);
  } else {
    initPanel();
  }
})();

})();
