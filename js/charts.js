/* ============================================================
   MATCH IQ — Charts Module (Chart.js wrappers)
   All charts use the dark futuristic design system
   ============================================================ */

const MatchIQCharts = (() => {

  // ─── SHARED CHART DEFAULTS ───
  const DEFAULTS = {
    color: {
      cyan:    '#00d4ff',
      indigo:  '#6366f1',
      purple:  '#8b5cf6',
      green:   '#10b981',
      amber:   '#f59e0b',
      red:     '#ef4444',
      text2:   '#cbd5e1',
      text3:   '#64748b',
      border:  'rgba(0,212,255,0.12)',
      gridLine:'rgba(255,255,255,0.04)',
    },
    font: { family: "'JetBrains Mono', monospace", size: 11 }
  };

  Chart.defaults.color = DEFAULTS.color.text3;
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 11;

  // ─── TEAM RADAR CHART ───
  function initTeamRadar(canvasId, homeData, awayData, homeName, awayName) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');

    const labels = ['进攻效率','防守稳定','射门转化','xG能力','压迫强度','定位球','中场控制','近期状态'];

    // Destroy existing chart if any
    if (canvas._chart) { canvas._chart.destroy(); }

    const chart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels,
        datasets: [
          {
            label: homeName,
            data: homeData,
            borderColor: DEFAULTS.color.cyan,
            backgroundColor: 'rgba(0,212,255,0.12)',
            borderWidth: 2,
            pointBackgroundColor: DEFAULTS.color.cyan,
            pointRadius: 3,
            pointHoverRadius: 5,
          },
          {
            label: awayName,
            data: awayData,
            borderColor: DEFAULTS.color.purple,
            backgroundColor: 'rgba(139,92,246,0.12)',
            borderWidth: 2,
            pointBackgroundColor: DEFAULTS.color.purple,
            pointRadius: 3,
            pointHoverRadius: 5,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: DEFAULTS.color.text2,
              padding: 12,
              boxWidth: 10,
              font: { size: 11 }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(13,21,39,0.95)',
            borderColor: 'rgba(0,212,255,0.3)',
            borderWidth: 1,
            titleColor: DEFAULTS.color.cyan,
            bodyColor: DEFAULTS.color.text2,
            padding: 10,
          }
        },
        scales: {
          r: {
            min: 0, max: 10,
            ticks: {
              display: false,
              stepSize: 2,
            },
            grid: { color: 'rgba(255,255,255,0.06)' },
            angleLines: { color: 'rgba(255,255,255,0.06)' },
            pointLabels: {
              color: DEFAULTS.color.text3,
              font: { size: 10 }
            }
          }
        }
      }
    });
    canvas._chart = chart;
    return chart;
  }

  // ─── MODEL EVOLUTION LINE CHART ───
  function initEvolutionChart(canvasId, evolutionData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (canvas._chart) canvas._chart.destroy();

    // Build labels and datasets from snapshots
    const snapshots = evolutionData.snapshots || [];
    const labels = snapshots.map(s => s.version);

    // Top 5 most important factors to track
    const trackedFactors = [
      { id: '01', name: '整体实力',  color: DEFAULTS.color.cyan },
      { id: '03', name: '核心球员',  color: DEFAULTS.color.green },
      { id: '09', name: '近期状态',  color: DEFAULTS.color.amber },
      { id: '05', name: '中场控制',  color: DEFAULTS.color.purple },
      { id: '35', name: '主场氛围',  color: DEFAULTS.color.red },
    ];

    const datasets = trackedFactors.map(f => ({
      label: f.name,
      data: snapshots.map(s => +(s.weights_snapshot[f.id] * 100).toFixed(2)),
      borderColor: f.color,
      backgroundColor: 'transparent',
      borderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5,
      tension: 0.4,
    }));

    // Add placeholder point if only 1 snapshot
    if (labels.length < 2) {
      labels.push('(待进化)');
      datasets.forEach(ds => ds.data.push(null));
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'right',
            labels: { color: DEFAULTS.color.text2, padding: 10, boxWidth: 10, font: { size: 10 } }
          },
          tooltip: {
            backgroundColor: 'rgba(13,21,39,0.95)',
            borderColor: 'rgba(0,212,255,0.3)',
            borderWidth: 1,
            titleColor: DEFAULTS.color.cyan,
            bodyColor: DEFAULTS.color.text2,
            callbacks: {
              label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y}%`
            }
          }
        },
        scales: {
          x: {
            grid: { color: DEFAULTS.color.gridLine },
            ticks: { color: DEFAULTS.color.text3 }
          },
          y: {
            grid: { color: DEFAULTS.color.gridLine },
            ticks: {
              color: DEFAULTS.color.text3,
              callback: v => v + '%'
            }
          }
        }
      }
    });
    canvas._chart = chart;
    return chart;
  }

  // ─── ACCURACY TREND CHART ───
  function initAccuracyChart(canvasId, historyData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (canvas._chart) canvas._chart.destroy();

    const records = (historyData.records || []).filter(r => r.result !== null);
    const labels = records.map((r, i) => `#${i + 1}`);
    const accuracyData = records.map((_, i) => {
      const slice = records.slice(0, i + 1);
      const correct = slice.filter(r => r.correct).length;
      return +((correct / slice.length) * 100).toFixed(1);
    });

    if (labels.length === 0) {
      labels.push('等待首场验证');
      accuracyData.push(null);
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: '累计准确率',
          data: accuracyData,
          borderColor: DEFAULTS.color.green,
          backgroundColor: 'rgba(16,185,129,0.1)',
          fill: true,
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(13,21,39,0.95)',
            borderColor: 'rgba(16,185,129,0.3)',
            borderWidth: 1,
            titleColor: DEFAULTS.color.green,
            bodyColor: DEFAULTS.color.text2,
            callbacks: { label: ctx => `准确率: ${ctx.parsed.y}%` }
          }
        },
        scales: {
          x: { grid: { color: DEFAULTS.color.gridLine }, ticks: { color: DEFAULTS.color.text3 } },
          y: {
            min: 0, max: 100,
            grid: { color: DEFAULTS.color.gridLine },
            ticks: { color: DEFAULTS.color.text3, callback: v => v + '%' }
          }
        }
      }
    });
    canvas._chart = chart;
    return chart;
  }

  // ─── FACTOR CONTRIBUTION BAR CHART ───
  function initFactorChart(canvasId, factorScores, weightsData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (canvas._chart) canvas._chart.destroy();

    const factors = weightsData.factors.slice(0, 12);
    const labels = factors.map(f => f.name.slice(0, 8));
    const weights = factors.map(f => +(f.weight * 100).toFixed(2));

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: '权重 %',
          data: weights,
          backgroundColor: factors.map((_, i) =>
            `hsla(${190 + i * 8}, 80%, 60%, 0.7)`
          ),
          borderColor: factors.map((_, i) =>
            `hsla(${190 + i * 8}, 80%, 60%, 1)`
          ),
          borderWidth: 1,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(13,21,39,0.95)',
            borderColor: DEFAULTS.color.border,
            borderWidth: 1,
            callbacks: {
              label: ctx => `权重: ${ctx.parsed.x}%`
            }
          }
        },
        scales: {
          x: {
            grid: { color: DEFAULTS.color.gridLine },
            ticks: { color: DEFAULTS.color.text3, callback: v => v + '%' }
          },
          y: {
            grid: { display: false },
            ticks: { color: DEFAULTS.color.text2, font: { size: 10 } }
          }
        }
      }
    });
    canvas._chart = chart;
    return chart;
  }

  // ─── ODDS MOVEMENT CHART ───
  function initOddsMovementChart(canvasId, oddsData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (canvas._chart) canvas._chart.destroy();

    const companies = ['company_1', 'company_2', 'company_3'];
    const labels = companies.map(c => oddsData[c] ? oddsData[c].name : c);

    const homeInitial = companies.map(c => oddsData[c]?.initial?.home || 0);
    const homeCurrent = companies.map(c => oddsData[c]?.current?.home || 0);
    const drawInitial = companies.map(c => oddsData[c]?.initial?.draw || 0);
    const drawCurrent = companies.map(c => oddsData[c]?.current?.draw || 0);
    const awayInitial = companies.map(c => oddsData[c]?.initial?.away || 0);
    const awayCurrent = companies.map(c => oddsData[c]?.current?.away || 0);

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: '主初', data: homeInitial, backgroundColor: 'rgba(0,212,255,0.3)', borderColor: DEFAULTS.color.cyan, borderWidth: 1, borderRadius: 3 },
          { label: '主即', data: homeCurrent, backgroundColor: 'rgba(0,212,255,0.7)', borderColor: DEFAULTS.color.cyan, borderWidth: 1, borderRadius: 3 },
          { label: '平初', data: drawInitial, backgroundColor: 'rgba(245,158,11,0.3)', borderColor: DEFAULTS.color.amber, borderWidth: 1, borderRadius: 3 },
          { label: '平即', data: drawCurrent, backgroundColor: 'rgba(245,158,11,0.7)', borderColor: DEFAULTS.color.amber, borderWidth: 1, borderRadius: 3 },
          { label: '客初', data: awayInitial, backgroundColor: 'rgba(139,92,246,0.3)', borderColor: DEFAULTS.color.purple, borderWidth: 1, borderRadius: 3 },
          { label: '客即', data: awayCurrent, backgroundColor: 'rgba(139,92,246,0.7)', borderColor: DEFAULTS.color.purple, borderWidth: 1, borderRadius: 3 },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: DEFAULTS.color.text2, padding: 8, boxWidth: 10, font: { size: 10 } } },
          tooltip: {
            backgroundColor: 'rgba(13,21,39,0.95)',
            borderColor: DEFAULTS.color.border,
            borderWidth: 1,
            bodyColor: DEFAULTS.color.text2,
          }
        },
        scales: {
          x: { grid: { color: DEFAULTS.color.gridLine }, ticks: { color: DEFAULTS.color.text2 } },
          y: {
            grid: { color: DEFAULTS.color.gridLine },
            ticks: { color: DEFAULTS.color.text3 },
            suggestedMin: 1.5,
          }
        }
      }
    });
    canvas._chart = chart;
    return chart;
  }

  return { initTeamRadar, initEvolutionChart, initAccuracyChart, initFactorChart, initOddsMovementChart };
})();
