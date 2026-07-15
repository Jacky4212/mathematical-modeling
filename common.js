/**
 * 数学建模学习平台 — 公共脚本
 * 主题切换 / 侧边栏高亮 / 章节导航 / 缓存刷新
 */
(function(){
'use strict';

// ===== Cache buster =====
var VERSION = '250714a';
if(localStorage.getItem('mm-ver') !== VERSION){
  localStorage.setItem('mm-ver', VERSION);
  location.reload(true);
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
(function(){
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

  // Highlight current page in chapter nav
  document.addEventListener('DOMContentLoaded', function(){
    var path = window.location.pathname.split('/').pop() || 'index.html';
    var panel = document.getElementById('chapterNav');
    if(!panel) return;
    panel.querySelectorAll('a, .nav-sub').forEach(function(a){
      if(a.getAttribute('href') === path) a.classList.add('current');
    });
  });
})();

})();
