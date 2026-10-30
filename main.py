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
        self.running = False
        self.stocks = [
            'RELIANCE.NS',
            'TCS.NS',
            'INFY.NS',
            'HDFCBANK.NS',
            'ICICIBANK.NS',
            'SBIN.NS',
            'BHARTIARTL.NS',
            'ITC.NS',
            'KOTAKBANK.NS',
            'LT.NS',
            'AXISBANK.NS',
            'TATAMOTORS.NS',
        ]
        self.base_prices = {}

        # Main Layout
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Header Title
        title = Label(
            text='[b]NSE 1% LADDER SCANNER[/b]',
            markup=True,
            font_size='22sp',
            size_hint_y=None,
            height=40,
            color=(0.2, 0.7, 1, 1),
        )
        root.add_widget(title)

        # Status Label
        self.status_lbl = Label(
            text='Status: Stopped',
            font_size='16sp',
            size_hint_y=None,
            height=30,
            color=(0.8, 0.8, 0.8, 1),
        )
        root.add_widget(self.status_lbl)

        # Start / Stop Button
        self.toggle_btn = Button(
            text='START SCANNER',
            font_size='18sp',
            size_hint_y=None,
            height=50,
            background_color=(0.1, 0.7, 0.3, 1),
        )
        self.toggle_btn.bind(on_press=self.toggle_scanner)
        root.add_widget(self.toggle_btn)

        # Log Display Area
        scroll = ScrollView(size_hint=(1, 1))
        self.log_lbl = Label(
            text='Logs will appear here once scanner starts...\n',
            size_hint_y=None,
            halign='left',
            valign='top',
            markup=True,
            font_size='14sp',
        )
        self.log_lbl.bind(
            texture_size=lambda instance, value: setattr(
                instance, 'height', value[1]
            )
        )
        self.log_lbl.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None))
        )
        scroll.add_widget(self.log_lbl)
        root.add_widget(scroll)

        return root

    def add_log(self, text):
        def update_label(dt):
            self.log_lbl.text = f"{text}\n" + self.log_lbl.text

        Clock.schedule_once(update_label)

    def toggle_scanner(self, instance):
        if not self.running:
            self.running = True
            self.toggle_btn.text = 'STOP SCANNER'
            self.toggle_btn.background_color = (0.9, 0.2, 0.2, 1)
            self.status_lbl.text = 'Status: Scanning active...'
            self.status_lbl.color = (0.2, 1, 0.3, 1)
            self.add_log(
                '[color=00ffea]--- Scanner Started Tracking ---[/color]'
            )

            # Background thread to avoid freezing UI
            t = threading.Thread(target=self.scan_loop)
            t.daemon = True
            t.start()
        else:
            self.running = False
            self.toggle_btn.text = 'START SCANNER'
            self.toggle_btn.background_color = (0.1, 0.7, 0.3, 1)
            self.status_lbl.text = 'Status: Stopped'
            self.status_lbl.color = (0.8, 0.8, 0.8, 1)
            self.add_log('[color=ff5555]--- Scanner Stopped ---[/color]')

    def fetch_price(self, symbol):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                price = data['chart']['result'][0]['meta'][
                    'regularMarketPrice'
                ]
                return float(price)
        except Exception:
            return None

    def scan_loop(self):
        while self.running:
            for sym in self.stocks:
                if not self.running:
                    break

                price = self.fetch_price(sym)
                if price is not None:
                    clean_name = sym.replace('.NS', '')

                    # Set initial baseline price
                    if sym not in self.base_prices:
                        self.base_prices[sym] = price
                        self.add_log(f'Init: {clean_name} @ ₹{price:.2f}')
                    else:
                        base = self.base_prices[sym]
                        pct = ((price - base) / base) * 100

                        # Check 1% Movement Ladder
                        if pct >= 1.0:
                            msg = f'[b][color=00ff00]▲ 1% UP: {clean_name} @ ₹{price:.2f} (+{pct:.2f}%)[/color][/b]'
                            self.add_log(msg)
                            self.base_prices[sym] = price  # Reset ladder baseline
                        elif pct <= -1.0:
                            msg = f'[b][color=ff3333]▼ 1% DOWN: {clean_name} @ ₹{price:.2f} ({pct:.2f}%)[/color][/b]'
                            self.add_log(msg)
                            self.base_prices[sym] = price  # Reset ladder baseline

                time.sleep(1)  # Interval between stock requests

            time.sleep(5)  # Wait before repeating the watchlist


if __name__ == '__main__':
    LadderScannerApp().run()
