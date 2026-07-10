/**
 * Chart Adapter — single charting engine for the platform (Apache ECharts).
 *
 * The ONE translation point between the platform's `chart_config` JSON (emitted by
 * `components/visual-chart-builder.js`) + widget/report data and a concrete chart.
 * Both the dashboard portlets (`components/dashboard-widget.js`) and the report
 * viewer (`components/report-viewer.js`) render through `renderChart()`.
 *
 * ECharts is self-hosted (`/assets/vendor/echarts.esm.min.js`) and lazy-imported on
 * first use, so pages without charts pay nothing. Its JSON `option` model maps
 * directly onto our JSON-driven layout requirement.
 *
 * Input contract:
 *   chartConfig = { chart_type, x_axis, y_axis: [..] | field, y_axis_secondary?, title?, colors?, stacked? }
 *   data        = { labels: [..], datasets: [{ label, data: [..] }, ..] }   // dashboard chart widgets
 *              OR [ {col: val, ..}, .. ]                                     // raw report rows
 */

let _echartsPromise = null;

/** Lazy-load the self-hosted ECharts ESM build once. */
export function loadECharts() {
    if (!_echartsPromise) {
        _echartsPromise = import('/assets/vendor/echarts.esm.min.js');
    }
    return _echartsPromise;
}

// Brand-neutral categorical palette (aligns with the platform's blue-forward Tailwind theme).
const PALETTE = [
    '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
];

/** Chart types the adapter renders natively today. Exotic types (see below) are deferred. */
export const SUPPORTED_CHART_TYPES = [
    'bar', 'bar_horizontal', 'bar_stacked', 'bar_grouped', 'column',
    'line', 'area', 'area_stacked',
    'pie', 'donut',
    'combo', 'scatter', 'funnel', 'gauge', 'waterfall',
];

// Available in ECharts but not yet wired into the builder UI — tracked as backlog, not built.
export const DEFERRED_CHART_TYPES = ['heatmap', 'treemap', 'sankey', 'map', 'candlestick', 'radar'];

function isDarkMode() {
    return document.documentElement.classList.contains('dark') ||
        document.documentElement.getAttribute('data-theme') === 'dark' ||
        (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
}

/** Normalise either supported input shape to { labels, datasets:[{label,data}] }. */
export function normalizeChartData(data, chartConfig = {}) {
    if (data && Array.isArray(data.datasets)) {
        return { labels: data.labels || [], datasets: data.datasets };
    }
    if (Array.isArray(data)) {
        const x = chartConfig.x_axis;
        const ys = Array.isArray(chartConfig.y_axis)
            ? chartConfig.y_axis
            : (chartConfig.y_axis ? [chartConfig.y_axis] : []);
        return {
            labels: x ? data.map((r) => r[x]) : data.map((_, i) => i + 1),
            datasets: ys.map((y) => ({ label: y, data: data.map((r) => r[y]) })),
        };
    }
    return { labels: [], datasets: [] };
}

function baseTheme(dark) {
    const axisColor = dark ? '#9ca3af' : '#6b7280';
    const splitColor = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
    const textColor = dark ? '#e5e7eb' : '#374151';
    return { axisColor, splitColor, textColor };
}

/** Build an ECharts `option` from chart_config + normalized data. */
export function buildOption(chartConfig = {}, nd = { labels: [], datasets: [] }, { dark = false } = {}) {
    const type = (chartConfig.chart_type || chartConfig.type || 'bar').toLowerCase();
    const { axisColor, splitColor, textColor } = baseTheme(dark);
    const colors = Array.isArray(chartConfig.colors) && chartConfig.colors.length ? chartConfig.colors : PALETTE;

    const common = {
        color: colors,
        backgroundColor: 'transparent',
        textStyle: { color: textColor, fontFamily: 'inherit' },
        title: chartConfig.title ? { text: chartConfig.title, left: 'center', textStyle: { color: textColor, fontSize: 13 } } : undefined,
        tooltip: { trigger: 'item', confine: true },
        legend: nd.datasets.length > 1 ? { bottom: 0, textStyle: { color: textColor } } : undefined,
        grid: { left: 48, right: 24, top: chartConfig.title ? 40 : 16, bottom: nd.datasets.length > 1 ? 40 : 28, containLabel: true },
    };

    const catAxis = { type: 'category', data: nd.labels, axisLine: { lineStyle: { color: axisColor } }, axisLabel: { color: axisColor } };
    const valAxis = { type: 'value', axisLine: { lineStyle: { color: axisColor } }, axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: splitColor } } };

    // --- Composition: pie / donut ---
    if (type === 'pie' || type === 'donut') {
        const ds = nd.datasets[0] || { data: [] };
        return {
            ...common,
            tooltip: { trigger: 'item', confine: true, formatter: '{b}: {c} ({d}%)' },
            legend: { bottom: 0, textStyle: { color: textColor } },
            series: [{
                type: 'pie',
                radius: type === 'donut' ? ['45%', '70%'] : '65%',
                data: nd.labels.map((name, i) => ({ name, value: ds.data[i] })),
                label: { color: textColor },
            }],
        };
    }

    // --- Funnel ---
    if (type === 'funnel') {
        const ds = nd.datasets[0] || { data: [] };
        return {
            ...common,
            tooltip: { trigger: 'item', confine: true, formatter: '{b}: {c}' },
            series: [{ type: 'funnel', data: nd.labels.map((name, i) => ({ name, value: ds.data[i] })), label: { color: textColor } }],
        };
    }

    // --- Gauge (first value of first dataset) ---
    if (type === 'gauge') {
        const ds = nd.datasets[0] || { data: [] };
        const value = ds.data[0] ?? 0;
        return {
            ...common,
            tooltip: { show: false },
            series: [{ type: 'gauge', progress: { show: true }, data: [{ value, name: ds.label || '' }], detail: { color: textColor } }],
        };
    }

    // --- Scatter ---
    if (type === 'scatter') {
        return {
            ...common,
            tooltip: { trigger: 'item', confine: true },
            xAxis: catAxis,
            yAxis: valAxis,
            series: nd.datasets.map((d) => ({ name: d.label, type: 'scatter', data: d.data })),
        };
    }

    // --- Waterfall (stacked-bar trick: transparent base + delta) ---
    if (type === 'waterfall') {
        const ds = nd.datasets[0] || { data: [] };
        const base = [];
        const inc = [];
        let running = 0;
        for (const v of ds.data) {
            const n = Number(v) || 0;
            base.push(n >= 0 ? running : running + n);
            inc.push(Math.abs(n));
            running += n;
        }
        return {
            ...common,
            tooltip: { trigger: 'axis', confine: true },
            xAxis: catAxis,
            yAxis: valAxis,
            series: [
                { type: 'bar', stack: 'wf', itemStyle: { color: 'transparent' }, emphasis: { itemStyle: { color: 'transparent' } }, data: base, silent: true },
                { type: 'bar', stack: 'wf', data: inc },
            ],
        };
    }

    // --- Cartesian family: bar / column / line / area / combo (+ variants) ---
    const horizontal = type === 'bar_horizontal';
    const stacked = type === 'bar_stacked' || type === 'area_stacked' || chartConfig.stacked === true;
    const isArea = type === 'area' || type === 'area_stacked';
    const isCombo = type === 'combo';
    const baseType = (type.startsWith('bar') || type === 'column' || type === 'waterfall') ? 'bar' : 'line';

    // A secondary axis only exists for a combo chart that explicitly configures one.
    const hasSecondary = isCombo && !!chartConfig.y_axis_secondary;

    const series = nd.datasets.map((d, i) => {
        // Combo: last series becomes a line (on the secondary axis when one is configured).
        const asLine = isCombo && i === nd.datasets.length - 1 && nd.datasets.length > 1;
        const s = {
            name: d.label,
            type: asLine ? 'line' : baseType,
            data: d.data,
            smooth: baseType === 'line' && !isArea ? false : baseType === 'line',
        };
        if (stacked && !asLine) s.stack = 'total';
        if (isArea && !asLine) s.areaStyle = {};
        if (asLine && hasSecondary) s.yAxisIndex = 1;
        return s;
    });

    const yAxes = hasSecondary
        ? [valAxis, { ...valAxis, name: chartConfig.y_axis_secondary }]
        : valAxis;

    return {
        ...common,
        tooltip: { trigger: 'axis', confine: true, axisPointer: { type: 'shadow' } },
        xAxis: horizontal ? valAxis : catAxis,
        yAxis: horizontal ? { ...catAxis } : yAxes,
        series,
    };
}

/**
 * Render (or update) a chart into `el`. Reuses the ECharts instance bound to the
 * element and keeps it responsive via a ResizeObserver. Returns the instance.
 */
export async function renderChart(el, chartConfig, data, opts = {}) {
    const echarts = await loadECharts();
    const dark = opts.dark ?? isDarkMode();
    let inst = echarts.getInstanceByDom(el);
    if (!inst) inst = echarts.init(el, null, { renderer: 'canvas' });

    const nd = normalizeChartData(data, chartConfig);
    inst.setOption(buildOption(chartConfig, nd, { dark }), true);

    if (!el.__chartResizeObserver && typeof ResizeObserver !== 'undefined') {
        const ro = new ResizeObserver(() => inst.resize());
        ro.observe(el);
        el.__chartResizeObserver = ro;
    }
    return inst;
}

/** Dispose the chart bound to `el` (call from a widget's destroy()). */
export async function disposeChart(el) {
    const echarts = await loadECharts();
    const inst = echarts.getInstanceByDom(el);
    if (inst) inst.dispose();
    if (el.__chartResizeObserver) { el.__chartResizeObserver.disconnect(); delete el.__chartResizeObserver; }
}
