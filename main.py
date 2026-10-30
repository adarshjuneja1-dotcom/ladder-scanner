import json
import threading
import time
import urllib.request
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

class LadderScannerApp(App):
    def build(self):
        self.is_scanning = False
        self.base_prices = {}
        self.ladder_step = 1.0  # 1% move check

        # Top-level layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header Title
        title_label = Label(
            text="Ladder Scanner (NSE 1%)",
            size_hint_y=0.1,
            font_size='20sp',
            bold=True
        )
        root.add_widget(title_label)

        # Start / Stop Button
        self.btn_toggle = Button(
            text="START SCANNER",
            size_hint_y=0.12,
            font_size='18sp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        self.btn_toggle.bind(on_release=self.toggle_scan)
        root.add_widget(self.btn_toggle)

        # Scrollable log area for alerts on screen
        scroll = ScrollView(size_hint_y=0.78)
        self.log_label = Label(
            text="Scanner ready. Click START to begin...\n",
            size_hint_y=None,
            font_size='14sp',
            halign='left',
            valign='top'
        )
        self.log_label.bind(
            width=lambda *x: setattr(self.log_label, 'text_size', (self.log_label.width, None))
        )
        self.log_label.bind(
            texture_size=lambda *x: setattr(self.log_label, 'height', self.log_label.texture_size[1])
        )
        scroll.add_widget(self.log_label)
        root.add_widget(scroll)

        return root

    def append_log(self, text):
        # Clock ke zariye UI safely update hota hai
        Clock.schedule_once(lambda dt: self._update_ui_text(text))

    def _update_ui_text(self, text):
        t_now = time.strftime("%H:%M:%S")
        self.log_label.text = f"[{t_now}] {text}\n" + self.log_label.text

    def toggle_scan(self, instance):
        if not self.is_scanning:
            self.is_scanning = True
            self.btn_toggle.text = "STOP SCANNER"
            self.btn_toggle.background_color = (0.8, 0.2, 0.2, 1)
            self.append_log("Scanner started. Fetching initial watchlist...")
            threading.Thread(target=self.run_scanner_loop, daemon=True).start()
        else:
            self.is_scanning = False
            self.btn_toggle.text = "START SCANNER"
            self.btn_toggle.background_color = (0.2, 0.7, 0.3, 1)
            self.append_log("Scanner stopped.")

    def run_scanner_loop(self):
        # Sample active symbols list
        symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "SBIN", "BHARTIARTL", "ITC", "LT", "KOTAKBANK"
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        while self.is_scanning:
            for sym in symbols:
                if not self.is_scanning:
                    break
                try:
                    # Replace with your actual live price endpoint or Yahoo finance ticker URL
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.NS"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        data = json.loads(response.read().decode())
                        meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                        price = meta.get('regularMarketPrice')

                        if price:
                            if sym not in self.base_prices:
                                self.base_prices[sym] = price
                                self.append_log(f"Watch: {sym} @ {price:.2f}")
                            else:
                                base = self.base_prices[sym]
                                pct_change = ((price - base) / base) * 100

                                # Trigger alert on 1% move up or down
                                if abs(pct_change) >= self.ladder_step:
                                    direction = "UP ▲" if pct_change > 0 else "DOWN ▼"
                                    alert_msg = f"ALERT: {sym} moved {pct_change:+.2f}% ({direction}) -> Now: {price:.2f}"
                                    self.append_log(alert_msg)
                                    # Reset base to current ladder step
                                    self.base_prices[sym] = price
                except Exception as e:
                    pass

                time.sleep(1)

            # Pause between scanner cycles
            for _ in range(15):
                if not self.is_scanning:
                    break
                time.sleep(1)
