/* ============================================================
   MATCH IQ — Render Module
   All DOM rendering functions for match cards and sections
   ============================================================ */

const MatchIQRender = (() => {

  // ─── HELPERS ───
  const h = (tag, cls, html, attrs = '') =>
    `<${tag} class="${cls}" ${attrs}>${html}</${tag}>`;

  function formatTime(isoStr) {
    if (!isoStr) return '--';
    const d = new Date(isoStr);
    return d.toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit', hour12: false });
  }

  function formatMatchNo(id) {
    if (!id) return '';
    const parts = id.split('_');
    if (parts.length >= 3) {
      return `No.${parts[parts.length - 1]}`;
    }
    return id.replace('match_', 'No.');
  }

  function formatDate(isoStr) {
    if (!isoStr) return '初始化';
    const d = new Date(isoStr);
    return d.toLocaleString('zh-CN', { year:'numeric', month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' });
  }

  function riskClass(risk) {
    if (!risk) return '';
    if (risk.includes('低')) return 'risk-low';
    if (risk.includes('中')) return 'risk-mid';
    return 'risk-high';
  }

  function recColor(confidence) {
    if (confidence >= 70) return 'green';
    if (confidence >= 55) return 'cyan';
    if (confidence >= 40) return 'amber';
    return 'red';
  }

  function formDots(form) {
    if (!form || !Array.isArray(form)) return '';
    return form.map(r => `<span class="form-dot ${r}">${r}</span>`).join('');
  }

  function oddsChangeClass(initial, current) {
    if (current < initial - 0.02) return 'odds-down';
    if (current > initial + 0.02) return 'odds-up';
    return 'odds-stable';
  }

  function oddsArrow(initial, current) {
    if (current < initial - 0.02) return '↓';
    if (current > initial + 0.02) return '↑';
    return '—';
  }

  function newsImpactClass(impact) {
    if (!impact) return 'neutral';
    if (impact.includes('利好') || impact.includes('正面')) return 'positive';
    if (impact.includes('利空') || impact.includes('负面')) return 'negative';
    return 'neutral';
  }

  function mpPredClass(pred) {
    if (!pred) return '';
    if (pred.includes('主')) return 'home';
    if (pred.includes('平')) return 'draw';
    if (pred.includes('客')) return 'away';
    return '';
  }

  function attitudeClass(att) {
    if (!att) return 'neutral';
    if (att.includes('引导') || att.includes('陷阱')) return 'trap';
    if (att.includes('保护')) return 'protect';
    return 'neutral';
  }

  function riskBadgeClass(risk) {
    if (!risk) return 'mid';
    if (risk.includes('极高') || risk.includes('高')) return 'hi';
    if (risk.includes('极低') || risk.includes('低')) return 'low';
    return 'mid';
  }

  // ─── ULTIMATE CONCLUSION CARD ───
  function renderUltimateCard(match) {
    const uc = match.ultimate_conclusion || {};
    const home = match.team_stats?.home || {};
    const away = match.team_stats?.away || {};
    const conf = uc.confidence || 0;
    const color = recColor(conf);
    const rClass = riskClass(uc.risk_level || '中');

    const isHighUpsetRisk = (match.conclusions?.upset_probability || 0) >= 0.35;
    const warningBadge = isHighUpsetRisk ? `<span class="upset-warning-badge glow-pulse">⚠ 爆冷预警</span>` : '';
    const isUpdated = match.prediction_updated === true;
    const updatedBadge = isUpdated ? `<span class="prediction-updated-badge">⚡ 预测更新</span>` : '';

    return `
    <div class="ultimate-card ${rClass} animate-in" id="uc-${match.id}">
      <div class="uc-header">
        <span class="uc-league"><span class="match-no-badge">${formatMatchNo(match.id)}</span>${match.league || '--'}${warningBadge}${updatedBadge}</span>
        <span class="uc-kickoff">${formatTime(match.kickoff)}</span>
      </div>
      <div class="uc-teams">
        <div class="uc-team">
          <div class="uc-team-name">${match.home || '主队'}</div>
          <div class="uc-team-form">${formDots(home.form)}</div>
        </div>
        <div class="vs-badge">VS</div>
        <div class="uc-team away">
          <div class="uc-team-name">${match.away || '客队'}</div>
          <div class="uc-team-form">${formDots(away.form)}</div>
        </div>
      </div>
      <div class="uc-conclusion">
        <div class="uc-rec-label">终极结论</div>
        <div class="uc-rec-value ${color}">${uc.recommendation || '分析中'}</div>
        <div class="confidence-bar">
          <div class="confidence-fill" style="width:${conf}%"></div>
        </div>
        <div class="uc-metrics">
          <div class="uc-metric">
            <div class="m-val text-cyan">${conf}%</div>
            <div class="m-lbl">信心</div>
          </div>
          <div class="uc-metric">
            <div class="m-val" style="color: ${uc.risk_level?.includes('低') ? 'var(--green)' : uc.risk_level?.includes('高') ? 'var(--red)' : 'var(--amber)'}">
              ${uc.risk_level || '--'}
            </div>
            <div class="m-lbl">风险</div>
          </div>
          <div class="uc-metric">
            <div class="m-val text-green">${match.conclusions?.most_likely_score || '--'}</div>
            <div class="m-lbl">最可能比分</div>
          </div>
        </div>
        <div class="uc-reasoning">${uc.reasoning || '等待分析数据'}</div>
      </div>
    </div>`;
  }

  // ─── STATS PANE ───
  function renderStatsPane(match, paneId) {
    const home = match.team_stats?.home?.season_stats || {};
    const away = match.team_stats?.away?.season_stats || {};
    const h2h  = match.head_to_head || {};

    const statRows = [
      { name: '进球', h: home.goals_scored, a: away.goals_scored },
      { name: '失球', h: home.goals_conceded, a: away.goals_conceded },
      { name: 'xG', h: home.xg?.toFixed(1), a: away.xg?.toFixed(1) },
      { name: 'xGA', h: home.xga?.toFixed(1), a: away.xga?.toFixed(1) },
      { name: '每场射门', h: home.shots_per_game?.toFixed(1), a: away.shots_per_game?.toFixed(1) },
      { name: '射正', h: home.shots_on_target?.toFixed(1), a: away.shots_on_target?.toFixed(1) },
      { name: '转化率', h: home.conversion_rate ? (home.conversion_rate*100).toFixed(1)+'%' : '--', a: away.conversion_rate ? (away.conversion_rate*100).toFixed(1)+'%' : '--' },
      { name: '控球率', h: home.possession?.toFixed(1)+'%', a: away.possession?.toFixed(1)+'%' },
      { name: '传球成功率', h: home.pass_accuracy?.toFixed(1)+'%', a: away.pass_accuracy?.toFixed(1)+'%' },
      { name: '定位球进球', h: home.set_piece_goals, a: away.set_piece_goals },
      { name: '零封场数', h: home.clean_sheets, a: away.clean_sheets },
      { name: '大球率', h: home.over25_rate ? (home.over25_rate*100).toFixed(0)+'%' : '--', a: away.over25_rate ? (away.over25_rate*100).toFixed(0)+'%' : '--' },
    ];

    const rows = statRows.map(r => {
      const hv = r.h ?? '--'; const av = r.a ?? '--';
      const hn = parseFloat(hv) || 0; const an = parseFloat(av) || 0;
      const total = hn + an || 1;
      const homeW = (hn / total * 100).toFixed(0);
      return `
        <div class="stat-row">
          <div class="stat-val home">${hv}</div>
          <div class="stat-name">${r.name}</div>
          <div class="stat-val away">${av}</div>
          <div class="stat-bar-wrap">
            <div class="stat-bar-home" style="width:${homeW}%"></div>
            <div class="stat-bar-away"></div>
          </div>
        </div>`;
    }).join('');

    // H2H summary
    const hasH2H = h2h && h2h.last_5 && h2h.last_5.length > 0;
    const h2hResult = hasH2H ? h2h.last_5.map(r => `<span class="form-dot ${r === 'H' ? 'W' : r === 'A' ? 'L' : 'D'}" style="width:22px;height:22px;font-size:10px">${r === 'H' ? '主' : r === 'A' ? '客' : '平'}</span>`).join('') : '';

    return `
    <div class="mc-pane ${paneId === 'stats' ? 'active' : ''}" id="pane-${match.id}-stats">
      <div class="stats-grid">
        <div>
          <div class="chart-box">
            <canvas id="radar-${match.id}"></canvas>
          </div>
        </div>
        <div class="stats-table">${rows}</div>
      </div>
      <div style="margin-top:20px; padding:14px; background:rgba(255,255,255,0.02); border:1px solid var(--border-subtle); border-radius:var(--radius);">
        <div style="font-size:12px;color:var(--text-3);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">交锋历史（近5场）</div>
        ${hasH2H ? `
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          <div style="display:flex;gap:4px;">${h2hResult}</div>
          <span class="tag">平均进球 ${h2h.avg_goals || '--'}</span>
          <span class="tag">双方进球率 ${h2h.btts_rate ? (h2h.btts_rate*100).toFixed(0)+'%' : '--'}</span>
        </div>` : `<div style="font-size:13px;color:var(--text-4);padding:4px 0;">双方无历史交锋</div>`}
      </div>
    </div>`;
  }

  // ─── ODDS PANE ───
  function renderOddsPane(match) {
    const odds = match.odds_analysis || {};
    const bookKeys = ['pinnacle', 'sbobet', 'nova88', 'crown', 'hkjc', 'm8bet'];
    const fallbackKeys = ['company_1', 'company_2', 'company_3'];
    const bookNames = {
      pinnacle: "平博 (Pinnacle)",
      sbobet: "利记 (SBOBET)",
      nova88: "新宝 (Nova88)",
      crown: "皇冠 (Crown)",
      hkjc: "马会 (HKJC)",
      m8bet: "沙巴 (M8Bet)"
    };

    let activeKeys = bookKeys.filter(k => odds[k]);
    if (activeKeys.length === 0) {
      activeKeys = fallbackKeys.filter(k => odds[k]);
    }

    const oddsRows = activeKeys.map(k => {
      const co = odds[k];
      const name = co.name || bookNames[k] || k;
      const hi = co.initial; const hc = co.current;
      return `
        <tr>
          <td style="text-align:left;color:var(--text-2);font-weight:600">${name}</td>
          <td>${hi.home?.toFixed(2)}</td>
          <td class="odds-val ${oddsChangeClass(hi.home, hc.home)}">${hc.home?.toFixed(2)} <span class="movement-arrow">${oddsArrow(hi.home, hc.home)}</span></td>
          <td>${hi.draw?.toFixed(2)}</td>
          <td class="odds-val ${oddsChangeClass(hi.draw, hc.draw)}">${hc.draw?.toFixed(2)} <span class="movement-arrow">${oddsArrow(hi.draw, hc.draw)}</span></td>
          <td>${hi.away?.toFixed(2)}</td>
          <td class="odds-val ${oddsChangeClass(hi.away, hc.away)}">${hc.away?.toFixed(2)} <span class="movement-arrow">${oddsArrow(hi.away, hc.away)}</span></td>
          <td style="color:var(--text-3);font-size:11px">${co.movement || '平稳'}</td>
        </tr>`;
    }).join('');

    const ah = odds.asian_handicap || {};
    const jc = odds.lottery_handicap || {};
    const ou = odds.over_under || {};

    const smokes = (odds.smoke_screens || []).map(s =>
      `<li>${s}</li>`
    ).join('');

    const retail = odds.retail_sentiment || {};
    const homeP = Math.round((retail.home_support || 0) * 100);
    const drawP = Math.round((retail.draw_support || 0) * 100);
    const awayP = Math.round((retail.away_support || 0) * 100);

    const traps = OddsAnalyzer.analyzeRetailTrap(match);
    const trapsHtml = traps.map(t => `
      <div style="padding:10px 12px;background:${t.severity==='HIGH'?'var(--red-dim)':'var(--amber-dim)'};border:1px solid ${t.severity==='HIGH'?'rgba(239,68,68,0.3)':'rgba(245,158,11,0.3)'};border-radius:var(--radius-sm);margin-bottom:8px;">
        <span style="font-size:11px;color:${t.severity==='HIGH'?'var(--red)':'var(--amber)'};font-weight:600">${t.outcome} — ${t.severity === 'HIGH' ? '⚠ 高风险陷阱' : '注意'}</span>
        <p style="font-size:12px;color:var(--text-2);margin-top:4px">${t.message}</p>
      </div>`).join('');

    return `
    <div class="mc-pane" id="pane-${match.id}-odds">
      <div class="odds-section">
        <div class="odds-section-title">欧赔对比（初盘 vs 即时盘）</div>
        <div style="overflow-x:auto;">
          <table class="odds-table">
            <thead>
              <tr>
                <th>公司</th>
                <th>主初</th><th>主即</th>
                <th>平初</th><th>平即</th>
                <th>客初</th><th>客即</th>
                <th>走势</th>
              </tr>
            </thead>
            <tbody>${oddsRows || '<tr><td colspan="8" style="color:var(--text-4);text-align:center;padding:20px">暂无数据</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="odds-section" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:16px;margin-top:16px">
        <div style="padding:16px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);">
          <div class="odds-section-title">亚盘分析</div>
          <div style="font-size:13px;color:var(--text-2)">
            <div style="margin-bottom:8px">初盘让球：<span class="font-mono text-cyan">${ah.initial?.handicap || '--'}</span></div>
            <div style="margin-bottom:8px">主 ${ah.initial?.home_odds || '--'} → <span class="odds-val ${oddsChangeClass(ah.initial?.home_odds||0, ah.current?.home_odds||0)}">${ah.current?.home_odds || '--'}</span></div>
            <div style="margin-bottom:8px">客 ${ah.initial?.away_odds || '--'} → <span class="odds-val ${oddsChangeClass(ah.initial?.away_odds||0, ah.current?.away_odds||0)}">${ah.current?.away_odds || '--'}</span></div>
            <div style="font-size:12px;color:var(--text-3);margin-top:8px">${ah.movement_signal || '--'}</div>
          </div>
        </div>
        <div style="padding:16px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);">
          <div class="odds-section-title">竞彩让球</div>
          <div style="font-size:13px;color:var(--text-2)">
            <div style="margin-bottom:8px">让球规格：<span class="font-mono text-rose">${jc.handicap || '--'}</span></div>
            <div style="margin-bottom:8px">让胜 ${jc.initial?.win || '--'} → <span class="odds-val ${oddsChangeClass(jc.initial?.win||0, jc.current?.win||0)}">${jc.current?.win || '--'}</span></div>
            <div style="margin-bottom:8px">让平 ${jc.initial?.draw || '--'} → <span class="odds-val ${oddsChangeClass(jc.initial?.draw||0, jc.current?.draw||0)}">${jc.current?.draw || '--'}</span></div>
            <div style="margin-bottom:8px">让负 ${jc.initial?.lose || '--'} → <span class="odds-val ${oddsChangeClass(jc.initial?.lose||0, jc.current?.lose||0)}">${jc.current?.lose || '--'}</span></div>
          </div>
        </div>
        <div style="padding:16px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);">
          <div class="odds-section-title">大小球分析</div>
          <div style="font-size:13px;color:var(--text-2)">
            <div style="margin-bottom:8px">盘口：<span class="font-mono text-cyan">${ou.initial?.line || '--'} 球</span></div>
            <div style="margin-bottom:8px">大初 ${ou.initial?.over || '--'} → <span class="odds-val ${oddsChangeClass(ou.initial?.over||0, ou.current?.over||0)}">${ou.current?.over || '--'}</span></div>
            <div style="margin-bottom:8px">小初 ${ou.initial?.under || '--'} → <span class="odds-val ${oddsChangeClass(ou.initial?.under||0, ou.current?.under||0)}">${ou.current?.under || '--'}</span></div>
            <div style="font-size:12px;color:var(--text-3);margin-top:8px">${ou.signal || '--'}</div>
          </div>
        </div>
      </div>

      <div class="bookmaker-intent">
        <h4>🎯 庄家意图推演</h4>
        <p>${odds.bookmaker_intent || '暂无分析'}</p>
      </div>

      ${smokes ? `<div class="smoke-screens"><h4>💨 烟雾弹识别</h4><ul>${smokes}</ul></div>` : ''}

      ${trapsHtml ? `<div style="margin-top:16px"><div style="font-size:12px;color:var(--text-3);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">散户陷阱分析</div>${trapsHtml}</div>` : ''}

      <div class="retail-sentiment">
        <h4>📊 散户押注分布</h4>
        <div class="sentiment-bars">
          <div class="sentiment-row">
            <div class="sentiment-label">主胜</div>
            <div class="sentiment-bar-wrap"><div class="sentiment-bar-fill home" style="width:${homeP}%"></div></div>
            <div class="sentiment-pct">${homeP}%</div>
          </div>
          <div class="sentiment-row">
            <div class="sentiment-label">平局</div>
            <div class="sentiment-bar-wrap"><div class="sentiment-bar-fill draw" style="width:${drawP}%"></div></div>
            <div class="sentiment-pct">${drawP}%</div>
          </div>
          <div class="sentiment-row">
            <div class="sentiment-label">客胜</div>
            <div class="sentiment-bar-wrap"><div class="sentiment-bar-fill away" style="width:${awayP}%"></div></div>
            <div class="sentiment-pct">${awayP}%</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--text-3);margin-top:12px">
          散户信心：<span class="text-amber">${retail.confidence_level || '--'}</span> &nbsp;·&nbsp;
          主流叙事：${retail.mainstream_narrative || '--'}
        </div>
      </div>


      <div style="margin-top:16px;padding:16px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);">
        <div style="font-size:12px;color:var(--text-3);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px">散户vs庄家视角对比</div>
        <div style="overflow-x:auto;">
          <table class="pvb-table">
            <thead><tr>
              <th>结果</th><th>散户预期</th><th>庄家隐含</th><th>真实估计</th><th>赔付风险</th><th>庄家态度</th>
            </tr></thead>
            <tbody>
              ${(match.public_vs_bookmaker || []).map(r => `
                <tr>
                  <td style="font-weight:600">${r.outcome}</td>
                  <td>${r.public_prob}</td>
                  <td>${r.bookmaker_implied}</td>
                  <td style="color:var(--cyan);font-family:var(--font-mono)">${r.true_est}</td>
                  <td><span class="risk-badge ${riskBadgeClass(r.payout_risk)}">${r.payout_risk}</span></td>
                  <td><span class="attitude-badge ${attitudeClass(r.bookmaker_attitude)}">${r.bookmaker_attitude}</span></td>
                </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-4);padding:20px">暂无数据</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </div>`;
  }

  // ─── INTELLIGENCE PANE ───
  function renderIntelPane(match) {
    const intel = match.intelligence || {};
    const news = intel.verified_news || [];
    const mediaPreds = intel.media_predictions || [];

    const newsHtml = news.map(n => `
      <div class="news-item">
        <div class="news-header">
          <div class="news-title">${n.title}</div>
          <span class="news-impact ${newsImpactClass(n.impact)}">${n.impact || '--'}</span>
        </div>
        <div class="news-meta">
          <span>${n.source}</span>
          <span>·</span>
          <span>${n.date || '--'}</span>
          ${n.verified ? '<span class="verified-badge">✓ 已验证</span>' : ''}
          ${n.url ? `<a href="${n.url}" target="_blank" style="font-size:10px;color:var(--cyan)">查看原文 →</a>` : ''}
        </div>
      </div>`).join('') || '<div style="color:var(--text-4);font-size:13px;text-align:center;padding:20px">暂无已验证新闻</div>';

    const predHtml = mediaPreds.map(p => `
      <div class="media-pred-item">
        <div class="mp-source">${p.source}</div>
        <div class="mp-prediction ${mpPredClass(p.prediction)}">${p.prediction}</div>
        <div class="mp-score">${p.score || '--'}</div>
      </div>`).join('') || '<div style="color:var(--text-4);font-size:13px;text-align:center;padding:20px">暂无媒体预测</div>';

    return `
    <div class="mc-pane" id="pane-${match.id}-intel">
      <div class="intel-grid">
        <div>
          <div style="font-size:13px;font-weight:600;color:var(--text-2);margin-bottom:12px;text-transform:uppercase;letter-spacing:1px">已验证新闻</div>
          <div class="news-list">${newsHtml}</div>
        </div>
        <div>
          <div class="media-predictions">
            <div class="media-pred-title">媒体预测方向</div>
            <div class="media-pred-list">${predHtml}</div>
          </div>
          <div style="margin-top:20px;padding:14px;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:var(--radius);">
            <div style="font-size:12px;color:var(--indigo);font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px">社媒热议</div>
            ${intel.social_buzz ? `
              <div style="font-size:13px;color:var(--text-2);line-height:1.6">
                <div style="margin-bottom:8px">情绪：${intel.social_buzz.sentiment || '--'}</div>
                <div style="margin-bottom:8px">${intel.social_buzz.notable_discussion || '--'}</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
                  ${(intel.social_buzz.trending_keywords || []).map(kw =>
                    `<span class="tag">#${kw}</span>`
                  ).join('')}
                </div>
              </div>` : '<div style="color:var(--text-4);font-size:13px">暂无数据</div>'}
          </div>
          ${intel.weather_impact ? `
            <div style="margin-top:12px;padding:12px 14px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);font-size:12px;color:var(--text-3)">
              🌡 ${intel.weather_impact}
            </div>` : ''}
          ${intel.venue_notes ? `
            <div style="margin-top:8px;padding:12px 14px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);font-size:12px;color:var(--text-3)">
              🏟 ${intel.venue_notes}
            </div>` : ''}
        </div>
      </div>
    </div>`;
  }

  // ─── CONCLUSIONS PANE ───
  function renderConclusionsPane(match) {
    const c = match.conclusions || {};
    const upsetPct = c.upset_probability ? (c.upset_probability * 100).toFixed(0) : '0';

    return `
    <div class="mc-pane" id="pane-${match.id}-conclusions">
      <div class="conclusions-grid">
        <div class="conclusion-card mainstream">
          <div class="cc-label">主流方向</div>
          <div class="cc-value">${c.mainstream || '--'}</div>
        </div>
        <div class="conclusion-card upset">
          <div class="cc-label">冷门方向</div>
          <div class="cc-value">${c.upset || '--'}</div>
        </div>
        <div class="conclusion-card aggressive">
          <div class="cc-label">激进结论</div>
          <div class="cc-value">${c.aggressive || '--'}</div>
        </div>
        <div class="conclusion-card conservative">
          <div class="cc-label">信心结论</div>
          <div class="cc-value">${c.conservative || '--'}</div>
        </div>
      </div>
      <div class="conclusion-summary">
        <div class="cs-item">
          <div class="cs-label">最可能比分</div>
          <div class="cs-value">${c.most_likely_score || '--'}</div>
        </div>
        <div class="cs-item">
          <div class="cs-label">大小球</div>
          <div class="cs-value">${c.over_under || '--'}</div>
        </div>
        <div class="cs-item">
          <div class="cs-label">半/全场</div>
          <div class="cs-value">${c.half_full || '--'}</div>
        </div>
      </div>
      <div class="upset-probability">
        <div class="up-pct">${upsetPct}%</div>
        <div class="up-info">
          <div class="up-title">冷门概率</div>
          <div class="up-direction">方向：${c.upset_direction || '未知'}</div>
        </div>
      </div>
    </div>`;
  }

  // ─── FACTORS PANE ───
  function renderFactorsPane(match, weightsData) {
    const factors = weightsData?.factors || [];
    const rows = factors.map(f => {
      const maxW = 0.15;
      const barW = Math.min((f.weight / maxW) * 100, 100).toFixed(0);
      const delta = f.delta || 0;
      const deltaClass = delta > 0.0001 ? 'up' : delta < -0.0001 ? 'down' : 'neutral';
      const deltaStr = delta === 0 ? '--' : (delta > 0 ? '+' : '') + (delta * 100).toFixed(2) + '%';
      return `
        <div class="factor-row">
          <span class="factor-id">${f.id}</span>
          <span class="factor-name" title="${f.name}">${f.name}</span>
          <span class="factor-weight">${(f.weight * 100).toFixed(2)}%</span>
          <span class="factor-delta ${deltaClass}">${deltaStr}</span>
          <div class="factor-bar-wrap"><div class="factor-bar-fill" style="width:${barW}%"></div></div>
        </div>`;
    }).join('');

    return `
    <div class="mc-pane" id="pane-${match.id}-factors">
      <div style="margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <div style="font-size:12px;color:var(--text-3);margin-bottom:4px;text-transform:uppercase;letter-spacing:1px">模型版本 ${weightsData?.version || '--'}</div>
          <div style="font-size:13px;color:var(--text-2)">共 ${factors.length} 个决策因子 · 已验证 ${weightsData?.total_matches_validated || 0} 场</div>
        </div>
        <div style="position:relative;height:180px;width:240px;">
          <canvas id="factor-chart-${match.id}"></canvas>
        </div>
      </div>
      <div class="factors-grid">${rows}</div>
    </div>`;
  }

  // ─── FULL MATCH CARD ───
  function renderMatchCard(match, weightsData) {
    const home = match.team_stats?.home || {};
    const away = match.team_stats?.away || {};
    const w = match.weather || {};

    const isHighUpsetRisk = (match.conclusions?.upset_probability || 0) >= 0.35;
    const warningBadge = isHighUpsetRisk ? `<span class="upset-warning-badge glow-pulse">⚠ 爆冷预警</span>` : '';
    const isUpdated = match.prediction_updated === true;
    const updatedBadge = isUpdated ? `<span class="prediction-updated-badge">⚡ 预测更新</span>` : '';

    return `
    <div class="match-card animate-in" id="card-${match.id}">
      <div class="mc-header">
        <div class="mc-team">
          <div class="mc-team-league"><span class="match-no-badge">${formatMatchNo(match.id)}</span>${match.league || ''}${warningBadge}${updatedBadge}</div>
          <div class="mc-team-name">${match.home || '主队'}</div>
          <div class="mc-team-xg">xG ${home.season_stats?.xg?.toFixed(1) || '--'} · 射门 ${home.season_stats?.shots_per_game || '--'}/场</div>
        </div>
        <div class="mc-center">
          <div class="mc-vs">VS</div>
          <div class="mc-kickoff">${formatTime(match.kickoff)}</div>
          <div class="mc-venue">🏟 ${match.venue || '--'}</div>
          <div class="mc-weather">${w.condition ? `🌡 ${w.temp_c}°C · ${w.condition} · 湿度${w.humidity}%` : ''}</div>
        </div>
        <div class="mc-team away">
          <div class="mc-team-league">&nbsp;</div>
          <div class="mc-team-name">${match.away || '客队'}</div>
          <div class="mc-team-xg">xG ${away.season_stats?.xg?.toFixed(1) || '--'} · 射门 ${away.season_stats?.shots_per_game || '--'}/场</div>
        </div>
      </div>
      <button class="collapsible-trigger" data-expand-text="展开分析数据与盘口详情 ▾" data-collapse-text="收起分析数据与盘口详情 ▴">展开分析数据与盘口详情 ▾</button>
      <div class="collapsible-body">
        <div class="mc-tabs" id="tabs-${match.id}">
          <div class="mc-tab active" data-tab="stats"   data-match="${match.id}">📊 数据</div>
          <div class="mc-tab"        data-tab="odds"    data-match="${match.id}">💹 盘口</div>
          <div class="mc-tab"        data-tab="intel"   data-match="${match.id}">🔍 情报</div>
          <div class="mc-tab"        data-tab="conclusions" data-match="${match.id}">🎯 结论</div>
          <div class="mc-tab"        data-tab="factors" data-match="${match.id}">⚙️ 因子</div>
        </div>

        ${renderStatsPane(match, 'stats')}
        ${renderOddsPane(match)}
        ${renderIntelPane(match)}
        ${renderConclusionsPane(match)}
        ${renderFactorsPane(match, weightsData)}
      </div>
    </div>`;
  }

  // ─── MODEL STATUS BAR ───
  function renderModelStatus(weightsData, historyData, evolutionData) {
    const acc = historyData?.accuracy_rate;
    const accStr = acc !== null && acc !== undefined ? (acc * 100).toFixed(1) + '%' : '--';
    const validated = historyData?.total_predictions || 0;
    const version = weightsData?.version || 'v1.0';
    const evoCount = evolutionData?.evolution_count || 0;

    return `
    <div class="model-status-bar">
      <div class="ms-item">
        <div class="ms-val">${version}</div>
        <div class="ms-lbl">模型版本</div>
      </div>
      <div class="ms-divider"></div>
      <div class="ms-item">
        <div class="ms-val">${validated}</div>
        <div class="ms-lbl">已验证场次</div>
      </div>
      <div class="ms-divider"></div>
      <div class="ms-item">
        <div class="ms-val" style="color:${acc ? 'var(--green)' : 'var(--text-3)'}">${accStr}</div>
        <div class="ms-lbl">总体准确率</div>
      </div>
      <div class="ms-divider"></div>
      <div class="ms-item">
        <div class="ms-val">${evoCount}</div>
        <div class="ms-lbl">进化次数</div>
      </div>
      <div class="ms-divider"></div>
      <div class="ms-item">
        <div class="ms-val" style="font-size:12px;color:var(--text-3)">${formatDate(weightsData?.last_evolved)}</div>
        <div class="ms-lbl">上次进化</div>
      </div>
      <button class="ms-expand-btn" id="evolution-toggle">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        查看进化图表
      </button>
    </div>`;
  }

  // ─── EVOLUTION SECTION ───
  function renderEvolutionSection(evolutionData, historyData) {
    const snapshots = evolutionData?.snapshots || [];
    const latest = snapshots[snapshots.length - 1] || {};
    const evoCount = evolutionData?.evolution_count || 0;

    return `
    <div class="evolution-grid">
      <div class="evo-card">
        <div class="evo-card-title">权重进化历史</div>
        <div class="evo-chart-wrap">
          <canvas id="evolution-chart"></canvas>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="evo-card">
          <div class="evo-card-title">准确率趋势</div>
          <div style="position:relative;height:160px;">
            <canvas id="accuracy-chart"></canvas>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div class="evo-meta-item">
            <div class="evo-meta-val">${evoCount}</div>
            <div class="evo-meta-lbl">进化次数</div>
          </div>
          <div class="evo-meta-item">
            <div class="evo-meta-val">${latest.matches_validated || 0}</div>
            <div class="evo-meta-lbl">触发进化的验证场次</div>
          </div>
          <div class="evo-meta-item">
            <div class="evo-meta-val" style="font-size:14px">${latest.date || '等待首次进化'}</div>
            <div class="evo-meta-lbl">最新进化日期</div>
          </div>
        </div>
      </div>
    </div>
    ${snapshots.length > 1 && latest.significant_changes?.length ? `
    <div style="margin-top:20px;padding:16px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:var(--radius);">
      <div style="font-size:12px;color:var(--text-3);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px">最新进化显著变动</div>
      ${latest.significant_changes.map(c => `
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border-subtle);">
          <span style="font-size:13px;color:var(--text-2)">${c.factor}</span>
          <span style="font-family:var(--font-mono);font-size:12px;color:${c.direction==='up'?'var(--green)':'var(--red)'}">${c.direction==='up'?'↑':'↓'} ${c.change}</span>
          <span style="font-size:11px;color:var(--text-4)">${c.reason || ''}</span>
        </div>`).join('')}
    </div>` : ''}`;
  }

  // ─── HISTORY RECORDS SECTION ───
  function renderHistoryRecords(historyData) {
    const records = historyData?.records || [];
    if (records.length === 0) {
      return `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);border:1px dashed var(--border);border-radius:var(--radius)">暂无已完赛预测历史</div>`;
    }

    // 只保留最近十场，按时间倒序排列
    const recordsToShow = [...records].slice(-10).reverse();

    // 辅助函数：根据预测正确性打勾
    const renderPredRow = (label, item, customStyle = '') => {
      if (!item) return '';
      const val = typeof item === 'object' ? (item.val || '--') : item;
      const isCorrect = typeof item === 'object' ? !!item.correct : false;
      const checkmark = isCorrect ? ' <span style="color:var(--green);font-weight:bold;margin-left:4px">✅</span>' : '';
      
      return `
        <div class="hc-pred-row">
          <span class="hc-label">${label}</span>
          <span class="hc-val" ${customStyle ? `style="${customStyle}"` : ''}>${val}${checkmark}</span>
        </div>
      `;
    };

    return recordsToShow.map(r => {
      const p = r.predictions || {};
      const hasPreds = !!r.predictions;

      const predDetailsHTML = hasPreds ? `
        ${renderPredRow('终极结论', p.recommendation, 'color:var(--cyan);font-weight:600')}
        ${renderPredRow('首选方案', p.primary_bet)}
        ${renderPredRow('大众剧本', p.mainstream, 'font-size:11px;text-align:right;max-width:65%;word-break:break-all')}
        ${renderPredRow('激进结论', p.aggressive, 'color:var(--rose);font-size:11px;text-align:right;max-width:65%;word-break:break-all')}
        ${renderPredRow('防守路线', p.conservative, 'font-size:11px;text-align:right;max-width:65%;word-break:break-all')}
        ${renderPredRow('冷门方向', p.upset, 'color:var(--amber);font-size:11px;text-align:right;max-width:65%;word-break:break-all')}
        ${renderPredRow('半全场预测', p.half_full, 'font-size:11px;text-align:right;max-width:65%;word-break:break-all')}
        ${renderPredRow('大小球', p.over_under)}
        ${renderPredRow('预期比分', p.most_likely_score, 'font-weight:600;color:var(--green)')}
      ` : `
        <div class="hc-pred-row">
          <span class="hc-label">模型预测</span>
          <span class="hc-val">${r.prediction || '--'}</span>
        </div>
      `;

      return `
      <div class="history-card ${r.is_correct ? 'correct' : 'incorrect'} animate-in">
        <div class="hc-header">
          <span class="hc-league">${r.league || '--'}</span>
          <span class="hc-date">${r.date || '--'}</span>
        </div>
        <div class="hc-teams">${r.home || '主队'} vs ${r.away || '客队'}</div>
        <button class="collapsible-trigger" data-expand-text="查看预测详情 ▾" data-collapse-text="收起预测详情 ▴">查看预测详情 ▾</button>
        <div class="collapsible-body">
          ${predDetailsHTML}
        </div>
        <div class="hc-pred-row" style="border-top:1px solid rgba(255,255,255,0.08);margin-top:8px;padding-top:8px;">
          <span class="hc-label">实际赛果</span>
          <span class="hc-val ${r.is_correct ? 'highlight-correct' : 'highlight-incorrect'}" style="font-weight:600">${r.actual_result || '--'}</span>
        </div>
        <div class="hc-pred-row">
          <span class="hc-label">预测状态</span>
          <span class="hc-status-badge ${r.is_correct ? 'correct' : 'incorrect'}">${r.is_correct ? '预测正确' : '预测偏差'}</span>
        </div>
        <div class="hc-pred-row">
          <span class="hc-label">信心指数</span>
          <span class="hc-val">${r.confidence || '--'}%</span>
        </div>
      </div>
      `;
    }).join('');
  }

  // ─── EV PARLAYS RENDERER ───
  function renderParlays(matches) {
    const activeMatches = (matches || []).filter(m => m.status === 'pending' && m.odds_analysis && m.odds_analysis.pinnacle);
    if (activeMatches.length < 2) {
      return `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);border:1px dashed var(--border);border-radius:var(--radius)">待入场赛事少于2场，无法组合串关</div>`;
    }

    // Map each match to its Value and Aggressive options
    const parsedBets = activeMatches.map((m, index) => {
      const oddsObj = m.odds_analysis.pinnacle.current;
      const fair = {};
      const total = (1/oddsObj.home) + (1/oddsObj.draw) + (1/oddsObj.away);
      fair.home = (1/oddsObj.home) / total;
      fair.draw = (1/oddsObj.draw) / total;
      fair.away = (1/oddsObj.away) / total;

      const rec = m.ultimate_conclusion.recommendation || '';
      const conclusions = m.conclusions || {};

      // ─── 1. VALUE OPTION (Optimized for High Success Rate / Lower Payout) ───
      let valChoiceName = '';
      let valOdds = 0;
      let valProb = 0;

      if (oddsObj) {
        if (fair.home > 0.50) {
          valChoiceName = `${m.home} 不败 (双平胜)`;
          const dcOdds = 0.95 / ((1/oddsObj.home) + (1/oddsObj.draw));
          valOdds = Math.max(dcOdds, 1.15);
          valProb = Math.min(fair.home + fair.draw, 0.90);
        } else if (fair.away > 0.50) {
          valChoiceName = `${m.away} 不败 (双平负)`;
          const dcOdds = 0.95 / ((1/oddsObj.away) + (1/oddsObj.draw));
          valOdds = Math.max(dcOdds, 1.15);
          valProb = Math.min(fair.away + fair.draw, 0.90);
        } else {
          if (rec.includes('客胜') || rec.includes('客') || rec.includes('让负')) {
            valChoiceName = `${m.away} (+1.5受让胜)`;
            valOdds = 1.28;
            valProb = Math.min(fair.away + fair.draw + 0.12, 0.92);
          } else {
            valChoiceName = `${m.home} (+1.5受让胜)`;
            valOdds = 1.28;
            valProb = Math.min(fair.home + fair.draw + 0.12, 0.92);
          }
        }
      } else {
        valChoiceName = `${m.home} 胜/平`;
        valOdds = 1.35;
        valProb = 0.70;
      }

      // ─── 2. MIXED AGGRESSIVE OPTION ───
      let aggChoiceName = '';
      let aggOdds = 0;
      let aggProb = 0;

      const score = conclusions.most_likely_score || '';
      const halfFull = conclusions.half_full || '';
      
      const mixType = index % 4; // 0: 半全场, 1: 总进球数, 2: 胜平负/让球博冷, 3: 比分/其他

      if (mixType === 0 && halfFull && halfFull !== '--') {
        aggChoiceName = `半全场 ${halfFull}`;
        if (halfFull.includes('平/平')) { aggOdds = 4.80; aggProb = fair.draw * 0.70; }
        else if (halfFull.includes('平/胜') || halfFull.includes('平/负')) { aggOdds = 5.50; aggProb = 0.18; }
        else if (halfFull.includes('胜/负') || halfFull.includes('负/胜')) { aggOdds = 25.0; aggProb = 0.03; }
        else { aggOdds = 3.50; aggProb = 0.25; }
      } 
      else if (mixType === 1) {
        // 总进球数区间 (1-2, 3-4, 5-6)
        let totalGoals = 2; // default
        if (score && score !== '--') {
          const s = score.split('或')[0].trim();
          const parts = s.split('-');
          if (parts.length === 2) totalGoals = parseInt(parts[0]) + parseInt(parts[1]);
        }
        if (totalGoals <= 2) {
          aggChoiceName = '总进球数 1-2球';
          aggOdds = 2.10;
          aggProb = 0.45;
        } else if (totalGoals <= 4) {
          aggChoiceName = '总进球数 3-4球';
          aggOdds = 2.60;
          aggProb = 0.35;
        } else {
          aggChoiceName = '总进球数 5-6球';
          aggOdds = 7.50;
          aggProb = 0.10;
        }
      }
      else if (mixType === 2) {
        // 胜平负/让球博冷 (Pick the highest odds among 1x2 that is reasonable)
        if (fair.draw > 0.25 && oddsObj.draw > 3.0) {
          aggChoiceName = '胜平负 平局';
          aggOdds = oddsObj.draw;
          aggProb = fair.draw;
        } else if (fair.away > 0.20 && oddsObj.away > 3.5) {
          aggChoiceName = `胜平负 ${m.away}胜`;
          aggOdds = oddsObj.away;
          aggProb = fair.away;
        } else if (fair.home > 0.20 && oddsObj.home > 3.5) {
          aggChoiceName = `胜平负 ${m.home}胜`;
          aggOdds = oddsObj.home;
          aggProb = fair.home;
        } else if (m.odds_analysis.lottery_handicap && m.odds_analysis.lottery_handicap.current) {
          const lh = m.odds_analysis.lottery_handicap;
          const hcText = lh.handicap || '';
          aggChoiceName = `让球胜平负 平局 (${hcText})`;
          aggOdds = lh.current.draw || 3.40;
          aggProb = 0.28;
        } else {
          aggChoiceName = `胜平负 平局`;
          aggOdds = oddsObj.draw;
          aggProb = fair.draw;
        }
      }
      else {
        // mixType === 3: 比分 (Correct Score)
        if (score && score !== '--') {
          const cleanScore = score.split('或')[0].trim();
          aggChoiceName = `比分 ${cleanScore}`;
          if (cleanScore === '0-0') { aggOdds = 7.50; aggProb = fair.draw * 0.45; }
          else if (cleanScore === '1-1') { aggOdds = 6.00; aggProb = fair.draw * 0.55; }
          else if (cleanScore === '1-0' || cleanScore === '2-1') { aggOdds = 6.80; aggProb = fair.home * 0.38; }
          else if (cleanScore === '0-1' || cleanScore === '1-2') { aggOdds = 7.80; aggProb = fair.away * 0.38; }
          else { aggOdds = 8.50; aggProb = 0.12; }
        } else {
          aggChoiceName = `胜平负 平局`;
          aggOdds = oddsObj.draw;
          aggProb = fair.draw;
        }
      }

      return {
        id: m.id,
        home: m.home,
        away: m.away,
        value: {
          name: valChoiceName,
          odds: valOdds,
          prob: valProb,
          ev: (valOdds * valProb) - 1
        },
        aggressive: {
          name: aggChoiceName,
          odds: aggOdds,
          prob: aggProb,
          ev: (aggOdds * aggProb) - 1
        }
      };
    });

    const makeParlay = (size, type) => {
      if (parsedBets.length < size) return null;

      // Sort bets based on EV for this specific type to get the optimal combination
      const sortedBets = [...parsedBets].sort((a, b) => b[type].ev - a[type].ev);
      const selected = sortedBets.slice(0, size);

      // Multiply odds and win probability
      const totalOdds = selected.reduce((acc, b) => acc * b[type].odds, 1);
      const totalProb = selected.reduce((acc, b) => acc * b[type].prob, 1);
      const totalEv = (totalProb * totalOdds) - 1;

      // Styling parameters
      let tagClass = type === 'value' ? 'value-high' : 'value-aggressive';
      let tagText = type === 'value' ? '📈 价值优选' : '🔥 混合博取 (高倍)';
      let cardClass = type === 'value' ? '' : 'aggressive';
      let titleText = type === 'value' ? `${size}串1 组合` : `${size}串1 混合串关`;

      let riskText = '低风险';
      if (size >= 8) riskText = type === 'value' ? '高风险' : '极高风险';
      else if (size >= 6) riskText = type === 'value' ? '中高风险' : '高风险';
      else if (size >= 4) riskText = type === 'value' ? '中风险' : '中高风险';
      else if (size >= 3) riskText = type === 'value' ? '中低风险' : '中风险';

      const matchesListHTML = selected.map(b => `
        <div class="parlay-match-item">
          <span class="parlay-match-teams"><span class="match-no-badge-sm">${formatMatchNo(b.id)}</span>${b.home} vs ${b.away}</span>
          <span class="parlay-match-odds" style="color: ${type === 'value' ? 'var(--cyan)' : 'var(--rose)'}">${b[type].name} @ ${b[type].odds.toFixed(2)}</span>
        </div>
      `).join('');

      return `
        <div class="parlay-card ${cardClass} animate-in">
          <div>
            <span class="parlay-tag ${tagClass}">${tagText}</span>
            <span class="parlay-risk">${riskText}</span>
          </div>
          <div class="parlay-title">${titleText}</div>
          <div class="parlay-ev">组合期望收益 (EV): <span style="color:${totalEv >= 0 ? 'var(--green)' : 'var(--red)'};font-weight:700">${(totalEv * 100).toFixed(1)}%</span></div>
          <div class="parlay-matches-list">
            ${matchesListHTML}
          </div>
          <div class="parlay-summary">
            <span>组合总赔率</span>
            <span class="parlay-summary-val">${totalOdds.toFixed(2)} 倍</span>
          </div>
          <div class="parlay-summary" style="margin-top:8px; border-top:none; padding-top:0;">
            <span>数学期望概率</span>
            <span class="parlay-summary-val">${(totalProb * 100).toFixed(2)}%</span>
          </div>
        </div>
      `;
    };

    const sizes = [2, 3, 4, 6, 8];
    const parlaysHTML = [];
    sizes.forEach(s => {
      const valP = makeParlay(s, 'value');
      const aggP = makeParlay(s, 'aggressive');
      if (valP) parlaysHTML.push(valP);
      if (aggP) parlaysHTML.push(aggP);
    });

    return parlaysHTML.join('') || `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);border:1px dashed var(--border);border-radius:var(--radius)">无足够数量的待预测赛事可组成串关</div>`;
  }

  // ─── PARLAY HISTORY RENDERER ───
  function renderParlayHistory(historyData) {
    const records = historyData?.parlay_records || [];
    if (records.length === 0) {
      return `
        <div style="grid-column:1/-1;text-align:center;padding:48px;color:var(--text-4);border:1px dashed var(--border);border-radius:var(--radius-lg)">
          <div style="font-size:32px;margin-bottom:12px">📅</div>
          <div style="font-family:var(--font-display);font-size:15px;color:var(--text-3)">暂无历史串关记录</div>
          <div style="font-size:12px;margin-top:4px">下一次执行「更新赛果并进化模型」指令时，系统将自动开始记录并进行红黑核对。</div>
        </div>
      `;
    }

    // Sort records by date descending
    const sortedRecords = [...records].sort((a, b) => new Date(b.date) - new Date(a.date));

    return sortedRecords.map((day, idx) => {
      const total = day.parlays.length;
      const won = day.parlays.filter(p => p.is_correct === true).length;
      
      const parlaysHTML = day.parlays.map(p => {
        const statusBadge = p.is_correct === true 
          ? '<span class="parlay-status-badge won">🎉 通关</span>' 
          : p.is_correct === false 
            ? '<span class="parlay-status-badge lost">☠ 未通过</span>' 
            : '<span class="parlay-status-badge pending">⏳ 待定</span>';

        const selectionsHTML = p.selections.map(s => {
          let mark = '';
          if (s.is_correct === true) {
            mark = '<span style="color:var(--green);margin-left:6px;font-weight:bold">✓</span>';
          } else if (s.is_correct === false) {
            mark = '<span style="color:var(--red);margin-left:6px;font-weight:bold">✗</span>';
          }
          return `
            <div class="ph-selection-row">
              <span class="ph-teams">${s.teams}</span>
              <span class="ph-bet">${s.selection} @ ${s.odds.toFixed(2)}${mark}</span>
            </div>
          `;
        }).join('');

        const evText = p.ev !== undefined ? `<div class="ph-meta-item">期望值: ${(p.ev * 100).toFixed(1)}%</div>` : '';

        return `
          <div class="ph-parlay-card ${p.type === 'value' ? '' : 'aggressive'}">
            <div class="ph-card-header">
              <span class="ph-card-tag">${p.type === 'value' ? '📈 价值优选' : '🔥 混合博取'}</span>
              <span class="ph-card-title">${p.size}串1</span>
              ${statusBadge}
            </div>
            <div class="ph-selections-list">
              ${selectionsHTML}
            </div>
            <div class="ph-card-footer">
              <div class="ph-meta-item">总赔率: ${p.total_odds.toFixed(2)}倍</div>
              ${evText}
            </div>
          </div>
        `;
      }).join('');

      const containerId = `ph-day-content-${idx}`;

      return `
        <div class="ph-day-card">
          <div class="ph-day-header" onclick="document.getElementById('${containerId}').classList.toggle('collapsed')">
            <div class="ph-day-date">📅 ${day.date}</div>
            <div class="ph-day-stats">
              <span>今日推荐：${total}组</span>
              <span>·</span>
              <span style="color:var(--green)">红单：${won}组</span>
              <span>·</span>
              <span>通关率：${total > 0 ? ((won / total) * 100).toFixed(0) : 0}%</span>
            </div>
            <div class="ph-collapse-arrow">▼</div>
          </div>
          <div class="ph-day-content collapsed" id="${containerId}">
            <div class="ph-parlays-grid">
              ${parlaysHTML}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  return {
    renderUltimateCard,
    renderMatchCard,
    renderModelStatus,
    renderEvolutionSection,
    renderHistoryRecords,
    renderParlays,
    renderParlayHistory,
    formatDate,
    formatTime
  };
})();
