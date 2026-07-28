/**
 * PES / eFootball Monte Carlo 1000-Match Simulation Engine v1.0
 * Uses Dixon-Coles Bivariate Poisson & Time-Step Event Chains.
 */
(function(window) {
  'use strict';

  const PesMonteCarloEngine = {
    /**
     * Factorial lookup for fast calculation
     */
    factorial(n) {
      if (n === 0 || n === 1) return 1;
      let res = 1;
      for (let i = 2; i <= n; i++) res *= i;
      return res;
    },

    /**
     * Standard Poisson probability P(X = k; lambda)
     */
    poisson(k, lambda) {
      return (Math.pow(lambda, k) * Math.exp(-lambda)) / this.factorial(k);
    },

    /**
     * Dixon-Coles tau adjustment for low scores (0-0, 1-0, 0-1, 1-1)
     */
    dixonColesTau(x, y, lambdaH, lambdaA, rho = -0.065) {
      if (x === 0 && y === 0) return 1 - (lambdaH * lambdaA * rho);
      if (x === 1 && y === 0) return 1 + (lambdaH * rho);
      if (x === 0 && y === 1) return 1 + (lambdaA * rho);
      if (x === 1 && y === 1) return 1 - rho;
      return 1.0;
    },

    /**
     * Random Poisson sample using Inverse Transform Sampling
     */
    samplePoisson(lambda) {
      const L = Math.exp(-lambda);
      let k = 0;
      let p = 1.0;
      do {
        k++;
        p *= Math.random();
      } while (p > L);
      return k - 1;
    },

    /**
     * Derive expected goals lambda for home and away teams
     */
    calculateLambda(match) {
      const odds = match?.odds_analysis?.pinnacle?.current || { home: 2.10, draw: 3.20, away: 3.10 };
      const hWinProb = 1 / (odds.home || 2.10);
      const aWinProb = 1 / (odds.away || 3.10);

      // Base strength derived from odds & home advantage
      let lambdaH = Math.max(0.6, Math.min(3.8, (hWinProb * 2.7) + 0.35));
      let lambdaA = Math.max(0.5, Math.min(3.5, (aWinProb * 2.4)));

      // Injury Deduction
      const inj = match?.injury_analysis || {};
      const homeInj = inj.home_absences || 0;
      const awayInj = inj.away_absences || 0;
      
      lambdaH *= Math.max(0.75, 1 - (homeInj * 0.06));
      lambdaA *= Math.max(0.75, 1 - (awayInj * 0.06));

      return { lambdaH, lambdaA };
    },

    /**
     * Simulate 1 single 90+ min match with time-step event chains
     */
    simulateSingleMatch(baseLambdaH, baseLambdaA) {
      // Dynamic variance factor (stamina / form / random variance on the day: 0.85 ~ 1.15)
      const formH = 0.85 + (Math.random() * 0.30);
      const formA = 0.85 + (Math.random() * 0.30);
      
      let lambdaH = baseLambdaH * formH;
      let lambdaA = baseLambdaA * formA;

      // 1. Red card event chain (2.5% chance per team)
      let redH = Math.random() < 0.025;
      let redA = Math.random() < 0.025;

      if (redH) { lambdaH *= 0.60; lambdaA *= 1.35; }
      if (redA) { lambdaA *= 0.60; lambdaH *= 1.35; }

      // 2. Penalty / Own goal surprise factor (10% chance)
      let penaltyH = Math.random() < 0.10 ? 1 : 0;
      let penaltyA = Math.random() < 0.10 ? 1 : 0;

      // Split game into 1st Half (0-45+ min) and 2nd Half (45-90+ min)
      const lambdaH1 = lambdaH * 0.42;
      const lambdaA1 = lambdaA * 0.42;

      let hGoals1 = this.samplePoisson(lambdaH1);
      let aGoals1 = this.samplePoisson(lambdaA1);

      // Apply Dixon-Coles tau adjustment check for 1st half
      const tau1 = this.dixonColesTau(hGoals1, aGoals1, lambdaH1, lambdaA1);
      if (Math.random() > tau1 && (hGoals1 + aGoals1 > 0)) {
        if (hGoals1 > 0) hGoals1--;
      }

      // Second half gets ~58% + late-game open-space boost (75-90+ min)
      let boostH = (hGoals1 < aGoals1) ? 1.30 : 1.0;
      let boostA = (aGoals1 < hGoals1) ? 1.30 : 1.0;

      const lambdaH2 = (lambdaH * 0.58 * boostH) + (penaltyH * 0.7);
      const lambdaA2 = (lambdaA * 0.58 * boostA) + (penaltyA * 0.7);

      let hGoals2 = this.samplePoisson(lambdaH2);
      let aGoals2 = this.samplePoisson(lambdaA2);

      const hTotal = hGoals1 + hGoals2;
      const aTotal = aGoals1 + aGoals2;

      const htRes = hGoals1 > aGoals1 ? '胜' : hGoals1 === aGoals1 ? '平' : '负';
      const ftRes = hTotal > aTotal ? '胜' : hTotal === aTotal ? '平' : '负';
      const halfFull = `${htRes}${ftRes}`;

      return {
        score1st: `${hGoals1}-${aGoals1}`,
        scoreFull: `${hTotal}-${aTotal}`,
        hTotal,
        aTotal,
        halfFull,
        htRes,
        ftRes,
        isWildOutlier: (hTotal + aTotal >= 5) || (hTotal === aTotal && hTotal >= 3) || (hTotal === 0 && aTotal >= 3) || (aTotal === 0 && hTotal >= 4)
      };
    },

    /**
     * Run 5000-match Monte Carlo simulation
     */
    runSimulation5000(match) {
      const { lambdaH, lambdaA } = this.calculateLambda(match);
      const iterations = 5000;

      let homeWins = 0, draws = 0, awayWins = 0;
      const scoreFreq = {};
      const halfFullFreq = {};
      const wildOutliersMap = {};

      for (let i = 0; i < iterations; i++) {
        const sim = this.simulateSingleMatch(lambdaH, lambdaA);
        
        if (sim.hTotal > sim.aTotal) homeWins++;
        else if (sim.hTotal === sim.aTotal) draws++;
        else awayWins++;

        scoreFreq[sim.scoreFull] = (scoreFreq[sim.scoreFull] || 0) + 1;
        halfFullFreq[sim.halfFull] = (halfFullFreq[sim.halfFull] || 0) + 1;

        if (sim.isWildOutlier) {
          wildOutliersMap[sim.scoreFull] = (wildOutliersMap[sim.scoreFull] || 0) + 1;
        }
      }

      const sortedScores = Object.entries(scoreFreq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([score, count]) => ({
          score,
          count,
          pct: ((count / iterations) * 100).toFixed(1) + '%'
        }));

      const sortedHalfFull = Object.entries(halfFullFreq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([hf, count]) => ({
          hf,
          count,
          pct: ((count / iterations) * 100).toFixed(1) + '%'
        }));

      const sortedWildOutliers = Object.entries(wildOutliersMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(([score, count]) => ({
          score,
          count,
          pct: ((count / iterations) * 100).toFixed(1) + '%'
        }));

      // Calculate Tactical Style Tag
      const homePctNum = parseFloat(((homeWins / iterations) * 100).toFixed(1));
      const drawPctNum = parseFloat(((draws / iterations) * 100).toFixed(1));
      const awayPctNum = parseFloat(((awayWins / iterations) * 100).toFixed(1));
      const margin = Math.abs(homePctNum - awayPctNum);

      let styleTag = {
        name: '⚖️ 战术胶着型',
        desc: '两队中场缠斗，进球受限，防守拉锯剧烈',
        color: '#38bdf8',
        bg: 'rgba(56,189,248,0.12)',
        border: 'rgba(56,189,248,0.3)'
      };

      if (homePctNum >= 65.0) {
        styleTag = {
          name: '🛡️ 强弱悬殊型',
          desc: '主队压制力极强，高概率触发零封或多球屠杀',
          color: '#a855f7',
          bg: 'rgba(168,85,247,0.15)',
          border: 'rgba(168,85,247,0.4)'
        };
      } else if (homePctNum >= 55.0) {
        styleTag = {
          name: '🔥 强攻突破型',
          desc: '主场优势显著，主队进攻欲望强劲，看好主胜突破',
          color: '#4ade80',
          bg: 'rgba(74,222,128,0.12)',
          border: 'rgba(74,222,128,0.35)'
        };
      } else if (margin <= 12.0) {
        styleTag = {
          name: '⚔️ 均势对喷型',
          desc: '两队实力极度接近，易诱发互相撕裂防线的大比分或平局',
          color: '#fbbf24',
          bg: 'rgba(251,191,36,0.15)',
          border: 'rgba(251,191,36,0.4)'
        };
      } else if (awayPctNum >= 45.0) {
        styleTag = {
          name: '💣 反客为主型',
          desc: '客队反击极其犀利，谨防客队客场爆冷下克上',
          color: '#f87171',
          bg: 'rgba(248,113,113,0.15)',
          border: 'rgba(248,113,113,0.4)'
        };
      }

      return {
        iterations,
        winRate: {
          homePct: homePctNum.toFixed(1),
          drawPct: drawPctNum.toFixed(1),
          awayPct: awayPctNum.toFixed(1)
        },
        styleTag,
        topScores: sortedScores,
        topHalfFull: sortedHalfFull,
        wildOutliers: sortedWildOutliers
      };
    },

    runSimulation1000(match) {
      return this.runSimulation5000(match);
    }
  };

  window.PesMonteCarloEngine = PesMonteCarloEngine;
})(typeof window !== 'undefined' ? window : this);
