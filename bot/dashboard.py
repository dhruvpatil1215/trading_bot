# -*- coding: utf-8 -*-
"""
Lightweight web dashboard for the trading bot.
Uses Python's built-in http.server — no Flask or extra deps needed.
Run with: python -m bot.dashboard
"""

import json
import os
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from bot.logging_config import setup_logging
from bot.orders import execute_order
from bot.history import get_history

logger = logging.getLogger("trading_bot.dashboard")

PORT = 8080

def get_stats():
    """Calculate summary stats from history."""
    from bot.history import get_history
    history = get_history()
    total = len(history)
    simulated = sum(1 for t in history if t.get("order", {}).get("simulated", False))
    live = total - simulated
    
    return {
        "total": total,
        "simulated": simulated,
        "live": live
    }

# ---------------------------------------------------------
# DASHBOARD HTML/CSS/JS
# premium theme: dark, glassmorphic, inter font
# ---------------------------------------------------------
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Trading Bot Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            --bg-deep: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.7);
            --border-card: rgba(148, 163, 184, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #6366f1;
            --accent-hover: #818cf8;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }

        * {
            margin: 0; padding: 0; box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.1) 0px, transparent 50%);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 1080px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
        }

        /* HEADER */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.6s ease-out;
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .logo h1 {
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-card);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--warning);
            box-shadow: 0 0 10px var(--warning);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
        }

        /* STATS GRID */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
            margin-bottom: 2.5rem;
            animation: fadeIn 0.8s ease-out;
        }

        .stat-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-card);
            padding: 1.25rem;
            border-radius: 16px;
            text-align: center;
        }

        .stat-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
        }

        /* MAIN CONTENT */
        .grid-layout {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 2rem;
            align-items: start;
        }

        .card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-card);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        }

        h2 {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* FORM STYLES */
        .form-group {
            margin-bottom: 1.25rem;
        }

        label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            text-transform: uppercase;
        }

        input, select {
            width: 100%;
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border-card);
            color: white;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.9rem;
            font-family: inherit;
            transition: all 0.2s;
            outline: none;
        }

        input:focus, select:focus {
            border-color: var(--accent);
            background: rgba(15, 23, 42, 0.8);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }

        .btn {
            width: 100%;
            background: var(--accent);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 0.5rem;
        }

        .btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }

        .btn:active { transform: translateY(0); }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* HISTORY TABLE */
        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            max-height: 600px;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.85rem;
        }

        th {
            position: sticky; top: 0;
            background: #1e293b;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-card);
            z-index: 10;
        }

        td {
            padding: 14px 16px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.05);
        }

        tr:hover td {
            background: rgba(148, 163, 184, 0.05);
        }

        /* BADGES */
        .badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .badge-buy { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .badge-sell { background: rgba(239, 68, 68, 0.1); color: var(--danger); }
        .badge-sim { background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.2); }
        .badge-live { background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); }

        /* TOAST */
        #toast {
            position: fixed;
            bottom: 2rem; right: 2rem;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            backdrop-filter: blur(12px);
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            z-index: 1000;
            transform: translateY(100px);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            opacity: 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }

        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        #toast.success { background: rgba(16, 185, 129, 0.9); border: 1px solid rgba(255,255,255,0.2); }
        #toast.error { background: rgba(239, 68, 68, 0.9); border: 1px solid rgba(255,255,255,0.2); }

        /* LOADING SPINNER */
        .spinner {
            width: 18px; height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        @keyframes fadeIn {
            from { opacity: 0; } to { opacity: 1; }
        }

        /* RESPONSIVE */
        @media (max-width: 900px) {
            .grid-layout { grid-template-columns: 1fr; }
            .container { padding: 1rem; }
            header { flex-direction: column; gap: 1rem; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <h1>ANTIGRAVITY BOT</h1>
            </div>
            <div class="status-pill">
                <div class="status-dot"></div>
                SIMULATION MODE ENABLED
            </div>
        </header>

        <section class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value" id="stat-total">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Live Orders</div>
                <div class="stat-value" style="color: var(--success);" id="stat-live">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Simulated</div>
                <div class="stat-value" style="color: var(--warning);" id="stat-sim">--</div>
            </div>
        </section>

        <main class="grid-layout">
            <!-- PLACE ORDER -->
            <div class="card" style="animation: fadeInLeft 0.6s ease-out;">
                <h2>📝 NEW TRADE</h2>
                <form id="orderForm" onsubmit="submitForm(event)">
                    <div class="form-group">
                        <label>Instrument</label>
                        <select id="symbol" name="symbol">
                            <option value="BTCUSDT">BTCUSDT (Bitcoin)</option>
                            <option value="ETHUSDT">ETHUSDT (Ethereum)</option>
                            <option value="SOLUSDT">SOLUSDT (Solana)</option>
                            <option value="BNBUSDT">BNBUSDT (Binance Coin)</option>
                            <option value="XRPUSDT">XRPUSDT (Ripple)</option>
                        </select>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label>Side</label>
                            <select id="side" name="side" style="color: var(--success); font-weight: 700;">
                                <option value="BUY" style="color: var(--success);">BUY</option>
                                <option value="SELL" style="color: var(--danger);">SELL</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Type</label>
                            <select id="orderType" name="type" onchange="toggleOrderType()">
                                <option value="MARKET">MARKET</option>
                                <option value="LIMIT">LIMIT</option>
                                <option value="STOP_LIMIT">STOP LIMIT</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Quantity</label>
                        <input type="number" step="0.0001" id="quantity" name="quantity" placeholder="0.02" required>
                    </div>

                    <div id="priceField" class="form-group" style="display: none;">
                        <label>Limit Price ($)</label>
                        <input type="number" step="0.01" id="price" name="price" placeholder="68500.00">
                    </div>

                    <div id="stopPriceField" class="form-group" style="display: none;">
                        <label>Stop Price ($)</label>
                        <input type="number" step="0.01" id="stop_price" name="stop_price" placeholder="67000.00">
                    </div>

                    <button type="submit" class="btn" id="submitBtn">
                        EXECUTE ORDER
                    </button>
                </form>
            </div>

            <!-- HISTORY -->
            <div class="card" style="animation: fadeInRight 0.6s ease-out;">
                <h2>📜 TRADE HISTORY</h2>
                <div id="historyTable" class="table-container">
                    <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                        <div class="spinner" style="margin: 0 auto 1rem;"></div>
                        Synchronizing with blockchain...
                    </div>
                </div>
            </div>
        </main>
    </div>

    <div id="toast"></div>

    <script>
        const sideEl = document.getElementById('side');
        sideEl.addEventListener('change', () => {
            sideEl.style.color = sideEl.value === 'BUY' ? 'var(--success)' : 'var(--danger)';
        });

        function toggleOrderType() {
            const type = document.getElementById('orderType').value;
            document.getElementById('priceField').style.display = (type !== 'MARKET') ? 'block' : 'none';
            document.getElementById('stopPriceField').style.display = (type === 'STOP_LIMIT') ? 'block' : 'none';
        }

        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.className = 'show ' + type;
            setTimeout(() => { toast.className = ''; }, 4000);
        }

        async function updateStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-total').innerText = data.total;
                document.getElementById('stat-live').innerText = data.live;
                document.getElementById('stat-sim').innerText = data.simulated;
            } catch (e) { console.error('Stats fail', e); }
        }
        async function fetchHistory() {
            try {
                const res = await fetch('/api/history');
                const trades = await res.json();
                const container = document.getElementById('historyTable');

                if (trades.length === 0) {
                    container.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--text-secondary);">No active trades found.</div>`;
                    return;
                }

                let html = `<table><thead><tr>
                    <th>Time</th><th>Pair</th><th>Side</th><th>Type</th><th>Qty</th><th>Price</th><th>Mode</th>
                </tr></thead><tbody>`;

                trades.reverse().forEach(t => {
                    const o = t.order || {};
                    const sideClass = o.side === 'BUY' ? 'badge-buy' : 'badge-sell';
                    const modeClass = o.simulated ? 'badge-sim' : 'badge-live';
                    const modeText = o.simulated ? 'SIM' : 'LIVE';
                    const timeStr = t.recorded_at ? t.recorded_at.split(' ')[1] : '--:--';
                    
                    html += `<tr>
                        <td style="color: var(--text-secondary); font-size: 0.75rem;">${timeStr}</td>
                        <td style="font-weight: 600;">${o.symbol}</td>
                        <td><span class="badge ${sideClass}">${o.side}</span></td>
                        <td>${o.type}</td>
                        <td>${o.executedQty || o.quantity}</td>
                        <td>$${parseFloat(o.avgPrice || o.price).toLocaleString()}</td>
                        <td><span class="badge ${modeClass}">${modeText}</span></td>
                    </tr>`;
                });

                html += '</tbody></table>';
                container.innerHTML = html;
                updateStats();
            } catch (e) {
                console.error('History fail', e);
            }
        }

        updateStats();

        async function submitForm(e) {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const originalText = btn.innerHTML;
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> EXECUTING...';

            const formData = new FormData(e.target);
            const data = new URLSearchParams(formData);

            try {
                const res = await fetch('/api/order', { method: 'POST', body: data });
                const result = await res.json();

                if (result.success) {
                    showToast(`✅ ${result.order.side} Order Executed!`, 'success');
                    e.target.reset();
                    toggleOrderType();
                    fetchHistory();
                } else {
                    showToast(`❌ ${result.error || 'Execution Failed'}`, 'error');
                }
            } catch (err) {
                showToast('❌ Connection Lost', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        // Initial load & polling
        fetchHistory();
        setInterval(fetchHistory, 5000);
    </script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for the dashboard."""

    def log_message(self, format, *args):
        # use our logger instead of default stderr output
        logger.debug(f"HTTP {args[0]}")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_html(DASHBOARD_HTML)

        elif self.path == "/api/history":
            history = get_history()
            self._send_json(history)

        elif self.path == "/api/stats":
            stats = get_stats()
            self._send_json(stats)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/order":
            # read form data
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            params = urllib.parse.parse_qs(body)

            # extract params (parse_qs returns lists)
            symbol = params.get("symbol", [None])[0]
            side = params.get("side", [None])[0]
            order_type = params.get("type", [None])[0]
            quantity = params.get("quantity", [None])[0]
            price = params.get("price", [None])[0]
            stop_price = params.get("stop_price", [None])[0]

            # basic check
            if not all([symbol, side, order_type, quantity]):
                self._send_json({"success": False, "error": "Missing required fields"}, 400)
                return

            # don't send empty strings for optional fields
            if not price:
                price = None
            if not stop_price:
                stop_price = None

            try:
                result = execute_order(symbol, side, order_type, quantity, price, stop_price)
                if result:
                    self._send_json({"success": True, "order": result})
                else:
                    self._send_json({"success": False, "error": "Order failed — check server logs"})
            except Exception as e:
                logger.error(f"Dashboard order error: {e}")
                self._send_json({"success": False, "error": str(e)}, 500)

        else:
            self.send_response(404)
            self.end_headers()


def run_dashboard(port=None):
    """Start the dashboard server."""
    p = port or PORT
    setup_logging()

    server = HTTPServer(("0.0.0.0", p), DashboardHandler)
    print(f"""
+----------------------------------------------+
|   Trading Bot Dashboard                      |
|   Running at: http://localhost:{p}           |
|                                              |
|   Press Ctrl+C to stop                       |
+----------------------------------------------+
    """)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  👋 Dashboard stopped.\n")
        server.server_close()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_dashboard(port)
