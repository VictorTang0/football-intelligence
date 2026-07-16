/* ============================================================
   MATCH IQ — Main Application Entry
   Data loading, initialization, event handling
   ============================================================ */

const MatchIQ = (() => {

  // ─── APP STATE ───
  const state = {
    config: null,
    matches: null,
    weights: null,
    history: null,
    evolution: null,
    initialized: false,
    usingDemo: false,
    parlayFilter: 'all'
  };

  // ─── DATA LOADING ───
  async function loadJSON(path, fallback = null) {
    try {
      const res = await fetch(path + '?v=' + Date.now());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn(`[MatchIQ] Could not load ${path}: ${e.message}`);
      return fallback;
    }
  }

  async function loadAllData() {
    const [config, matches, weights, history, evolution] = await Promise.all([
      loadJSON('./data/config.json'),
      loadJSON('./data/matches.json'),
      loadJSON('./data/weights.json'),
      loadJSON('./data/history.json'),
      loadJSON('./data/model_evolution.json'),
    ]);

    state.config    = config;
    state.matches   = matches;
    state.weights   = weights;
    state.history   = history;
    state.evolution = evolution;
    state.usingDemo = matches?.is_demo === true;
  }

  // ─── RADAR DATA BUILDER ───
  function buildRadarData(stats) {
    const s = stats || {};
    const maxGoals = 90;
    const norm = (v, max) => Math.min(+(v / max * 10).toFixed(1), 10);
    return [
      norm(s.goals_scored || 0, maxGoals),                       // 进攻效率
      s.low_block_resilience !== undefined ? s.low_block_resilience : norm(50 - (s.goals_conceded || 30), 50), // 大巴防守
      norm((s.conversion_rate || 0.2) * 100, 40),                // 射门转化
      norm(s.xg || 50, 90),                                      // xG能力
      s.superstar_impact !== undefined ? s.superstar_impact : norm(s.pressing_intensity || 60, 100), // 巨星破局
      norm(s.set_piece_goals || 8, 20),                          // 定位球
      norm(s.possession || 50, 70),                              // 中场控制
      norm(s.shots_on_target || 5, 10),                          // 近期状态
    ];
  }

  // ─── RENDER APP ───
  function renderApp() {
    const matches = state.matches?.matches || [];
    const upcomingMatches = matches.filter(m => m.status !== 'finished');
    const weights = state.weights;
    const history = state.history;
    const evolution = state.evolution;

    // Demo banner
    const demoBanner = document.getElementById('demo-banner');
    if (demoBanner) {
      if (state.usingDemo) demoBanner.classList.remove('hidden');
      else demoBanner.classList.add('hidden');
    }

    // Update header badges
    const versionBadge = document.getElementById('version-badge');
    const matchCountEl = document.getElementById('header-match-count');
    const accEl = document.getElementById('header-accuracy');
    if (versionBadge) versionBadge.textContent = weights?.version || 'v1.0';
    if (matchCountEl) matchCountEl.textContent = upcomingMatches.length;
    if (accEl) {
      const acc = history?.accuracy_rate;
      accEl.textContent = acc !== null && acc !== undefined ? (acc * 100).toFixed(1) + '%' : '--';
    }

    // ── Ultimate Conclusions Section ──
    const ucGrid = document.getElementById('ultimate-grid');
    if (ucGrid) {
      if (upcomingMatches.length === 0) {
        ucGrid.innerHTML = `
          <div style="grid-column:1/-1;text-align:center;padding:48px;color:var(--text-4);">
            <div style="font-size:48px;margin-bottom:16px">📡</div>
            <div style="font-family:var(--font-display);font-size:20px;margin-bottom:8px">等待赛事数据</div>
            <div style="font-size:13px">请发送赛程图片触发分析</div>
          </div>`;
      } else {
        ucGrid.innerHTML = upcomingMatches.map(m => MatchIQRender.renderUltimateCard(m)).join('');
      }
    }

    // ── EV-Optimized Parlays Section ──
    const parlayContainer = document.getElementById('parlay-container');
    if (parlayContainer) {
      let filteredUpcoming = upcomingMatches;
      if (state.parlayFilter === 'sameday' && upcomingMatches.length > 0) {
        const sorted = [...upcomingMatches].sort((a, b) => new Date(a.kickoff) - new Date(b.kickoff));
        const earliestDate = new Date(sorted[0].kickoff).toLocaleDateString('zh-CN', {
          year: 'numeric', month: '2-digit', day: '2-digit'
        }).replace(/\//g, '-');
        filteredUpcoming = sorted.filter(m => {
          const mDate = new Date(m.kickoff).toLocaleDateString('zh-CN', {
            year: 'numeric', month: '2-digit', day: '2-digit'
          }).replace(/\//g, '-');
          return mDate === earliestDate;
        });
      }
      parlayContainer.innerHTML = MatchIQRender.renderParlays(filteredUpcoming);
    }

    // ── Model Status ──
    const statusContainer = document.getElementById('model-status-container');
    if (statusContainer) {
      statusContainer.innerHTML = MatchIQRender.renderModelStatus(weights, history, evolution);
      document.getElementById('evolution-toggle')?.addEventListener('click', toggleEvolution);
    }

    // ── Match Cards ──
    const matchesGrid = document.getElementById('matches-grid');
    if (matchesGrid) {
      if (upcomingMatches.length === 0) {
        matchesGrid.innerHTML = `
          <div style="text-align:center;padding:64px;color:var(--text-4);">
            <div style="font-size:13px">暂无比赛分析数据</div>
          </div>`;
      } else {
        matchesGrid.innerHTML = upcomingMatches.map(m => MatchIQRender.renderMatchCard(m, weights)).join('');
      }
    }

    // ── Evolution Section ──
    const evoContainer = document.getElementById('evolution-container');
    if (evoContainer) {
      evoContainer.innerHTML = MatchIQRender.renderEvolutionSection(evolution, history);
    }

    // ── History Records Section ──
    const historyGrid = document.getElementById('history-records-grid');
    if (historyGrid) {
      historyGrid.innerHTML = MatchIQRender.renderHistoryRecords(history);
    }

    // ── Parlay History Section ──
    const parlayHistoryContainer = document.getElementById('parlay-history-container');
    if (parlayHistoryContainer) {
      parlayHistoryContainer.innerHTML = MatchIQRender.renderParlayHistory(history);
    }

    // Init all charts after DOM is updated (only for upcoming/active matches)
    requestAnimationFrame(() => {
      initAllCharts(upcomingMatches, weights, history, evolution);
      bindTabEvents();
    });
  }

  // ─── INITIALIZE CHARTS ───
  function initAllCharts(matches, weights, history, evolution) {
    // Radar charts for each match
    matches.forEach(match => {
      const homeStats = match.team_stats?.home?.season_stats;
      const awayStats = match.team_stats?.away?.season_stats;
      MatchIQCharts.initTeamRadar(
        `radar-${match.id}`,
        buildRadarData(homeStats),
        buildRadarData(awayStats),
        match.home || '主队',
        match.away || '客队'
      );


      // Factor chart (first match only or all)
      MatchIQCharts.initFactorChart(`factor-chart-${match.id}`, {}, weights);
    });

    // Evolution chart
    if (evolution) {
      MatchIQCharts.initEvolutionChart('evolution-chart', evolution);
    }

    // Accuracy chart
    if (history) {
      MatchIQCharts.initAccuracyChart('accuracy-chart', history);
    }

    // Evolution panel charts (if panel open)
    if (weights) {
      MatchIQCharts.initFactorChart('evolution-factor-chart', {}, weights);
    }
  }

  // ─── TAB EVENTS ───
  function bindTabEvents() {
    // Parlay filter tab buttons
    document.querySelectorAll('.parlay-tab-btn').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = 'true';
      btn.addEventListener('click', () => {
        document.querySelectorAll('.parlay-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.parlayFilter = btn.dataset.type;
        
        // Trigger partial render for parlay container
        const matches = state.matches?.matches || [];
        const upcomingMatches = matches.filter(m => m.status !== 'finished');
        const parlayContainer = document.getElementById('parlay-container');
        if (parlayContainer) {
          let filteredUpcoming = upcomingMatches;
          if (state.parlayFilter === 'sameday' && upcomingMatches.length > 0) {
            const sorted = [...upcomingMatches].sort((a, b) => new Date(a.kickoff) - new Date(b.kickoff));
            const earliestDate = new Date(sorted[0].kickoff).toLocaleDateString('zh-CN', {
              year: 'numeric', month: '2-digit', day: '2-digit'
            }).replace(/\//g, '-');
            filteredUpcoming = sorted.filter(m => {
              const mDate = new Date(m.kickoff).toLocaleDateString('zh-CN', {
                year: 'numeric', month: '2-digit', day: '2-digit'
              }).replace(/\//g, '-');
              return mDate === earliestDate;
            });
          }
          parlayContainer.innerHTML = MatchIQRender.renderParlays(filteredUpcoming);
        }
      });
    });

    document.querySelectorAll('.mc-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const matchId = tab.dataset.match;
        const tabName = tab.dataset.tab;

        // Update active tab
        document.querySelectorAll(`#tabs-${matchId} .mc-tab`).forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show correct pane
        const card = document.getElementById(`card-${matchId}`);
        if (!card) return;
        card.querySelectorAll('.mc-pane').forEach(p => p.classList.remove('active'));
        const targetPane = document.getElementById(`pane-${matchId}-${tabName}`);
        if (targetPane) {
          targetPane.classList.add('active');
          // Re-init charts in pane if needed (in case they were not visible before)
          setTimeout(() => {
            const match = (state.matches?.matches || []).find(m => m.id === matchId);
            if (!match) return;
            if (tabName === 'stats') {
              MatchIQCharts.initTeamRadar(
                `radar-${matchId}`,
                buildRadarData(match.team_stats?.home?.season_stats),
                buildRadarData(match.team_stats?.away?.season_stats),
                match.home, match.away
              );
            } else if (tabName === 'odds') {
              // No odds chart needed

            } else if (tabName === 'factors') {
              MatchIQCharts.initFactorChart(`factor-chart-${matchId}`, {}, state.weights);
            }
          }, 50);
        }
      });
    });
  }

  // ─── EVOLUTION PANEL TOGGLE ───
  function toggleEvolution() {
    const panel = document.getElementById('evolution-panel');
    const btn = document.getElementById('evolution-toggle');
    if (!panel || !btn) return;

    const isOpen = panel.classList.toggle('visible');
    btn.classList.toggle('expanded', isOpen);
    btn.querySelector(':last-child').textContent = isOpen ? ' 收起图表' : ' 查看进化图表';

    if (isOpen) {
      setTimeout(() => {
        MatchIQCharts.initEvolutionChart('evolution-chart-panel', state.evolution);
        MatchIQCharts.initAccuracyChart('accuracy-chart-panel', state.history);
      }, 50);
    }
  }

  // ─── UPLOAD ZONE ───
  function initUploadZone() {
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    if (!zone || !fileInput) return;

    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      const file = e.dataTransfer?.files[0];
      if (file) handleImageUpload(file);
    });

    fileInput.addEventListener('change', e => {
      const file = e.target.files[0];
      if (file) handleImageUpload(file);
    });
  }

  function handleImageUpload(file) {
    if (!file.type.startsWith('image/')) {
      alert('请上传图片文件');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById('upload-preview');
      const instruction = document.getElementById('upload-instruction');
      if (preview) {
        preview.innerHTML = `
          <div style="margin-top:20px">
            <img src="${e.target.result}" style="max-height:300px;border-radius:var(--radius);border:1px solid var(--border);width:100%;object-fit:contain;" alt="赛程图片"/>
          </div>
          <div style="margin-top:16px;padding:16px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:var(--radius);">
            <p style="font-size:13px;color:var(--green);font-weight:600;margin-bottom:6px">✅ 图片已上传</p>
            <p style="font-size:13px;color:var(--text-2);line-height:1.6">
              请将此图片同时发送到 AI 对话窗口，并输入命令：<br>
              <code style="background:rgba(0,212,255,0.1);color:var(--cyan);padding:4px 8px;border-radius:4px;font-family:var(--font-mono)">分析今日赛事</code>
              <br><br>AI 将自动执行：识别比赛 → 权重进化 → 数据抓取 → 完整分析 → 输出JSON
            </p>
          </div>`;
      }
    };
    reader.readAsDataURL(file);
  }

  // ─── NAVIGATION & BACK TO TOP ───
  function initNavigation() {
    const sideLinks = document.querySelectorAll('.side-index-link');
    const backToTop = document.getElementById('back-to-top');
    const sections = Array.from(sideLinks).map(link => document.getElementById(link.dataset.target)).filter(Boolean);

    // Scroll listener for Scrollspy and Back-to-Top fade-in
    window.addEventListener('scroll', () => {
      const scrollPos = window.scrollY + 120; // offset for sticky header

      // 1. Scrollspy active link highlight
      let currentSectionId = '';
      for (const section of sections) {
        if (scrollPos >= section.offsetTop && scrollPos < section.offsetTop + section.offsetHeight) {
          currentSectionId = section.id;
        }
      }
      
      // Fallback to first section if at very top
      if (window.scrollY < 200 && sections.length > 0) {
        currentSectionId = sections[0].id;
      }
      
      sideLinks.forEach(link => {
        if (link.dataset.target === currentSectionId) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });

      // 2. Back to Top visibility
      if (window.scrollY > 300) {
        backToTop?.classList.add('visible');
      } else {
        backToTop?.classList.remove('visible');
      }
    }, { passive: true });

    // Smooth scroll for nav links
    sideLinks.forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        const targetId = link.dataset.target;
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          const headerOffset = 70; // height of sticky header
          const elementPosition = targetEl.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
          
          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      });
    });

    // Smooth scroll back to top
    backToTop?.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // ─── INIT ───
  async function init() {
    try {
      await loadAllData();
      renderApp();
      initNavigation();
      state.initialized = true;
    } catch (err) {
      console.error('[MatchIQ] Init error:', err);
    } finally {
      // Hide loading screen
      const loading = document.getElementById('loading-screen');
      if (loading) {
        loading.style.opacity = '0';
        loading.style.transition = 'opacity 0.5s';
        setTimeout(() => loading.classList.add('hidden'), 500);
      }
    }
  }

  // ─── AUTO-REFRESH (optional, every 5 min) ───
  function startAutoRefresh(intervalMs = 300000) {
    setInterval(async () => {
      console.log('[MatchIQ] Auto-refreshing data...');
      await loadAllData();
      renderApp();
    }, intervalMs);
  }

  // Public API
  return { init, loadAllData, renderApp, state };
})();

// ─── BOOT ───
document.addEventListener('DOMContentLoaded', () => {
  MatchIQ.init().then(() => {
    // Wait for initial load
  });

  // ─── MOBILE NAVBAR LISTENERS ───
  const menuToggle = document.getElementById('mobile-menu-toggle');
  const menuDropdown = document.getElementById('mobile-menu-dropdown');
  
  if (menuToggle && menuDropdown) {
    menuToggle.addEventListener('click', () => {
      const isOpen = menuToggle.classList.toggle('open');
      menuDropdown.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close menu when a link is clicked
    menuDropdown.addEventListener('click', (e) => {
      if (e.target.classList.contains('mobile-menu-link')) {
        menuToggle.classList.remove('open');
        menuDropdown.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ─── COLLAPSIBLE MOB BLOCKS GLOBAL TOGGLER ───
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.collapsible-trigger');
    if (trigger) {
      const parent = trigger.parentElement;
      const body = parent.querySelector('.collapsible-body');
      if (body) {
        const isExpanded = body.classList.toggle('expanded');
        trigger.textContent = isExpanded ? trigger.getAttribute('data-collapse-text') : trigger.getAttribute('data-expand-text');
        
        // Re-trigger radar charts or factors charts if inside match-card
        if (isExpanded) {
          const activeTab = parent.querySelector('.mc-tab.active');
          if (activeTab) {
            activeTab.click();
          }
        }
      }
    }
  });
});
