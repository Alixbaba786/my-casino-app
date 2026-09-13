import random
import secrets
import json
import urllib.request
import urllib.parse
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


# ============================================================
# APP CONFIGURATION
# ============================================================

APP_NAME = "PK786 Casino"
STARTING_COINS = 5000.0
BET_PRESETS = [50, 100, 250, 500, 1000, 2500]

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = "https://YOUR_SUPABASE_PROJECT_ID.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"

# --- TELEGRAM BOT CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

BG = (0.025, 0.035, 0.065, 1)
CARD = (0.065, 0.085, 0.14, 1)
CARD_2 = (0.09, 0.115, 0.18, 1)
TEXT = (0.94, 0.97, 1, 1)
MUTED = (0.58, 0.65, 0.76, 1)
GREEN = (0.0, 0.85, 0.62, 1)
PINK = (1.0, 0.20, 0.45, 1)
GOLD = (1.0, 0.72, 0.12, 1)
BLUE = (0.20, 0.48, 1.0, 1)
RED = (1.0, 0.22, 0.25, 1)


# ============================================================
# GLOBAL STATE & UTILS
# ============================================================

STATE = {
    "username": "Guest",
    "coins": STARTING_COINS,
    "history": [],
}


def send_telegram_alert(message):
    """Telegram Bot alert notification using native urllib"""
    if not TELEGRAM_BOT_TOKEN or "YOUR_" in TELEGRAM_BOT_TOKEN:
        return

    def _send(dt=None):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"Telegram Notification Error: {e}")

    Clock.schedule_once(lambda dt: _send(), 0.1)


def sync_supabase_profile(username, coins):
    """Supabase REST API user balance & activity sync"""
    if not SUPABASE_URL or "YOUR_" in SUPABASE_URL:
        return

    def _sync(dt=None):
        try:
            url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }
            payload = json.dumps({
                "username": username,
                "phone": "03000000000",
                "balance": float(coins)
            }).encode('utf-8')

            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"Supabase Sync Error: {e}")

    Clock.schedule_once(lambda dt: _sync(), 0.1)


def money(value):
    return f"{float(value):,.2f}"


def add_history(title, amount, note=""):
    STATE["history"].insert(
        0,
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "amount": float(amount),
            "note": note,
        },
    )
    STATE["history"] = STATE["history"][:50]
    sync_supabase_profile(STATE["username"], STATE["coins"])


def toast(message, title="PK786 DEMO"):
    content = BoxLayout(orientation="vertical", padding=18)
    content.add_widget(
        Label(
            text=message,
            color=TEXT,
            font_size="16sp",
            halign="center",
            valign="middle",
        )
    )
    popup = Popup(
        title=title,
        content=content,
        size_hint=(0.86, None),
        height=180,
        separator_color=GREEN,
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 1.7)


def spend(amount, title):
    amount = float(amount)
    if amount <= 0:
        return False
    if STATE["coins"] < amount:
        toast("Not enough demo coins.")
        return False

    STATE["coins"] -= amount
    add_history(title, -amount, "Bet placed")
    return True


def award(amount, title, note="Win"):
    amount = max(0.0, float(amount))
    STATE["coins"] += amount
    if amount:
        add_history(title, amount, note)
        if amount >= 500:
            msg = f"🏆 *BIG WIN ALERT*\n👤 Player: `{STATE['username']}`\n🎮 Game: {title}\n💰 Won: *{money(amount)}* coins"
            send_telegram_alert(msg)


# ============================================================
# UI COMPONENTS
# ============================================================

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = kwargs.pop("padding", 14)
        self.spacing = kwargs.pop("spacing", 10)
        self.bg_color = kwargs.pop("bg_color", CARD)
        self.radius = 18
        self._draw()
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius],
            )
            Color(0.18, 0.25, 0.38, 0.7)
            Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    self.radius,
                ),
                width=1.1,
            )


class AppButton(Button):
    def __init__(self, **kwargs):
        bg = kwargs.pop("btn_color", BLUE)
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg
        self.color = TEXT
        self.bold = True
        self.font_size = kwargs.get("font_size", "15sp")


class DemoScreen(Screen):
    def header(self, title, back=True):
        bar = BoxLayout(
            size_hint_y=None,
            height=58,
            spacing=8,
            padding=(8, 6),
        )

        if back:
            back_btn = AppButton(
                text="‹ BACK",
                size_hint_x=None,
                width=90,
                btn_color=(0.15, 0.19, 0.29, 1),
            )
            back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "lobby"))
            bar.add_widget(back_btn)

        bar.add_widget(
            Label(
                text=f"[b]{title}[/b]",
                markup=True,
                color=TEXT,
                font_size="20sp",
                halign="left",
            )
        )

        self.balance_label = Label(
            text=f"[b]{money(STATE['coins'])}[/b]",
            markup=True,
            color=GREEN,
            font_size="15sp",
            size_hint_x=None,
            width=125,
            halign="right",
        )
        bar.add_widget(self.balance_label)
        return bar

    def refresh_balance(self):
        if hasattr(self, "balance_label"):
            self.balance_label.text = f"[b]{money(STATE['coins'])}[/b]"


class BottomNav(BoxLayout):
    def __init__(self, manager, **kwargs):
        super().__init__(**kwargs)
        self.manager_ref = manager
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 58
        self.spacing = 5
        self.padding = 5

        for caption, screen in [
            ("⌂ Lobby", "lobby"),
            ("◈ Wallet", "wallet"),
            ("● Account", "account"),
        ]:
            btn = AppButton(
                text=caption,
                btn_color=(0.08, 0.12, 0.20, 1),
                font_size="13sp",
            )
            btn.bind(
                on_release=lambda x, s=screen: setattr(
                    self.manager_ref, "current", s
                )
            )
            self.add_widget(btn)


def page_background(layout):
    with layout.canvas.before:
        Color(*BG)
        Rectangle(pos=(0, 0), size=(5000, 5000))


# ============================================================
# LOGIN SCREEN
# ============================================================

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=22,
            spacing=16,
        )
        page_background(root)

        root.add_widget(
            Label(
                text="[b][color=ff2050]PK786[/color] [color=00e0aa]DEMO[/color][/b]",
                markup=True,
                font_size="38sp",
                size_hint_y=None,
                height=100,
            )
        )

        root.add_widget(
            Label(
                text="[color=9aa8c0]Virtual coins entertainment app[/color]",
                markup=True,
                font_size="16sp",
                size_hint_y=None,
                height=35,
            )
        )

        card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=280,
            padding=20,
        )

        card.add_widget(
            Label(
                text="[b]WELCOME PLAYER[/b]",
                markup=True,
                color=GOLD,
                font_size="22sp",
                size_hint_y=None,
                height=42,
            )
        )

        self.username = TextInput(
            hint_text="Enter username",
            multiline=False,
            size_hint_y=None,
            height=56,
            font_size="17sp",
            padding=(14, 14),
        )
        card.add_widget(self.username)

        enter = AppButton(
            text="ENTER DEMO LOBBY",
            btn_color=GREEN,
            color=(0.02, 0.05, 0.08, 1),
            size_hint_y=None,
            height=58,
        )
        enter.bind(on_release=self.login)
        card.add_widget(enter)

        card.add_widget(
            Label(
                text="[color=ffcc66]DEMO ONLY — NO REAL MONEY[/color]",
                markup=True,
                font_size="13sp",
                size_hint_y=None,
                height=35,
            )
        )

        root.add_widget(card)
        root.add_widget(Label())
        self.add_widget(root)

    def login(self, instance):
        name = self.username.text.strip()
        if len(name) < 2:
            toast("Username kam az kam 2 characters ka hona chahiye.")
            return

        STATE["username"] = name[:24]
        send_telegram_alert(f"🔑 *PLAYER LOGIN*\nUsername: `{STATE['username']}`\nCoins: `{money(STATE['coins'])}`")
        sync_supabase_profile(STATE["username"], STATE["coins"])
        self.manager.current = "lobby"


# ============================================================
# LOBBY SCREEN
# ============================================================

class LobbyScreen(DemoScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", spacing=8)
        page_background(root)

        top = self.header("PK786")
        root.add_widget(top)

        notice = Card(
            orientation="vertical",
            size_hint_y=None,
            height=86,
            bg_color=(0.08, 0.18, 0.20, 1),
        )
        notice.add_widget(
            Label(
                text="[b]DEMO WALLET[/b]\n[color=9feadd]All coins are virtual and have no cash value.[/color]",
                markup=True,
                color=TEXT,
                font_size="15sp",
                halign="center",
            )
        )
        root.add_widget(notice)

        scroll = ScrollView()
        grid = GridLayout(
            cols=2,
            spacing=12,
            padding=12,
            size_hint_y=None,
        )
        grid.bind(minimum_height=grid.setter("height"))

        games = [
            ("🚀", "Rocket Crash", "crash", RED),
            ("🎰", "VIP Slots", "slots", PINK),
            ("🎡", "Lucky Spin", "spin", GOLD),
            ("💣", "Mines Field", "mines", BLUE),
        ]

        for icon, title, screen, color in games:
            card = Card(
                orientation="vertical",
                size_hint_y=None,
                height=205,
                padding=10,
            )
            card.add_widget(
                Label(
                    text=icon,
                    font_size="44sp",
                    size_hint_y=None,
                    height=62,
                )
            )
            card.add_widget(
                Label(
                    text=f"[b]{title}[/b]",
                    markup=True,
                    color=TEXT,
                    font_size="16sp",
                    size_hint_y=None,
                    height=34,
                )
            )
            button = AppButton(
                text="PLAY DEMO",
                btn_color=color,
                size_hint_y=None,
                height=48,
            )
            button.bind(
                on_release=lambda x, s=screen: setattr(
                    self.manager, "current", s
                )
            )
            card.add_widget(button)
            grid.add_widget(card)

        scroll.add_widget(grid)
        root.add_widget(scroll)
        root.add_widget(BottomNav(self.manager))
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()


# ============================================================
# WALLET SCREEN
# ============================================================

class WalletScreen(DemoScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", spacing=10)
        page_background(root)
        root.add_widget(self.header("Virtual Wallet"))

        balance_card = Card(
            orientation="vertical",
            size_hint_y=None,
            height=145,
        )
        balance_card.add_widget(
            Label(
                text="[color=9aa8c0]AVAILABLE DEMO COINS[/color]",
                markup=True,
                font_size="14sp",
            )
        )
        self.big_balance = Label(
            text=money(STATE["coins"]),
            color=GREEN,
            font_size="32sp",
        )
        balance_card.add_widget(self.big_balance)
        balance_card.add_widget(
            Label(
                text="[color=ffcc66]No deposits or withdrawals available[/color]",
                markup=True,
                font_size="13sp",
            )
        )
        root.add_widget(balance_card)

        self.history_box = BoxLayout(
            orientation="vertical",
            spacing=5,
            size_hint_y=None,
            padding=8,
        )
        self.history_box.bind(minimum_height=self.history_box.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.history_box)
        root.add_widget(scroll)
        root.add_widget(BottomNav(self.manager))
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()
        self.big_balance.text = money(STATE["coins"])
        self.history_box.clear_widgets()

        if not STATE["history"]:
            self.history_box.add_widget(
                Label(
                    text="No transactions yet.",
                    color=MUTED,
                    size_hint_y=None,
                    height=45,
                )
            )
            return

        for item in STATE["history"]:
            amount = item["amount"]
            color = "00e0aa" if amount >= 0 else "ff6677"
            sign = "+" if amount >= 0 else ""
            self.history_box.add_widget(
                Label(
                    text=(
                        f"[b]{item['title']}[/b]  "
                        f"[color={color}]{sign}{money(amount)}[/color]\n"
                        f"[color=8998b2]{item['time']} • {item['note']}[/color]"
                    ),
                    markup=True,
                    color=TEXT,
                    halign="left",
                    size_hint_y=None,
                    height=58,
                )
            )

    def refresh_balance(self):
        super().refresh_balance()
        if hasattr(self, "big_balance"):
            self.big_balance.text = money(STATE["coins"])


# ============================================================
# ACCOUNT SCREEN
# ============================================================

class AccountScreen(DemoScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", spacing=12, padding=14)
        page_background(root)
        root.add_widget(self.header("Account"))

        card = Card(orientation="vertical", size_hint_y=None, height=230)
        card.add_widget(
            Label(
                text="[b]PLAYER PROFILE[/b]",
                markup=True,
                color=GOLD,
                font_size="20sp",
            )
        )
        self.profile = Label(color=TEXT, font_size="17sp")
        card.add_widget(self.profile)
        card.add_widget(
            Label(
                text="[color=9aa8c0]This application uses local demo data only.[/color]",
                markup=True,
                font_size="13sp",
            )
        )
        copy = AppButton(
            text="COPY DEMO SUPPORT TEXT",
            btn_color=BLUE,
            size_hint_y=None,
            height=52,
        )
        copy.bind(
            on_release=lambda x: (
                Clipboard.copy("PK786 Demo Support"),
                toast("Text copied"),
            )
        )
        card.add_widget(copy)
        root.add_widget(card)

        root.add_widget(Label())
        root.add_widget(BottomNav(self.manager))
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()
        self.profile.text = (
            f"[b]Username:[/b] {STATE['username']}\n"
            f"[b]Demo coins:[/b] {money(STATE['coins'])}\n"
            f"[b]Mode:[/b] Virtual coins only"
        )


# ============================================================
# BASE GAME SCREEN
# ============================================================

class GameScreen(DemoScreen):
    def make_bets(self, selected=50):
        self.selected_bet = selected
        self.bet_buttons = {}
        grid = GridLayout(
            cols=3,
            spacing=6,
            size_hint_y=None,
            height=120,
        )

        for value in BET_PRESETS:
            button = AppButton(
                text=str(value),
                btn_color=GOLD if value == selected else (0.12, 0.17, 0.27, 1),
                color=(0.04, 0.05, 0.07, 1) if value == selected else TEXT,
                font_size="14sp",
            )
            button.bind(on_release=lambda x, v=value: self.select_bet(v))
            self.bet_buttons[value] = button
            grid.add_widget(button)

        return grid

    def select_bet(self, value):
        if getattr(self, "busy", False):
            return
        self.selected_bet = value
        for amount, button in self.bet_buttons.items():
            active = amount == value
            button.background_color = GOLD if active else (0.12, 0.17, 0.27, 1)
            button.color = (0.04, 0.05, 0.07, 1) if active else TEXT
        if hasattr(self, "action_button"):
            self.action_button.text = f"BET {value} COINS"

    def on_leave(self, *args):
        self.busy = False


# ============================================================
# GAME: SLOTS
# ============================================================

class SlotsScreen(GameScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.busy = False

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)
        page_background(root)
        root.add_widget(self.header("VIP Slots"))

        self.reels = Label(
            text="🍒     🍋     🔔",
            font_size="42sp",
            size_hint_y=None,
            height=130,
        )
        root.add_widget(self.reels)

        card = Card(orientation="vertical", size_hint_y=None, height=250)
        card.add_widget(
            Label(
                text="[b]SELECT BET[/b]",
                markup=True,
                color=GOLD,
                size_hint_y=None,
                height=30,
            )
        )
        card.add_widget(self.make_bets())

        self.action_button = AppButton(
            text="BET 50 COINS",
            btn_color=PINK,
            size_hint_y=None,
            height=58,
        )
        self.action_button.bind(on_release=self.play)
        card.add_widget(self.action_button)
        root.add_widget(card)

        root.add_widget(
            Label(
                text="[color=9aa8c0]3 same = 5x • 2 same = 1.5x • otherwise lose[/color]",
                markup=True,
                size_hint_y=None,
                height=35,
            )
        )
        root.add_widget(Label())
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()

    def play(self, instance):
        if self.busy:
            return

        bet = self.selected_bet
        if not spend(bet, "VIP Slots"):
            return

        self.busy = True
        self.action_button.disabled = True

        symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]
        result = [secrets.choice(symbols) for _ in range(3)]
        self.reels.text = "     ".join(result)

        if result[0] == result[1] == result[2]:
            payout = bet * 5
        elif result[0] == result[1] or result[1] == result[2]:
            payout = bet * 1.5
        else:
            payout = 0

        award(payout, "VIP Slots", "Slot payout")
        self.refresh_balance()

        if payout:
            toast(f"You won {money(payout)} demo coins!", "WIN")
        else:
            toast("No win this round.")

        self.busy = False
        self.action_button.disabled = False


# ============================================================
# GAME: LUCKY SPIN
# ============================================================

class SpinScreen(GameScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.busy = False

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)
        page_background(root)
        root.add_widget(self.header("Lucky Spin"))

        self.result = Label(
            text="🎡\n\nPRESS SPIN",
            font_size="27sp",
            halign="center",
        )
        root.add_widget(self.result)

        card = Card(orientation="vertical", size_hint_y=None, height=250)
        card.add_widget(
            Label(
                text="[b]SELECT BET[/b]",
                markup=True,
                color=GOLD,
                size_hint_y=None,
                height=30,
            )
        )
        card.add_widget(self.make_bets())

        self.action_button = AppButton(
            text="BET 50 COINS",
            btn_color=GOLD,
            color=(0.04, 0.05, 0.07, 1),
            size_hint_y=None,
            height=58,
        )
        self.action_button.bind(on_release=self.spin)
        card.add_widget(self.action_button)
        root.add_widget(card)
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()

    def spin(self, instance):
        if self.busy:
            return

        bet = self.selected_bet
        if not spend(bet, "Lucky Spin"):
            return

        self.busy = True
        self.action_button.disabled = True

        outcomes = [
            ("0x", 0),
            ("0x", 0),
            ("0.5x", 0.5),
            ("1x", 1),
            ("1.5x", 1.5),
            ("2x", 2),
            ("3x", 3),
        ]
        label, multiplier = random.choice(outcomes)
        payout = bet * multiplier

        award(payout, "Lucky Spin", f"Result {label}")
        self.result.text = f"🎡\n\n[b]{label}[/b]"
        self.result.markup = True
        self.refresh_balance()

        toast(f"Spin result: {label}\nPayout: {money(payout)} coins")

        self.busy = False
        self.action_button.disabled = False


# ============================================================
# GAME: ROCKET CRASH
# ============================================================

class CrashScreen(GameScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.busy = False
        self.running = False
        self.multiplier = 1.0
        self.crash_point = 1.0
        self.timer = None

        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        page_background(root)
        root.add_widget(self.header("Rocket Crash"))

        self.status = Label(
            text="🚀\n\n[b]READY[/b]\n\n1.00x",
            markup=True,
            font_size="28sp",
            halign="center",
        )
        root.add_widget(self.status)

        card = Card(orientation="vertical", size_hint_y=None, height=245)
        card.add_widget(self.make_bets())

        self.action_button = AppButton(
            text="BET 50 COINS",
            btn_color=GREEN,
            color=(0.02, 0.05, 0.07, 1),
            size_hint_y=None,
            height=58,
        )
        self.action_button.bind(on_release=self.action)
        card.add_widget(self.action_button)
        root.add_widget(card)

        root.add_widget(
            Label(
                text="[color=9aa8c0]Cash out before the rocket crashes.[/color]",
                markup=True,
                size_hint_y=None,
                height=30,
            )
        )
        self.add_widget(root)

    def on_enter(self):
        self.refresh_balance()

    def action(self, instance):
        if not self.running:
            bet = self.selected_bet
            if not spend(bet, "Rocket Crash"):
                return

            self.running = True
            self.busy = True
            self.multiplier = 1.0
            self.crash_point = round(random.uniform(1.15, 5.0), 2)

            self.action_button.text = "CASH OUT"
            self.action_button.background_color = GOLD
            self.action_button.color = (0.04, 0.05, 0.07, 1)
            self.status.text = "🚀\n\n[b]FLYING[/b]\n\n1.00x"
            self.timer = Clock.schedule_interval(self.tick, 0.08)
        else:
            self.cashout()

    def tick(self, dt):
        if not self.running:
            return

        self.multiplier = round(self.multiplier + 0.03, 2)
        self.status.text = (
            f"🚀\n\n[color=00e0aa][b]FLYING[/b][/color]\n\n"
            f"[size=38sp]{self.multiplier:.2f}x[/size]"
        )

        if self.multiplier >= self.crash_point:
            self.crash()

    def cashout(self):
        if not self.running:
            return

        self.stop_timer()
        payout = self.selected_bet * self.multiplier
        award(payout, "Rocket Crash", f"Cashed out at {self.multiplier:.2f}x")

        self.running = False
        self.busy = False
        self.action_button.text = f"BET {self.selected_bet} COINS"
        self.action_button.background_color = GREEN
        self.status.text = (
            f"🚀\n\n[color=00e0aa][b]CASHED OUT[/b][/color]\n\n"
            f"{self.multiplier:.2f}x"
        )
        self.refresh_balance()
        toast(f"You received {money(payout)} demo coins.", "CASH OUT")

    def crash(self):
        self.stop_timer()
        self.running = False
        self.busy = False
        self.action_button.text = f"BET {self.selected_bet} COINS"
        self.action_button.background_color = GREEN
        self.status.text = (
            f"💥\n\n[color=ff6677][b]CRASHED[/b][/color]\n\n"
            f"{self.crash_point:.2f}x"
        )
        self.refresh_balance()
        toast("Rocket crashed. Bet lost.")

    def stop_timer(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def on_leave(self, *args):
        self.stop_timer()
        self.running = False
        self.busy = False


# ============================================================
# GAME: MINES FIELD
# ============================================================

class MinesScreen(GameScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.busy = False
        self.active = False
        self.bet = 0
        self.mine_count = 5
        self.mines = set()
        self.revealed = set()
        self.current_multiplier = 1.0

        root = BoxLayout(orientation="vertical", padding=10, spacing=7)
        page_background(root)
        root.add_widget(self.header("Mines Field"))

        self.info = Label(
            text="Select a bet and start a round.",
            color=TEXT,
            size_hint_y=None,
            height=36,
        )
        root.add_widget(self.info)

        self.board = GridLayout(
            cols=5,
            spacing=5,
            padding=5,
            size_hint_y=None,
            height=300,
        )
        root.add_widget(self.board)

        card = Card(orientation="vertical", size_hint_y=None, height=235)
        card.add_widget(self.make_bets())

        self.mine_input = TextInput(
            text="5",
            hint_text="Mines: 1-20",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=45,
        )
        card.add_widget(self.mine_input)

        self.action_button = AppButton(
            text="START MINES",
            btn_color=BLUE,
            size_hint_y=None,
            height=52,
        )
        self.action_button.bind(on_release=self.start_or_cashout)
        card.add_widget(self.action_button)

        root.add_widget(card)
        self.add_widget(root)
        self.build_board()

    def build_board(self):
        self.board.clear_widgets()
        for index in range(25):
            button = AppButton(
                text="?",
                btn_color=(0.12, 0.18, 0.30, 1),
                font_size="20sp",
            )
            button.bind(
                on_release=lambda x, i=index: self.reveal(i)
            )
            self.board.add_widget(button)

    def on_enter(self):
        self.refresh_balance()

    def start_or_cashout(self, instance):
        if self.active:
            if self.current_multiplier <= 1:
                toast("At least one safe tile reveal karein.")
                return

            payout = self.bet * self.current_multiplier
            award(payout, "Mines", "Manual cash out")
            self.end_round(True)
            toast(f"Cashed out: {money(payout)} coins")
            return

        try:
            count = int(self.mine_input.text)
        except ValueError:
            count = 5

        if count < 1 or count > 20:
            toast("Mines 1 se 20 ke darmiyan hon.")
            return

        if not spend(self.selected_bet, "Mines"):
            return

        self.bet = self.selected_bet
        self.mine_count = count
        self.mines = set(random.sample(range(25), count))
        self.revealed = set()
        self.current_multiplier = 1.0
        self.active = True
        self.busy = True
        self.action_button.text = "CASH OUT"
        self.action_button.background_color = GOLD
        self.action_button.color = (0.04, 0.05, 0.07, 1)
        self.info.text = "Choose a safe tile."
        self.build_board()

    def reveal(self, index):
        if not self.active or index in self.revealed:
            return

        self.revealed.add(index)
        button = self.board.children[24 - index]

        if index in self.mines:
            button.text = "💣"
            button.background_color = RED
            self.end_round(False)
            toast("Mine hit! Bet lost.")
            return

        button.text = "💎"
        button.background_color = GREEN
        button.color = (0.02, 0.05, 0.07, 1)

        safe_total = 25 - self.mine_count
        safe_revealed = len(self.revealed)
        self.current_multiplier = round(
            1.0 + (safe_revealed / max(1, safe_total)) * 2.5,
            2,
        )
        self.info.text = (
            f"Safe tile. Current multiplier: "
            f"{self.current_multiplier:.2f}x"
        )

    def end_round(self, won):
        self.active = False
        self.busy = False
        self.action_button.text = "START MINES"
        self.action_button.background_color = BLUE
        self.action_button.color = TEXT

        if not won:
            for index in self.mines:
                button = self.board.children[24 - index]
                button.text = "💣"
                button.background_color = RED

        self.refresh_balance()

    def on_leave(self, *args):
        self.active = False
        self.busy = False


# ============================================================
# MAIN APPLICATION ENGINE
# ============================================================

class PK786DemoApp(App):
    def build(self):
        self.title = APP_NAME

        Window.softinput_mode = "below_target"
        Window.clearcolor = BG
        Window.bind(on_keyboard=self.on_key_press)

        self.manager = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )

        self.manager.add_widget(LoginScreen(name="login"))
        self.manager.add_widget(LobbyScreen(name="lobby"))
        self.manager.add_widget(WalletScreen(name="wallet"))
        self.manager.add_widget(AccountScreen(name="account"))
        self.manager.add_widget(SlotsScreen(name="slots"))
        self.manager.add_widget(SpinScreen(name="spin"))
        self.manager.add_widget(CrashScreen(name="crash"))
        self.manager.add_widget(MinesScreen(name="mines"))

        return self.manager

    def on_key_press(self, window, key, *args):
        # Prevent auto-exit when Android hard back button is pressed (Keycode 27)
        if key == 27:
            if self.manager.current != "lobby" and self.manager.current != "login":
                self.manager.current = "lobby"
                return True
            elif self.manager.current == "lobby":
                return True
        return False


if __name__ == "__main__":
    PK786DemoApp().run()
