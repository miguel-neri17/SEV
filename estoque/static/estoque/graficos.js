/* Gráficos do SEV desenhados em canvas puro, com animação de entrada.
Cada função de desenho recebe um progresso t (0 a 1) e é chamada
   várias vezes pelo loop de animação até chegar em 1. */
(function () {
    const DURACAO = 850;          // duração da animação, em milissegundos
    const COR_A = '#22A9DE';
    const COR_B = '#0E6E63';
    const CORES = ['#22A9DE', '#0E6E63', '#A85A08', '#5B6ABF', '#A72B21', '#5FA8C9'];

    // Respeita quem pediu menos animação no sistema operacional.
    const semAnimacao = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function getData() {
        const el = document.getElementById('dados-graficos');
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.error('Dados dos gráficos inválidos:', e);
            return null;
        }
    }

    function setup(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, rect.width);
        const height = Math.max(280, rect.height);
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        const ctx = canvas.getContext('2d');
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, width, height);
        return { ctx, width, height };
    }

    function text(ctx, value, x, y, size, align, alpha) {
        ctx.save();
        ctx.globalAlpha = alpha === undefined ? 1 : alpha;
        ctx.font = (size || 12) + "px 'IBM Plex Mono', Consolas, monospace";
        ctx.fillStyle = '#5A6B7A';
        ctx.textAlign = align || 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(value), x, y);
        ctx.restore();
    }

    function formatar(valor, prefixo) {
        const n = Number(valor || 0);
        if (!prefixo) return String(Math.round(n));
        return prefixo + n.toLocaleString('pt-BR', {
            minimumFractionDigits: 2, maximumFractionDigits: 2
        });
    }

    function semDados(ctx, width, height, mensagem) {
        ctx.font = "13px 'Inter', 'Segoe UI', sans-serif";
        ctx.fillStyle = '#5A6B7A';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(mensagem, width / 2, height / 2);
    }

    function vazio(valores) {
        return !valores.length || valores.every(v => !Number(v));
    }

    function niceMax(value) {
        if (value <= 0) return 1;
        const power = Math.pow(10, Math.floor(Math.log10(value)));
        const n = value / power;
        const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
        return step * power;
    }

    // Desacelera no fim: começa rápido e "assenta" no valor final.
    function suavizar(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    // Cada barra começa um pouco depois da anterior (efeito cascata).
    function progressoItem(t, indice, total) {
        if (total <= 1) return t;
        const atraso = 0.35;                       // fatia do tempo usada no escalonamento
        const passo = atraso / total;
        const local = (t - passo * indice) / (1 - atraso);
        return Math.max(0, Math.min(1, local));
    }

    // ------------------------------------------------- barras agrupadas

    function drawGroupedBars(id, labels, first, second, firstLabel, secondLabel, t) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);

        if (!labels.length || (vazio(first) && vazio(second))) {
            semDados(ctx, width, height, 'Sem estoque ou vendas registradas.');
            return;
        }

        const left = 48, right = 20, top = 28, bottom = 48;
        const plotW = width - left - right, plotH = height - top - bottom;
        const max = niceMax(Math.max(...first, ...second, 1));
        const steps = 5;

        ctx.strokeStyle = '#DCE4EC';
        ctx.lineWidth = 1;
        for (let i = 0; i <= steps; i++) {
            const y = top + plotH - (plotH * i / steps);
            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(width - right, y);
            ctx.stroke();
            text(ctx, Math.round(max * i / steps), left - 8, y, 11, 'right');
        }

        const n = Math.max(labels.length, 1);
        const groupW = plotW / n;
        const barW = Math.min(34, groupW * 0.28);

        labels.forEach((label, i) => {
            const xCenter = left + groupW * i + groupW / 2;
            const p = suavizar(progressoItem(t, i, n));
            const vals = [first[i] || 0, second[i] || 0];
            vals.forEach((v, j) => {
                const h = (v / max) * plotH * p;    // a barra "cresce" da base para cima
                const x = xCenter + (j === 0 ? -barW - 2 : 2);
                const y = top + plotH - h;
                ctx.fillStyle = j === 0 ? COR_A : COR_B;
                ctx.fillRect(x, y, barW, h);
                if (v && p > 0.55) {
                    // o valor aparece quando a barra já está quase no lugar
                    text(ctx, formatar(v), x + barW / 2, y - 8, 10, 'center', (p - 0.55) / 0.45);
                }
            });
            const short = String(label).length > 14 ? String(label).slice(0, 13) + '…' : label;
            text(ctx, short, xCenter, top + plotH + 18, 10, 'center');
        });

        ctx.fillStyle = COR_A;
        ctx.fillRect(left, 8, 12, 12);
        text(ctx, firstLabel, left + 18, 14, 11);
        ctx.fillStyle = COR_B;
        ctx.fillRect(left + 105, 8, 12, 12);
        text(ctx, secondLabel, left + 123, 14, 11);
    }

    // --------------------------------------------- barras horizontais

    function drawBars(id, labels, values, titulo, prefix, t) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);

        if (vazio(values)) {
            semDados(ctx, width, height, 'Nenhuma venda registrada.');
            return;
        }

        const left = Math.min(150, Math.max(75, width * 0.25)), right = 35, top = 28, bottom = 25;
        const plotW = width - left - right, plotH = height - top - bottom;
        const max = niceMax(Math.max(...values, 1));
        const n = Math.max(labels.length, 1);
        const rowH = plotH / n;

        ctx.strokeStyle = '#DCE4EC';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
            const x = left + plotW * i / 5;
            ctx.beginPath();
            ctx.moveTo(x, top);
            ctx.lineTo(x, height - bottom);
            ctx.stroke();
            text(ctx, formatar(max * i / 5, prefix), x, height - 10, 10, 'center');
        }

        labels.forEach((label, i) => {
            const y = top + rowH * i + rowH * 0.2;
            const h = Math.max(10, rowH * 0.58);
            const p = suavizar(progressoItem(t, i, n));
            const w = (values[i] || 0) / max * plotW * p;   // a barra estica da esquerda
            ctx.fillStyle = COR_A;
            ctx.fillRect(left, y, w, h);
            const short = String(label).length > 22 ? String(label).slice(0, 21) + '…' : label;
            text(ctx, short, left - 8, y + h / 2, 11, 'right');
            if (p > 0.55) {
                text(ctx, formatar(values[i], prefix),
                    Math.min(left + w + 6, width - 4), y + h / 2, 10, 'left', (p - 0.55) / 0.45);
            }
        });

        text(ctx, titulo, left, 14, 11, 'left');
    }

    // ------------------------------------------------------------ donut

    function drawDonut(id, labels, values, t) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const { ctx, width, height } = setup(canvas);

        const total = values.reduce((a, b) => a + Number(b || 0), 0);
        if (!total) {
            semDados(ctx, width, height, 'Nenhuma forma de pagamento registrada.');
            return;
        }

        const p = suavizar(t);
        const cx = width * 0.35, cy = height * 0.5;
        const r = Math.min(width * 0.23, height * 0.34);
        let start = -Math.PI / 2;

        // o anel é preenchido girando, como um relógio
        values.forEach((v, i) => {
            const portion = Number(v) / total;
            const end = start + portion * Math.PI * 2 * p;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, start, end);
            ctx.closePath();
            ctx.fillStyle = CORES[i % CORES.length];
            ctx.fill();
            start = end;
        });

        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.58, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();

        // o número no centro conta de 0 até o total
        text(ctx, Math.round(total * p), cx, cy, 18, 'center');
        text(ctx, 'vendas', cx, cy + 22, 11, 'center');

        labels.forEach((label, i) => {
            const y = 35 + i * 28;
            const alpha = Math.max(0, Math.min(1, (p - 0.5) * 2));
            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.fillStyle = CORES[i % CORES.length];
            ctx.fillRect(width * 0.63, y - 7, 12, 12);
            ctx.restore();
            const pct = Math.round(Number(values[i]) / total * 100);
            text(ctx, String(label) + ' — ' + values[i] + ' (' + pct + '%)',
                width * 0.63 + 20, y, 11, 'left', alpha);
        });
    }

    // ------------------------------------------------------------ loop

    function desenhar(dados, t) {
        const c = dados.categorias || { labels: [], estoque: [], vendas: [], faturamento: [] };
        const p = dados.produtos || { labels: [], faturamento: [] };
        const pay = dados.pagamentos || { labels: [], valores: [] };

        drawGroupedBars('grafico-categorias', c.labels, c.estoque, c.vendas, 'Estoque', 'Vendas', t);
        drawBars('grafico-faturamento', p.labels, p.faturamento, 'Faturamento por produto', 'R$ ', t);
        drawDonut('grafico-pagamentos', pay.labels, pay.valores, t);
        drawBars('grafico-faturamento-categoria', c.labels, c.faturamento || [],
            'Faturamento por categoria', 'R$ ', t);
    }

    function render(animar) {
        const dados = getData();
        if (!dados) return;

        if (!animar || semAnimacao) {
            desenhar(dados, 1);
            return;
        }

        cancelAnimationFrame(window.__sevAnim);
        const inicio = performance.now();
        (function passo(agora) {
            const t = Math.min(1, (agora - inicio) / DURACAO);
            desenhar(dados, t);
            if (t < 1) window.__sevAnim = requestAnimationFrame(passo);
        })(inicio);
    }

    document.addEventListener('DOMContentLoaded', function () {
        render(true);
    });

    // No redimensionamento redesenha direto, sem repetir a animação.
    window.addEventListener('resize', function () {
        clearTimeout(window.__sevChartTimer);
        window.__sevChartTimer = setTimeout(function () {
            render(false);
        }, 150);
    });
})();
