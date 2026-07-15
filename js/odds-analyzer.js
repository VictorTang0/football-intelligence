/* ============================================================
   MATCH IQ — Odds Analyzer Module
   Detects smoke screens, infers bookmaker intent, calculates EV
   ============================================================ */

const OddsAnalyzer = (() => {

  // ─── CALCULATE IMPLIED PROBABILITY FROM ODDS ───
  function impliedProb(odds) {
    return odds > 0 ? 1 / odds : 0;
  }

  // ─── REMOVE BOOKMAKER MARGIN (OVERROUND) ───
  function removemargin(home, draw, away) {
    const total = impliedProb(home) + impliedProb(draw) + impliedProb(away);
    return {
      home: +(impliedProb(home) / total * 100).toFixed(1),
      draw: +(impliedProb(draw) / total * 100).toFixed(1),
      away: +(impliedProb(away) / total * 100).toFixed(1),
      margin: +((total - 1) * 100).toFixed(2)
    };
  }

  // ─── DETECT ODDS MOVEMENT DIRECTION ───
  function detectMovement(initial, current) {
    const homeChange = current.home - initial.home;
    const drawChange = current.draw - initial.draw;
    const awayChange = current.away - initial.away;

    const signals = [];
    const threshold = 0.05;

    if (homeChange < -threshold) signals.push({ dir: 'home_down', strength: Math.abs(homeChange), msg: '主队赔率被压低（资金流入主队方向）' });
    if (homeChange >  threshold) signals.push({ dir: 'home_up',   strength: homeChange,           msg: '主队赔率上升（市场规避主队风险）' });
    if (drawChange < -threshold) signals.push({ dir: 'draw_down', strength: Math.abs(drawChange), msg: '平局赔率被压低（资金流入平局方向）' });
    if (drawChange >  threshold) signals.push({ dir: 'draw_up',   strength: drawChange,           msg: '平局赔率上升（庄家保护平局方向）' });
    if (awayChange < -threshold) signals.push({ dir: 'away_down', strength: Math.abs(awayChange), msg: '客队赔率被压低（资金流入客队方向）' });
    if (awayChange >  threshold) signals.push({ dir: 'away_up',   strength: awayChange,           msg: '客队赔率上升（庄家保护客队方向）' });

    return { homeChange, drawChange, awayChange, signals };
  }

  // ─── CROSS-VALIDATE MULTIPLE COMPANIES ───
  function crossValidateCompanies(oddsData) {
    const companies = ['company_1', 'company_2', 'company_3'].filter(c => oddsData[c]);
    if (companies.length === 0) return { consensus: null, divergence: [] };

    const movements = companies.map(c => detectMovement(oddsData[c].initial, oddsData[c].current));
    const homeChanges = movements.map(m => m.homeChange);
    const drawChanges = movements.map(m => m.drawChange);
    const awayChanges = movements.map(m => m.awayChange);

    // Check if all companies move in the same direction
    const homeConsensus = homeChanges.every(c => c < -0.03) ? 'down' : homeChanges.every(c => c > 0.03) ? 'up' : 'mixed';
    const drawConsensus = drawChanges.every(c => c < -0.03) ? 'down' : drawChanges.every(c => c > 0.03) ? 'up' : 'mixed';
    const awayConsensus = awayChanges.every(c => c < -0.03) ? 'down' : awayChanges.every(c => c > 0.03) ? 'up' : 'mixed';

    const divergence = [];
    if (homeConsensus === 'mixed') divergence.push('主队赔率各家分歧，信号不明确');
    if (drawConsensus === 'mixed') divergence.push('平局赔率各家分歧，可能存在信息差');
    if (awayConsensus === 'mixed') divergence.push('客队赔率各家分歧，需结合亚盘判断');

    return { homeConsensus, drawConsensus, awayConsensus, divergence };
  }

  // ─── INFER BOOKMAKER INTENT FROM PATTERNS ───
  function inferBookmakerIntent(oddsData) {
    const companies = ['company_1', 'company_2', 'company_3'].filter(c => oddsData[c]);
    if (companies.length === 0) return { intent: '数据不足', confidence: 'low' };

    // Aggregate movement
    let homeDown = 0, drawUp = 0, awayUp = 0, homeUp = 0;
    companies.forEach(c => {
      const m = detectMovement(oddsData[c].initial, oddsData[c].current);
      if (m.homeChange < -0.05) homeDown++;
      if (m.drawChange > 0.05)  drawUp++;
      if (m.awayChange > 0.05)  awayUp++;
      if (m.homeChange > 0.05)  homeUp++;
    });

    const totalCo = companies.length;
    const intents = [];

    // Classic trap pattern: all companies lower home odds → attract public → bookmaker protects draw/away
    if (homeDown === totalCo && (drawUp >= 1 || awayUp >= 1)) {
      intents.push({
        type: 'TRAP',
        description: '典型诱导陷阱：主队赔率集体下降引导散户押主，同时平局/客队赔率上升，庄家真实保护方向为平局或客胜',
        bookmaker_protects: drawUp > awayUp ? 'draw' : 'away',
        confidence: 'high'
      });
    }

    // Asian handicap confirmation
    const ah = oddsData.asian_handicap;
    if (ah) {
      const ahHomeChange = (ah.current?.home_odds || 0) - (ah.initial?.home_odds || 0);
      const ahAwayChange = (ah.current?.away_odds || 0) - (ah.initial?.away_odds || 0);

      if (Math.abs(ahHomeChange) < 0.05 && Math.abs(ahAwayChange) < 0.05) {
        intents.push({
          type: 'AH_STABLE',
          description: '亚盘稳定未动，主客实力被认定接近，欧赔变动可能是引导操作',
          confidence: 'medium'
        });
      } else if (ahAwayChange > 0.05) {
        intents.push({
          type: 'AH_PROTECT_AWAY',
          description: '亚盘客队赔率上升，庄家在保护让球客队方向，主队让球风险较高',
          confidence: 'high'
        });
      }
    }

    // O/U analysis
    const ou = oddsData.over_under;
    if (ou) {
      const overChange = (ou.current?.over || 0) - (ou.initial?.over || 0);
      if (overChange < -0.05) {
        intents.push({
          type: 'OVER_COMPRESSED',
          description: '大球赔率被压缩，资金明显流向大球方向，大球概率高于初盘隐含值',
          confidence: 'medium'
        });
      }
    }

    return intents.length > 0 ? intents : [{
      type: 'NEUTRAL',
      description: '盘口走势平稳，无明显庄家意图信号，建议参考数据面分析',
      confidence: 'low'
    }];
  }

  // ─── CALCULATE EXPECTED VALUE ───
  function calcEV(trueProb, odds) {
    // EV = (trueProbability × (odds - 1)) - (1 - trueProbability)
    const ev = trueProb * (odds - 1) - (1 - trueProb);
    return +ev.toFixed(3);
  }

  // ─── BUILD RETAIL SENTIMENT TRAP ANALYSIS ───
  function analyzeRetailTrap(match) {
    const sentiment = match.odds_analysis?.retail_sentiment;
    const pvb = match.public_vs_bookmaker || [];
    const traps = [];

    if (!sentiment) return traps;

    pvb.forEach(item => {
      const publicPct  = parseFloat(item.public_prob)  / 100;
      const truePct    = parseFloat(item.true_est)      / 100;
      const bookImplied= parseFloat(item.bookmaker_implied) / 100;
      const diff = publicPct - truePct;

      if (diff > 0.15) {
        traps.push({
          outcome: item.outcome,
          severity: diff > 0.25 ? 'HIGH' : 'MEDIUM',
          message: `散户${Math.round(publicPct*100)}%押注${item.outcome}，但真实概率估计仅${Math.round(truePct*100)}%，超配${Math.round(diff*100)}%，赔付风险${item.payout_risk}`
        });
      }
    });

    return traps;
  }

  return {
    impliedProb,
    removemargin,
    detectMovement,
    crossValidateCompanies,
    inferBookmakerIntent,
    calcEV,
    analyzeRetailTrap
  };
})();
