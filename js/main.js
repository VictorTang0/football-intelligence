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
    teamTags: {},
    leagueProfiles: {},
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
    const [config, matches, weights, history, evolution, teamTags, leagueProfiles] = await Promise.all([
      loadJSON('./data/config.json'),
      loadJSON('./data/matches.json'),
      loadJSON('./data/weights.json'),
      loadJSON('./data/history.json'),
      loadJSON('./data/model_evolution.json'),
      loadJSON('./data/team_tags.json', {}),
      loadJSON('./data/league_profiles.json', {})
    ]);

    state.config         = config;
    state.matches        = matches;
    state.weights        = weights;
    state.history        = history;
    state.evolution      = evolution;
    state.teamTags       = teamTags || {};
    state.leagueProfiles = leagueProfiles || {};
    state.usingDemo      = matches?.is_demo === true;
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

  const weekdayMap = {"周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7};
  function getSportterySortKey(m) {
    const numStr = m.match_no || m.matchNumStr || m.id || '';
    let dayNum = 99;
    let matchCode = 999;
    
    // 1. Regex match for match_YYMMDD_code (e.g. match_260724_201)
    const matchReg = /match_(\d{2})(\d{2})(\d{2})_(\d+)/.exec(numStr);
    if (matchReg) {
      const year = 2000 + parseInt(matchReg[1], 10);
      const month = parseInt(matchReg[2], 10) - 1;
      const day = parseInt(matchReg[3], 10);
      const dt = new Date(year, month, day);
      if (!isNaN(dt.getTime())) {
        const dayOfWeek = dt.getDay(); // 0 (Sun) to 6 (Sat)
        dayNum = dayOfWeek === 0 ? 7 : dayOfWeek;
      }
      matchCode = parseInt(matchReg[4], 10);
    } else {
      // 2. Traditional Chinese weekday parsing
      for (const [wk, idx] of Object.entries(weekdayMap)) {
        if (numStr.includes(wk)) {
          dayNum = idx;
          const codePart = numStr.replace(wk, '').replace(/[^0-9]/g, '').trim();
          if (codePart) matchCode = parseInt(codePart, 10);
          break;
        }
      }
    }
    return [dayNum, matchCode, m.kickoff || '', m.id || ''];
  }

  function sortMatchesBySporttery(matchList) {
    return [...matchList].sort((a, b) => {
      const keyA = getSportterySortKey(a);
      const keyB = getSportterySortKey(b);
      if (keyA[0] !== keyB[0]) return keyA[0] - keyB[0];
      if (keyA[1] !== keyB[1]) return keyA[1] - keyB[1];
      return keyA[2].localeCompare(keyB[2]);
    });
  }

  // ─── RENDER APP ───
  function renderApp() {
    const matches = state.matches?.matches || [];
    const rawUpcoming = matches.filter(m => !m.is_finished && m.status !== 'finished' && !m.ultimate_conclusion?.actual_result);
    const upcomingMatches = sortMatchesBySporttery(rawUpcoming);
    const weights = state.weights;
    const history = state.history;
    const evolution = state.evolution;

    // Demo banner
    try {
      const demoBanner = document.getElementById('demo-banner');
      if (demoBanner) {
        if (state.usingDemo) demoBanner.classList.remove('hidden');
        else demoBanner.classList.add('hidden');
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering demo banner:', e);
    }

    // Update header badges
    try {
      const versionBadge = document.getElementById('version-badge');
      const matchCountEl = document.getElementById('header-match-count');
      const m10DirEl = document.getElementById('m10-acc-dir');
      const m10GoalsEl = document.getElementById('m10-acc-goals');
      const m10ScoreEl = document.getElementById('m10-acc-score');
      const m10HafuEl = document.getElementById('m10-acc-hafu');
      const accEl = document.getElementById('header-accuracy');
      const scoreAccEl = document.getElementById('header-score-accuracy');
      const hfAccEl = document.getElementById('header-hf-accuracy');
      const historyCountEl = document.getElementById('header-history-count');
      const evoCountEl = document.getElementById('header-evo-count');

      const latestVersion = evolution?.snapshots?.slice(-1)[0]?.version || weights?.version || 'v3.5';
      if (versionBadge) versionBadge.textContent = latestVersion;
      if (matchCountEl) matchCountEl.textContent = upcomingMatches.length;

      // M10 竞彩大师四维首选命中率 (2x4 表格) 专属渲染
      const spStats = history?.sporttery_primary_stats || {};
      if (m10DirEl) {
        const acc = spStats.direction?.accuracy_rate;
        m10DirEl.textContent = acc !== null && acc !== undefined && spStats.direction?.total > 0 ? (acc * 100).toFixed(1) + '%' : '--%';
      }
      if (m10GoalsEl) {
        const acc = spStats.goals?.accuracy_rate;
        m10GoalsEl.textContent = acc !== null && acc !== undefined && spStats.goals?.total > 0 ? (acc * 100).toFixed(1) + '%' : '--%';
      }
      if (m10ScoreEl) {
        const acc = spStats.score?.accuracy_rate;
        m10ScoreEl.textContent = acc !== null && acc !== undefined && spStats.score?.total > 0 ? (acc * 100).toFixed(1) + '%' : '--%';
      }
      if (m10HafuEl) {
        const acc = spStats.half_full?.accuracy_rate;
        m10HafuEl.textContent = acc !== null && acc !== undefined && spStats.half_full?.total > 0 ? (acc * 100).toFixed(1) + '%' : '--%';
      }

      if (accEl) {
        const acc = history?.accuracy_rate;
        accEl.textContent = acc !== null && acc !== undefined ? (acc * 100).toFixed(1) + '%' : '--';
      }
      if (scoreAccEl) {
        const acc = history?.score_accuracy_rate;
        scoreAccEl.textContent = acc !== null && acc !== undefined ? (acc * 100).toFixed(1) + '%' : '--';
      }
      if (hfAccEl) {
        const acc = history?.half_full_accuracy_rate;
        hfAccEl.textContent = acc !== null && acc !== undefined ? (acc * 100).toFixed(1) + '%' : '--';
      }
      if (historyCountEl) {
        historyCountEl.textContent = history?.total_predictions || 0;
      }
      if (evoCountEl) {
        evoCountEl.textContent = evolution?.evolution_count || 0;
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering header badges:', e);
    }

    // ── Ultimate Conclusions Section ──
    try {
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
          ucGrid.innerHTML = upcomingMatches.map(m => {
            try {
              return MatchIQRender.renderUltimateCard(m, state.teamTags, state.leagueProfiles);
            } catch (err) {
              console.error(`[MatchIQ] Error rendering ultimate card for ${m.id}:`, err);
              return `<div class="ultimate-card risk-low" style="padding:24px;text-align:center;color:var(--text-4);border:1px dashed var(--border-subtle)">⚠️ 无法加载此推荐内容 (${m.home || '未知'} vs ${m.away || '未知'})</div>`;
            }
          }).join('');
        }
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering ultimate section:', e);
    }

    // ── EV-Optimized Parlays Section ──
    try {
      const parlayContainer = document.getElementById('parlay-container');
      if (parlayContainer) {
        let filteredUpcoming = upcomingMatches;
        if (state.parlayFilter === 'sameday' && upcomingMatches.length > 0) {
          const sorted = sortMatchesBySporttery(upcomingMatches);
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
    } catch (e) {
      console.error('[MatchIQ] Error rendering parlays:', e);
    }

    // ── Model Status ──
    try {
      const statusContainer = document.getElementById('model-status-container');
      if (statusContainer) {
        statusContainer.innerHTML = MatchIQRender.renderModelStatus(weights, history, evolution);
        document.getElementById('evolution-toggle')?.addEventListener('click', toggleEvolution);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering model status:', e);
    }

    // ── Summary Table ──
    try {
      const summaryContainer = document.getElementById('summary-table-container');
      if (summaryContainer) {
        const bankrollInput = document.getElementById('kelly-bankroll-input');
        const bankroll = bankrollInput ? (parseFloat(bankrollInput.value) || 100) : 100;
        summaryContainer.innerHTML = MatchIQRender.renderSummaryTable(upcomingMatches, bankroll);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering summary table:', e);
    }

    // ── Match Cards ──
    try {
      const matchesGrid = document.getElementById('matches-grid');
      if (matchesGrid) {
        if (upcomingMatches.length === 0) {
          matchesGrid.innerHTML = `
            <div style="text-align:center;padding:64px;color:var(--text-4);">
              <div style="font-size:13px">暂无比赛分析数据</div>
            </div>`;
        } else {
          matchesGrid.innerHTML = upcomingMatches.map(m => {
            try {
              return MatchIQRender.renderMatchCard(m, weights, state.teamTags, state.tagsConfig, state.leagueProfiles);
            } catch (err) {
              console.error(`[MatchIQ] Error rendering match card for ${m.id}:`, err);
              return `<div class="match-card" style="padding:24px;text-align:center;color:var(--text-4);border:1px dashed var(--border-subtle)">⚠️ 无法加载此场比赛分析 (${m.home || '未知'} vs ${m.away || '未知'})</div>`;
            }
          }).join('');
        }
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering match cards grid:', e);
    }

    // ── Evolution Section ──
    try {
      const evoContainer = document.getElementById('evolution-container');
      if (evoContainer) {
        evoContainer.innerHTML = MatchIQRender.renderEvolutionSection(evolution, history);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering evolution section:', e);
    }

    // ── History Records Section ──
    try {
      const historyGrid = document.getElementById('history-records-grid');
      if (historyGrid) {
        historyGrid.innerHTML = MatchIQRender.renderHistoryRecords(history);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering history grid:', e);
    }

    // ── Parlay History Section ──
    try {
      const parlayHistoryContainer = document.getElementById('parlay-history-container');
      if (parlayHistoryContainer) {
        parlayHistoryContainer.innerHTML = MatchIQRender.renderParlayHistory(history);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering parlay history:', e);
    }

    // ── Risk Radar History Section ──
    try {
      const radarHistoryContainer = document.getElementById('risk-radar-history-container');
      if (radarHistoryContainer) {
        radarHistoryContainer.innerHTML = MatchIQRender.renderRadarHistory(history);
      }
    } catch (e) {
      console.error('[MatchIQ] Error rendering radar history:', e);
    }

    // Init all charts after DOM is updated (only for upcoming/active matches)
    requestAnimationFrame(() => {
      try {
        initAllCharts(upcomingMatches, weights, history, evolution);
      } catch (err) {
        console.error('[MatchIQ] Error initializing charts:', err);
      }
      try {
        bindTabEvents();
      } catch (err) {
        console.error('[MatchIQ] Error binding tab events:', err);
      }
      try {
        updateRiskRadarAndKelly(upcomingMatches);
      } catch (err) {
        console.error('[MatchIQ] Error updating risk radar/Kelly:', err);
      }
    });
  }

  // ─── RISK RADAR & KELLY SIZER ───
  function updateRiskRadarAndKelly(upcomingMatches) {
    const ticker = document.getElementById('risk-radar-ticker');
    const calcBtn = document.getElementById('kelly-calc-btn');
    const bankrollInput = document.getElementById('kelly-bankroll-input');
    
    if (!ticker) return;

    // Display cumulative radar accuracy
    const accBadge = document.getElementById('risk-radar-accuracy-badge');
    if (accBadge && state.history?.radar_stats) {
      const stats = state.history.radar_stats;
      const rate = (stats.accuracy_rate * 100).toFixed(1);
      accBadge.innerHTML = `(预警累计准确率: ${rate}% / 已发 ${stats.total_alerts} 场)`;
    }
    
    // 1. Process Risk Radar Alerts
    const alerts = [];
    const trap_t = state.config?.odds_trap_threshold || 0.01;
    const protect_t = state.config?.odds_protect_threshold || -0.01;
    
    upcomingMatches.forEach(m => {
      const pvb = m.public_vs_bookmaker || [];
      if (!pvb.length) return;
      
      const matchNo = m.id.replace('match_', 'No.');
      const matchDesc = `${m.home} VS ${m.away}`;
      
      // Find highest risk row or active attitude
      let targetRow = pvb.find(r => r.payout_risk === '极高') || 
                        pvb.find(r => r.payout_risk === '偏高') || 
                        pvb.find(r => r.payout_risk === '适中') || 
                        pvb[0];
                        
      const outcome = targetRow.outcome || '主胜';
      const risk = targetRow.payout_risk || '低';
      const attitude = targetRow.bookmaker_attitude || '中性';
      const pubProb = targetRow.public_prob || '--';
      const trueEst = targetRow.true_est || '--';
      const bmImplied = targetRow.bookmaker_implied || '--';
      
      const opp = outcome === "主胜" ? "客队不败" : outcome === "客胜" ? "主队不败" : "双选胜负";

      if (risk === '极高') {
        alerts.push(`
          <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:12px 10px; text-align:center; font-weight:700; color:var(--text-3); font-size:14px;">${matchNo}</td>
            <td style="padding:12px 10px; font-weight:600; color:var(--text-1); font-size:15px;">${m.home} <span style="color:var(--text-4); font-size:12px;">VS</span> ${m.away}</td>
            <td style="padding:12px 10px; font-size:14.5px; font-weight:700; color:#ff5252; white-space:nowrap;">🚨 资本诱盘 (${attitude})</td>
            <td style="padding:12px 10px; font-size:14.5px; color:var(--text-2);">散户过度热买【${outcome}】(${pubProb})，官方赔率升水阻尼防范</td>
            <td style="padding:12px 10px; text-align:center; font-size:14.5px; font-weight:700; color:#ff5252; white-space:nowrap;">防冷推荐: ${opp}</td>
          </tr>
        `);
      } else if (risk === '偏高') {
        alerts.push(`
          <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:12px 10px; text-align:center; font-weight:700; color:var(--text-3); font-size:14px;">${matchNo}</td>
            <td style="padding:12px 10px; font-weight:600; color:var(--text-1); font-size:15px;">${m.home} <span style="color:var(--text-4); font-size:12px;">VS</span> ${m.away}</td>
            <td style="padding:12px 10px; font-size:14.5px; font-weight:700; color:#4caf50; white-space:nowrap;">🟢 降水保护 (${attitude})</td>
            <td style="padding:12px 10px; font-size:14.5px; color:var(--text-2);">真实估值【${outcome}】(${trueEst})高于官赔，官方降水控赔支持</td>
            <td style="padding:12px 10px; text-align:center; font-size:14.5px; font-weight:700; color:#4caf50; white-space:nowrap;">首选支持: ${outcome}</td>
          </tr>
        `);
      } else if (risk === '适中') {
        alerts.push(`
          <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:12px 10px; text-align:center; font-weight:700; color:var(--text-3); font-size:14px;">${matchNo}</td>
            <td style="padding:12px 10px; font-weight:600; color:var(--text-1); font-size:15px;">${m.home} <span style="color:var(--text-4); font-size:12px;">VS</span> ${m.away}</td>
            <td style="padding:12px 10px; font-size:14.5px; font-weight:700; color:#2196f3; white-space:nowrap;">🔵 机构支持 (${attitude})</td>
            <td style="padding:12px 10px; font-size:14.5px; color:var(--text-2);">真实概率估值【${outcome}】(${trueEst})具备优势，开盘表现稳健</td>
            <td style="padding:12px 10px; text-align:center; font-size:14.5px; font-weight:700; color:#2196f3; white-space:nowrap;">建议支持: ${outcome}</td>
          </tr>
        `);
      } else {
        alerts.push(`
          <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:12px 10px; text-align:center; font-weight:700; color:var(--text-3); font-size:14px;">${matchNo}</td>
            <td style="padding:12px 10px; font-weight:600; color:var(--text-1); font-size:15px;">${m.home} <span style="color:var(--text-4); font-size:12px;">VS</span> ${m.away}</td>
            <td style="padding:12px 10px; font-size:14.5px; font-weight:700; color:var(--text-3); white-space:nowrap;">⚪ 盘面平衡 (${attitude})</td>
            <td style="padding:12px 10px; font-size:14.5px; color:var(--text-2);">筹码与官赔分布均衡(${bmImplied})，无显现资本异常倾斜</td>
            <td style="padding:12px 10px; text-align:center; font-size:14.5px; font-weight:700; color:var(--text-2); white-space:nowrap;">常规关注</td>
          </tr>
        `);
      }
    });
    
    if (alerts.length > 0) {
      ticker.innerHTML = `
        <table style="width:100%; border-collapse:collapse; text-align:left; font-size:14.5px; margin-top:8px;">
          <thead>
            <tr style="border-bottom:1px solid rgba(255,61,0,0.15); color:var(--text-3); font-size:12.5px; font-weight:700; text-transform:uppercase;">
              <th style="padding:8px; text-align:center; width:10%;">场次</th>
              <th style="padding:8px; text-align:left; width:25%;">赛事对阵</th>
              <th style="padding:8px; text-align:left; width:15%;">风控预警</th>
              <th style="padding:8px; text-align:left; width:35%;">变盘与诱盘分析</th>
              <th style="padding:8px; text-align:center; width:15%;">避险决策推荐</th>
            </tr>
          </thead>
          <tbody>
            ${alerts.join('')}
          </tbody>
        </table>
      `;
    } else {
      ticker.innerHTML = `<span style="color:var(--text-4); font-style:italic; font-size:14.5px; display:block; padding:12px 0;">雷达检测中... 暂未发现触发变盘阀值异常的赛事</span>`;
    }
    
    // 2. Kelly Bet Sizer Calculations
    const runKellyCalculations = () => {
      const bankroll = bankrollInput ? (parseFloat(bankrollInput.value) || 100) : 100;
      upcomingMatches.forEach(m => {
        // Find Card (Ultimate Card)
        const ucCard = document.getElementById(`uc-${m.id}`);
        if (ucCard) {
          let sizerEl = ucCard.querySelector('.kelly-sizer-badge');
          if (!sizerEl) {
            const metricsEl = ucCard.querySelector('.uc-metrics');
            if (metricsEl) {
              sizerEl = document.createElement('div');
              sizerEl.className = 'kelly-sizer-badge';
              sizerEl.style.cssText = 'margin-top:12px; padding:8px 12px; background:rgba(0, 212, 255, 0.05); border:1px solid rgba(0, 212, 255, 0.2); border-radius:6px; font-size:12.5px; color:var(--text-2); text-align:center;';
              metricsEl.parentNode.insertBefore(sizerEl, metricsEl.nextSibling);
            }
          }
          if (sizerEl) {
            const uc = m.ultimate_conclusion || {};
            const recommendation = uc.recommendation || "";
            const oddsObj = m.odds_analysis?.pinnacle?.current || {};
            
            const ph = oddsObj["home"] || 2.0;
            const pd = oddsObj["draw"] || 3.0;
            const pa = oddsObj["away"] || 3.0;
            
            let odds = 1.80;
            let outcomeKey = "home";
            
            // Determine bet type & calculate odds
            if (recommendation.includes("主不败") || recommendation.includes("主队不败") || recommendation.includes("双选不败")) {
              odds = 1 / ((1 / ph) + (1 / pd));
            } else if (recommendation.includes("客不败") || recommendation.includes("客队不败") || recommendation.includes("反基本面冷门 (客队不败)")) {
              odds = 1 / ((1 / pa) + (1 / pd));
            } else if (recommendation.includes("反基本面冷门 (主队不败)")) {
              odds = 1 / ((1 / ph) + (1 / pd));
            } else if (recommendation.includes("平局") || recommendation.includes("平")) {
              outcomeKey = "draw";
              odds = oddsObj[outcomeKey] || 1.80;
            } else if (recommendation.includes("客胜") || recommendation.includes("客")) {
              outcomeKey = "away";
              odds = oddsObj[outcomeKey] || 1.80;
            } else {
              odds = oddsObj["home"] || 1.80;
            }
            
            // Round odds to 2 decimal places
            odds = Math.round(odds * 100) / 100;
            
            // True estimated probability is direct from model confidence
            const prob = (uc.confidence || 65) / 100;
            
            // Fractional Kelly multiplier (using quarter-kelly 0.25 to prevent over-betting)
            const b = odds - 1;
            const q = 1 - prob;
            let kellyFraction = 0;
            if (b > 0) {
              kellyFraction = (prob * b - q) / b;
            }
            
            const quarterKelly = Math.max(0, kellyFraction * 0.25);
            const recommendStake = Math.round(bankroll * quarterKelly);
            
            if (quarterKelly > 0) {
              sizerEl.innerHTML = `🧮 <strong>量化资金管理</strong>: 季凯比率 <span style="color:var(--cyan);font-weight:700">${(quarterKelly*100).toFixed(2)}%</span> · 推荐投注额 <span style="color:var(--cyan);font-weight:700">${recommendStake} 元</span> <span style="font-size:11px;color:var(--text-3);">[赔率:${odds.toFixed(2)}]</span>`;
              sizerEl.style.display = 'block';
            } else {
              sizerEl.innerHTML = `🧮 <strong>量化资金管理</strong>: 期望值为负 (EV < 0) · <span style="color:var(--red);font-weight:700">建议观望 (No Bet)</span> <span style="font-size:11px;color:var(--text-4);">[赔率:${odds.toFixed(2)}]</span>`;
              sizerEl.style.display = 'block';
            }
          }
        }
      });

      // Re-render summary table with new bankroll
      const summaryContainer = document.getElementById('summary-table-container');
      if (summaryContainer) {
        summaryContainer.innerHTML = MatchIQRender.renderSummaryTable(upcomingMatches, bankroll);
      }
    };
    
    // Bind click event for sizer button
    if (calcBtn) calcBtn.onclick = runKellyCalculations;
    if (bankrollInput && !bankrollInput.dataset.bound) {
      bankrollInput.dataset.bound = 'true';
      let timer = null;
      bankrollInput.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(runKellyCalculations, 150);
      });
    }
    
    // Auto run once
    runKellyCalculations();
  }

  function getAdjustedWeights(match, weightsData, teamTags, tagsConfig, leagueProfiles) {
    if (!weightsData) return null;
    const factors = (weightsData.factors || []).map(f => ({ ...f }));
    const tagConfigMap = {};
    if (tagsConfig?.tags) {
      tagsConfig.tags.forEach(t => {
        tagConfigMap[t.name] = t;
      });
    }

    const home = match.home;
    const away = match.away;
    const homeTags = teamTags?.[home]?.tags || {};
    const awayTags = teamTags?.[away]?.tags || {};

    const activeAdjustments = [];
    const collectAdjustments = (teamName, tags) => {
      Object.entries(tags).forEach(([name, info]) => {
        if (info.level >= 2) {
          const config = tagConfigMap[name];
          if (config && config.factors) {
            activeAdjustments.push({
              teamName,
              tagName: name,
              level: info.level,
              factorIds: config.factors
            });
          }
        }
      });
    };
    collectAdjustments(home, homeTags);
    collectAdjustments(away, awayTags);

    activeAdjustments.forEach(adj => {
      adj.factorIds.forEach(fid => {
        const factor = factors.find(f => f.id === fid);
        if (factor) {
          factor.weight *= (1.0 + 0.15 * adj.level);
        }
      });
    });

    // Apply league profile modifiers (M01-M08)
    const leagueName = match.league || '';
    if (leagueProfiles && leagueName) {
      const matchedKey = Object.keys(leagueProfiles).find(k => leagueName.includes(k) || k.includes(leagueName));
      if (matchedKey) {
        const profile = leagueProfiles[matchedKey];
        if (profile.modifiers) {
          Object.entries(profile.modifiers).forEach(([fid, multiplier]) => {
            const factor = factors.find(f => f.id === fid);
            if (factor) {
              factor.weight *= multiplier;
            }
          });
        }
      }
    }

    const totalWeight = factors.reduce((sum, f) => sum + f.weight, 0);
    if (totalWeight > 0) {
      factors.forEach(f => {
        f.weight = f.weight / totalWeight;
      });
    }
    return { ...weightsData, factors };
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
      const adjW = getAdjustedWeights(match, weights, state.teamTags, state.tagsConfig, state.leagueProfiles);
      MatchIQCharts.initFactorChart(`factor-chart-${match.id}`, {}, adjW);
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
        const rawUpcoming = matches.filter(m => !m.is_finished && m.status !== 'finished' && !m.ultimate_conclusion?.actual_result);
        const upcomingMatches = sortMatchesBySporttery(rawUpcoming);
        const parlayContainer = document.getElementById('parlay-container');
        if (parlayContainer) {
          let filteredUpcoming = upcomingMatches;
          if (state.parlayFilter === 'sameday' && upcomingMatches.length > 0) {
            const sorted = sortMatchesBySporttery(upcomingMatches);
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
              const adjW = getAdjustedWeights(match, state.weights, state.teamTags, state.tagsConfig, state.leagueProfiles);
              MatchIQCharts.initFactorChart(`factor-chart-${matchId}`, {}, adjW);
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
      // Hide loading screen & default scroll to Conclusion Summary (#summary-section)
      const loading = document.getElementById('loading-screen');
      if (loading) {
        loading.style.opacity = '0';
        loading.style.transition = 'opacity 0.5s';
        setTimeout(() => {
          loading.classList.add('hidden');
          if (!window.location.hash) {
            const summaryEl = document.getElementById('summary-section');
            if (summaryEl) {
              summaryEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }
        }, 500);
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
  // Global tooltips init
  const tooltip = document.getElementById('matchiq-tooltip');
  if (tooltip) {
    document.body.addEventListener('mouseover', (e) => {
      const target = e.target.closest('[data-tooltip]');
      if (!target) return;

      const text = target.getAttribute('data-tooltip');
      if (!text) return;

      tooltip.innerHTML = text.replace(/\n/g, '<br>');
      tooltip.classList.add('visible');

      const rect = target.getBoundingClientRect();
      let top = rect.top + window.scrollY - tooltip.offsetHeight - 10;
      let left = rect.left + window.scrollX + (rect.width - tooltip.offsetWidth) / 2;

      if (left < 10) left = 10;
      if (left + tooltip.offsetWidth > window.innerWidth - 10) {
        left = window.innerWidth - tooltip.offsetWidth - 10;
      }
      if (rect.top - tooltip.offsetHeight < 10) {
        top = rect.bottom + window.scrollY + 10;
      }

      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
    });

    document.body.addEventListener('mouseout', (e) => {
      const target = e.target.closest('[data-tooltip]');
      if (target && !e.relatedTarget?.closest('[data-tooltip]')) {
        tooltip.classList.remove('visible');
      }
    });
  }

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
