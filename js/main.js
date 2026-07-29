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
    // 优先使用竞彩官方开售业务日期 issue_date (如 260725) 或 business_date (如 2026-07-25)
    let dateCode = m.issue_date || m.business_date || '';
    if (!dateCode) {
      const matchReg = /match_(\d{6})_(\d+)/.exec(m.id || '');
      if (matchReg) {
        dateCode = matchReg[1];
      } else {
        dateCode = (m.kickoff || '').split('T')[0].split(' ')[0] || '9999-99-99';
      }
    }
    let code = m.match_code;
    if (code === undefined || code === null) {
      const numStr = m.match_no || m.matchNumStr || m.id || '';
      const numMatch = numStr.match(/\d+$/);
      code = numMatch ? parseInt(numMatch[0], 10) : 999;
    }
    return [dateCode, code, m.kickoff || '', m.id || ''];
  }

  function sortMatchesBySporttery(matchList) {
    return [...matchList].sort((a, b) => {
      const getRank = (m) => {
        if (m.status === 'waiting_result' || m.status_label === '等待赛果') return 0;
        if (m.status === 'finished' || m.is_finished || m.ultimate_conclusion?.actual_result) return 2;
        return 1;
      };
      const rankA = getRank(a);
      const rankB = getRank(b);
      if (rankA !== rankB) return rankA - rankB;

      const keyA = getSportterySortKey(a);
      const keyB = getSportterySortKey(b);
      // 1. Sort by official Business Date / issue_date ascending
      if (keyA[0] !== keyB[0]) return keyA[0].localeCompare(keyB[0]);
      // 2. Sort by Match Code (201 < 202 < ... < 211) ascending
      if (keyA[1] !== keyB[1]) return keyA[1] - keyB[1];
      // 3. Fallback: Kickoff exact timestamp
      return keyA[2].localeCompare(keyB[2]);
    });
  }

  // ─── RENDER APP ───
  function renderApp() {
    const matches = state.matches?.matches || [];
    const rawUpcoming = matches.filter(m => {
      // 1. Exclude finished matches that already have actual_result (they belong exclusively to History Table)
      if (m.status === 'finished' || m.is_finished || m.ultimate_conclusion?.actual_result) return false;
      // 2. Strict on-sale active pending matches only
      return m.status === 'pending' || m.status === 'Pending';
    });
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
      const accEl = document.getElementById('header-accuracy');
      const scoreAccEl = document.getElementById('header-score-accuracy');
      const hfAccEl = document.getElementById('header-hf-accuracy');
      const historyCountEl = document.getElementById('header-history-count');
      const evoCountEl = document.getElementById('header-evo-count');

      const latestVersion = evolution?.snapshots?.slice(-1)[0]?.version || weights?.version || 'v3.5';
      if (versionBadge) versionBadge.textContent = latestVersion;
      if (matchCountEl) matchCountEl.textContent = upcomingMatches.length;

      // M10 竞彩大师 5 维独立开奖命中率 (415场实盘水温训) 专属渲染
      const m10Stats = history?.m10_stats || {};
      const m10HadEl = document.getElementById('m10-acc-had');
      const m10HhadEl = document.getElementById('m10-acc-hhad');
      const m10GoalsEl = document.getElementById('m10-acc-goals');
      const m10ScoreEl = document.getElementById('m10-acc-score');
      const m10HafuEl = document.getElementById('m10-acc-hafu');

      if (m10HadEl) m10HadEl.textContent = m10Stats.had !== undefined ? (m10Stats.had * 100).toFixed(1) + '%' : '--%';
      if (m10HhadEl) m10HhadEl.textContent = m10Stats.hhad !== undefined ? (m10Stats.hhad * 100).toFixed(1) + '%' : '--%';
      if (m10ScoreEl) m10ScoreEl.textContent = m10Stats.crs !== undefined ? (m10Stats.crs * 100).toFixed(1) + '%' : '--%';
      if (m10GoalsEl) m10GoalsEl.textContent = m10Stats.goals !== undefined ? (m10Stats.goals * 100).toFixed(1) + '%' : '--%';
      if (m10HafuEl) m10HafuEl.textContent = m10Stats.hafu !== undefined ? (m10Stats.hafu * 100).toFixed(1) + '%' : '--%';

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
          // 对在售卡片按竞彩官方开售期号 (Date Ascending) 与 组内编号 (Code Ascending 001->006) 正序排列 (与竞彩网完全一致)
          const sortedUpcomingForCards = [...upcomingMatches].sort((a, b) => {
            const getTag = (m) => {
              let t = m.issue_date || m.business_date || '';
              if (!t) {
                const mId = (m.id || '').match(/match_(\d{6})_/);
                t = mId ? mId[1] : (m.kickoff || '').split('T')[0].split(' ')[0].replace(/-/g, '').slice(2);
              }
              return t;
            };
            const dateA = getTag(a);
            const dateB = getTag(b);
            if (dateA !== dateB) return dateA.localeCompare(dateB); // 日期从早到晚
            
            const getNum = (m) => {
              const mid = m.id || m.match_id || '';
              const no = m.match_no || '';
              const mId = mid.match(/_(\d+)$/);
              if (mId) return parseInt(mId[1], 10);
              const mNo = no.match(/(\d+)/);
              if (mNo) return parseInt(mNo[1], 10);
              return 0;
            };
            return getNum(a) - getNum(b); // 组内编号从小到大正序 (001 -> 002 -> 003 -> 004 -> 005 -> 006)
          });

          matchesGrid.innerHTML = sortedUpcomingForCards.map(m => {
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
    const mobileBottomTabs = document.querySelectorAll('.mobile-bottom-tab');
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

      mobileBottomTabs.forEach(tab => {
        if (tab.dataset.target === currentSectionId) {
          tab.classList.add('active');
        } else {
          tab.classList.remove('active');
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
    const allNavLinks = [...sideLinks, ...mobileBottomTabs];
    allNavLinks.forEach(link => {
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
            const matchId = activeTab.dataset.match;
            const tabName = activeTab.dataset.tab;
            if (matchId && tabName) {
              const card = document.getElementById(`card-${matchId}`);
              if (card) {
                card.querySelectorAll('.mc-pane').forEach(p => p.classList.remove('active'));
                const targetPane = document.getElementById(`pane-${matchId}-${tabName}`);
                if (targetPane) targetPane.classList.add('active');
              }
            }
          }
        }
      }
    }

    // Global Event Delegation for Match Card Tabs (.mc-tab)
    const tab = e.target.closest('.mc-tab');
    if (tab) {
      const matchId = tab.dataset.match;
      const tabName = tab.dataset.tab;
      if (!matchId || !tabName) return;

      const tabsBox = tab.parentElement;
      if (tabsBox) {
        tabsBox.querySelectorAll('.mc-tab').forEach(t => t.classList.remove('active'));
      }
      tab.classList.add('active');

      const card = document.getElementById(`card-${matchId}`);
      if (!card) return;
      card.querySelectorAll('.mc-pane').forEach(p => p.classList.remove('active'));
      const targetPane = document.getElementById(`pane-${matchId}-${tabName}`);
      if (targetPane) {
        targetPane.classList.add('active');
        setTimeout(() => {
          const matches = (window.MatchIQ && window.MatchIQ.currentMatches) || [];
          const match = matches.find(m => m.id === matchId || String(m.id).endsWith(matchId));
          if (!match) return;
          if (tabName === 'stats' && window.MatchIQCharts) {
            const buildRadarData = (s) => ({
              winRate: (s?.wins || 0) / (s?.played || 1),
              attackPower: Math.min(1, (s?.goals_scored || 0) / (s?.played || 1) / 2.5),
              defensiveSolidty: Math.max(0, 1 - (s?.goals_conceded || 0) / (s?.played || 1) / 2.5),
              formMomentum: (s?.wins || 0) / (s?.played || 1) * 0.9,
              xgEfficiency: (s?.xg || 1.2) / 2.5
            });
            window.MatchIQCharts.initTeamRadar(
              `radar-${matchId}`,
              buildRadarData(match.team_stats?.home?.season_stats),
              buildRadarData(match.team_stats?.away?.season_stats),
              match.home, match.away
            );
          } else if (tabName === 'factors' && window.MatchIQCharts) {
            const state = window.MatchIQState || {};
            if (typeof getAdjustedWeights === 'function') {
              const adjW = getAdjustedWeights(match, state.weights, state.teamTags, state.tagsConfig, state.leagueProfiles);
              window.MatchIQCharts.initFactorChart(`factor-chart-${matchId}`, {}, adjW);
            }
          }
        }, 50);
      }
    }
  });
});

window.toggleMasterHistorySection = function() {
  const wrapper = document.getElementById('master-history-wrapper');
  const badge = document.getElementById('master-history-toggle-badge');
  if (!wrapper || !badge) return;
  const isHidden = (wrapper.style.display === 'none' || wrapper.style.display === '');
  if (isHidden) {
    wrapper.style.display = 'block';
    badge.innerHTML = '收起预测历史 ▴';
    badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    badge.style.color = '#ef4444';
    badge.style.background = 'rgba(239, 68, 68, 0.08)';
  } else {
    wrapper.style.display = 'none';
    badge.innerHTML = '点击展开预测历史 ▾ (共 97 场完赛)';
    badge.style.borderColor = 'rgba(0, 212, 255, 0.3)';
    badge.style.color = 'var(--cyan)';
    badge.style.background = 'rgba(0, 212, 255, 0.1)';
  }
};

window.runLivePesSimulation = function(matchId) {
  const matches = (window.MatchIQ && window.MatchIQ.currentMatches) || [];
  const match = matches.find(m => m.id === matchId || String(m.id).endsWith(matchId));
  if (!match) {
    alert('未找到该比赛数据，请刷新重试！');
    return;
  }

  let modal = document.getElementById('pes-sim-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'pes-sim-modal';
    modal.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(5, 10, 20, 0.85); backdrop-filter:blur(12px); z-index:99999; display:flex; align-items:center; justify-content:center; padding:16px; opacity:0; transition:opacity 0.3s;';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div style="background:rgba(13,21,39,0.95); border:1px solid rgba(168,85,247,0.4); border-radius:16px; width:100%; max-width:540px; padding:24px; box-shadow:0 20px 50px rgba(0,0,0,0.6); position:relative; text-align:left; color:#e2e8f0; font-family:sans-serif;">
      <button style="position:absolute; top:16px; right:16px; background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer;" onclick="document.getElementById('pes-sim-modal').style.opacity='0'; setTimeout(()=>document.getElementById('pes-sim-modal').style.display='none',300);">✕</button>
      
      <div style="font-size:12px; color:#c084fc; font-weight:800; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">🎮 PES / eFootball 蒙特卡洛足球沙盘</div>
      <div style="font-size:18px; font-weight:800; color:#ffffff; margin-bottom:16px;">
        ${match.home} <span style="color:#94a3b8; font-weight:normal;">VS</span> ${match.away}
      </div>

      <div id="sim-progress-box" style="margin-bottom:20px; background:rgba(0,0,0,0.4); padding:16px; border-radius:10px; border:1px solid rgba(168,85,247,0.2);">
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:8px;">
          <span style="color:#e9d5ff; font-weight:700;">5,000 场平行宇宙沙盘极速推演中...</span>
          <span id="sim-counter-text" style="color:#c084fc; font-weight:800;">0 / 5000 场</span>
        </div>
        <div style="width:100%; height:8px; background:rgba(255,255,255,0.1); border-radius:4px; overflow:hidden;">
          <div id="sim-progress-bar" style="width:0%; height:100%; background:linear-gradient(90deg, #c084fc, #3b82f6); transition:width 0.08s linear;"></div>
        </div>
      </div>

      <div id="sim-result-container" style="display:none;"></div>
    </div>
  `;

  modal.style.display = 'flex';
  setTimeout(() => { modal.style.opacity = '1'; }, 10);

  const progressBar = document.getElementById('sim-progress-bar');
  const counterText = document.getElementById('sim-counter-text');
  const resContainer = document.getElementById('sim-result-container');

  let currentCount = 0;
  const targetCount = 5000;
  const interval = setInterval(() => {
    currentCount += 625;
    if (currentCount >= targetCount) {
      currentCount = targetCount;
      clearInterval(interval);

      const sim = window.PesMonteCarloEngine ? window.PesMonteCarloEngine.runSimulation5000(match) : null;
      if (sim) {
        renderSimResultsInModal(resContainer, sim, match);
      }
    }
    progressBar.style.width = (currentCount / targetCount * 100) + '%';
    counterText.innerText = `${currentCount} / 5000 场`;
  }, 35);

  function renderSimResultsInModal(container, sim, m) {
    const topS = sim.topScores || [];
    const topHF = sim.topHalfFull || [];
    const wild = sim.wildOutliers || [];

    const scoresHtml = topS.map((s, i) => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px; margin-bottom:6px; border:1px solid rgba(255,255,255,0.06);">
        <span style="font-weight:700; color:#e2e8f0;">No.${i+1} 比分 <span style="color:#c084fc; font-size:14px; margin-left:6px;">${s.score}</span></span>
        <span style="font-weight:800; color:#4ade80;">${s.pct} <span style="font-size:11px; color:#94a3b8; font-weight:normal;">(${s.count}场)</span></span>
      </div>`).join('');

    const hfHtml = topHF.map((hf, i) => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:6px 10px; border-radius:6px; margin-bottom:4px;">
        <span style="color:#cbd5e1; font-size:12px;">组合 ${hf.hf}</span>
        <span style="font-weight:700; color:#c084fc; font-size:12px;">${hf.pct}</span>
      </div>`).join('');

    const wildHtml = wild.map(w => `
      <span style="display:inline-block; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.4); color:#fbbf24; padding:3px 8px; border-radius:4px; font-weight:800; font-size:12px; margin-right:6px; margin-bottom:4px;">
        💥 ${w.score} (${w.pct})
      </span>`).join('');

    const styleTagHtml = sim.styleTag ? `
      <div style="margin-bottom:12px; background:${sim.styleTag.bg}; border:1px solid ${sim.styleTag.border}; padding:10px 14px; border-radius:8px; display:flex; align-items:center; justify-content:space-between;">
        <div>
          <span style="font-weight:800; font-size:13.5px; color:${sim.styleTag.color};">${sim.styleTag.name}</span>
          <div style="font-size:11.5px; color:#cbd5e1; margin-top:2px;">💡 ${sim.styleTag.desc}</div>
        </div>
      </div>` : '';

    container.innerHTML = `
      <div style="font-size:13px; font-weight:800; color:#4ade80; margin-bottom:12px; background:rgba(74,222,128,0.1); border:1px solid rgba(74,222,128,0.25); padding:8px 12px; border-radius:6px; text-align:center;">
        ✅ 5,000 次平行宇宙沙盘推演收敛完毕！
      </div>

      ${styleTagHtml}

      <div style="margin-bottom:16px;">
        <div style="font-size:11.5px; color:#94a3b8; margin-bottom:6px;">1,000 场全仿真胜胜负分布表</div>
        <div style="display:flex; height:24px; border-radius:6px; overflow:hidden; font-size:11px; font-weight:800; text-align:center; line-height:24px;">
          <div style="width:${sim.winRate.homePct}%; background:#22c55e; color:#000;">主胜 ${sim.winRate.homePct}%</div>
          <div style="width:${sim.winRate.drawPct}%; background:#64748b; color:#fff;">平 ${sim.winRate.drawPct}%</div>
          <div style="width:${sim.winRate.awayPct}%; background:#ef4444; color:#fff;">客胜 ${sim.winRate.awayPct}%</div>
        </div>
      </div>

      <div style="margin-bottom:14px;">
        <div style="font-size:12px; font-weight:700; color:#e2e8f0; margin-bottom:8px;">🎯 最可能终场比分 Top 4</div>
        ${scoresHtml}
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
        <div>
          <div style="font-size:12px; font-weight:700; color:#e2e8f0; margin-bottom:6px;">半全场热力分布</div>
          ${hfHtml}
        </div>
        <div>
          <div style="font-size:12px; font-weight:700; color:#f87171; margin-bottom:6px;">💥 狂野爆冷比分捕获</div>
          ${wildHtml || '<div style="font-size:11px; color:#64748b;">本场无明显狂野爆冷</div>'}
        </div>
      </div>
    `;
    container.style.display = 'block';
  }
};
