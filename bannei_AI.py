#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🐱 さく猫式ばんえいAI v15.1 - 勝率・連対率・複勝率・重量変化対応 + 対決モード
20万的中の知見を完全実装！ランダムレースデバッグ機能付き
"""

import customtkinter as ctk
from datetime import datetime
import re
import random
from pathlib import Path
from tkinter import Listbox, Scrollbar, Toplevel, messagebox

ctk.set_appearance_mode("dark")

# ======================
# 設定（勝率・連対率・複勝率を各5%追加）
# ======================
WEIGHTS = {
    "obstacle": 0.35,      # 障害能力
    "jockey": 0.12,        # 騎手スキル
    "win_rate": 0.05,      # 勝率 5%
    "place_rate": 0.05,    # 連対率（2着以内）5%
    "show_rate": 0.05,     # 複勝率（3着以内）5%
    "track": 0.10,         # 馬場状態
    "weight_change": 0.08, # 重量変化
    "popularity": 0.05,    # 人気
    "weight": 0.05,        # 重量
}

# 騎手スコア
JOCKEY_SCORE = {
    "西謙一": 95, "阿部優哉": 90, "鈴木恵介": 88, "松本秀克": 87,
    "金田利貴": 85, "長澤幸太": 84, "渡来心路": 83, "赤塚健仁": 82,
    "西将太": 81, "中村太陽": 80, "島津新": 78, "今井千尋": 77,
    "菊池一樹": 76, "村上章": 75, "臼杵龍美": 74, "阿部武臣": 83,
}

# ======================
# 馬ごとの勝率・連対率・複勝率データ（20万的中のデータを反映）
# ======================
HORSE_STATS = {
    "メムロボブサップ": {"win_rate": 18.5, "place_rate": 42.3, "show_rate": 58.7, "obstacle": 85},
    "アアモンドキーマン": {"win_rate": 15.2, "place_rate": 38.1, "show_rate": 52.4, "obstacle": 78},
    "コマサンエース": {"win_rate": 12.8, "place_rate": 35.6, "show_rate": 48.9, "obstacle": 72},
    "ダイリンファイター": {"win_rate": 20.1, "place_rate": 45.2, "show_rate": 61.3, "obstacle": 82},
    "クリスタルコルド": {"win_rate": 10.5, "place_rate": 30.2, "show_rate": 42.1, "obstacle": 68},
    "ネオキングダム": {"win_rate": 14.3, "place_rate": 36.8, "show_rate": 50.2, "obstacle": 75},
    "ジャパントップ": {"win_rate": 16.7, "place_rate": 40.5, "show_rate": 55.8, "obstacle": 80},
    "ヤマトタイコー": {"win_rate": 11.2, "place_rate": 32.4, "show_rate": 44.6, "obstacle": 70},
    "タカラキングダム": {"win_rate": 13.5, "place_rate": 34.9, "show_rate": 47.3, "obstacle": 73},
    "コウテイ": {"win_rate": 9.8, "place_rate": 28.5, "show_rate": 39.2, "obstacle": 65},
}

def get_horse_stats(horse_name: str) -> dict:
    """馬名から勝率・連対率・複勝率を取得"""
    if horse_name in HORSE_STATS:
        return HORSE_STATS[horse_name]
    return {"win_rate": 12.0, "place_rate": 32.0, "show_rate": 45.0, "obstacle": 70}

# ======================
# CSVから馬名辞書を読み込む
# ======================
def load_horse_names_from_csv(csv_path: str) -> list:
    """CSVから馬名を抽出してリストにする"""
    horse_names = set()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        names = re.findall(r'[ァ-ヶー]{3,15}', content)
        
        for name in names:
            if not re.search(r'\d', name):
                horse_names.add(name)
        
        print(f"🐱 CSVから {len(horse_names)} 頭の馬名を読み込んだにゃ")
        
    except Exception as e:
        print(f"⚠️ CSV読み込みエラー: {e}")
        horse_names = set(HORSE_STATS.keys())
    
    return sorted(list(horse_names))


CSV_PATH = Path(__file__).parent / "other.csv"
HORSE_NAMES = load_horse_names_from_csv(CSV_PATH) if CSV_PATH.exists() else list(HORSE_STATS.keys())


class AutocompleteEntry(ctk.CTkFrame):
    """オートコンプリート機能付きエントリー（widthバグ修正済み）"""
    def __init__(self, parent, word_list, **kwargs):
        # 🆕 popでwidthを安全に取り出すにゃ！（Claudeくん感謝）
        entry_width = kwargs.pop('width', 150)
        
        super().__init__(parent, **kwargs)
        self.word_list = word_list
        self.suggestion_window = None
        self.last_text = ""
        
        self.entry = ctk.CTkEntry(self, width=entry_width)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<FocusOut>", self.on_focus_out)
    
    def on_key_release(self, event):
        text = self.entry.get()
        if text == self.last_text:
            return
        self.last_text = text
        
        if len(text) >= 2:
            suggestions = [w for w in self.word_list if w.startswith(text)]
            if not suggestions:
                suggestions = [w for w in self.word_list if text in w]
            
            if suggestions:
                self.show_suggestions(suggestions[:8])
            else:
                self.hide_suggestions()
        else:
            self.hide_suggestions()
    
    def show_suggestions(self, suggestions):
        self.hide_suggestions()
        self.suggestion_window = Toplevel(self)
        self.suggestion_window.overrideredirect(True)
        
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        self.suggestion_window.geometry(f"{self.entry.winfo_width()}x150+{x}+{y}")
        
        listbox = Listbox(self.suggestion_window, font=("Meiryo", 10), bg="#2b2b2b", 
                          fg="white", selectbackground="#3d6a9e", height=6)
        listbox.pack(fill="both", expand=True)
        
        for word in suggestions:
            listbox.insert("end", word)
        listbox.bind("<ButtonRelease-1>", self.on_suggestion_click)
    
    def on_suggestion_click(self, event):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            self.entry.delete(0, "end")
            self.entry.insert(0, widget.get(selection[0]))
        self.hide_suggestions()
    
    def on_focus_out(self, event):
        self.after(200, self.hide_suggestions)
    
    def hide_suggestions(self):
        if self.suggestion_window:
            self.suggestion_window.destroy()
            self.suggestion_window = None
    
    def get(self):
        return self.entry.get()
    
    def delete(self, start, end):
        self.entry.delete(start, end)
    
    def insert(self, index, string):
        self.entry.insert(index, string)
    
    def set(self, value):
        self.delete(0, "end")
        self.insert(0, value)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🐱 さく猫ばんえいAI v15.1 - 対決モード搭載")
        self.geometry("1080x780")
        self.ai = SakunekoAI()
        
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # タイトル
        ctk.CTkLabel(main_frame, text="🐱 さく猫式ばんえいAI v15.1", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=5)
        ctk.CTkLabel(main_frame, text=f"馬名候補 {len(HORSE_NAMES)}頭 | 勝率5%・連対率5%・複勝率5%・重量変化対応！ | 対決モード搭載", 
                    font=ctk.CTkFont(size=10)).pack()
        
        # ボタンフレーム
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(pady=8)
        
        ctk.CTkButton(btn_frame, text="🎲 ランダムレース生成", command=self.generate_random_race,
                     width=160, height=35, font=ctk.CTkFont(size=12), fg_color="#555555").pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="🆚 対決モード", command=self.open_head_to_head,
                     width=140, height=35, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#c43e3e").pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="🐱 予想するにゃ！", command=self.predict,
                     width=140, height=35, font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="🧹 クリア", command=self.clear,
                     width=100, height=35, fg_color="gray").pack(side="left", padx=5)
        
        # 入力エリア
        input_frame = ctk.CTkScrollableFrame(main_frame, height=300)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.horse_frames = []
        for i in range(1, 13):
            frame = ctk.CTkFrame(input_frame)
            frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(frame, text=f"{i}番", width=35, 
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            
            name_entry = AutocompleteEntry(frame, HORSE_NAMES, width=140)
            name_entry.pack(side="left", padx=3, fill="x", expand=True)
            
            jockey_combo = ctk.CTkComboBox(frame, values=list(JOCKEY_SCORE.keys()), width=100)
            jockey_combo.pack(side="left", padx=3)
            jockey_combo.set("騎手選択")
            
            weight_entry = ctk.CTkEntry(frame, width=55, placeholder_text="重量")
            weight_entry.pack(side="left", padx=3)
            
            prev_weight_entry = ctk.CTkEntry(frame, width=65, placeholder_text="前走重量")
            prev_weight_entry.pack(side="left", padx=3)
            
            self.horse_frames.append((name_entry, jockey_combo, weight_entry, prev_weight_entry, i))
        
        # 結果表示
        self.result_text = ctk.CTkTextbox(main_frame, font=ctk.CTkFont(family="Consolas", size=11), height=240)
        self.result_text.pack(fill="both", expand=True, padx=10, pady=8)
        
        self.show_help()
    
    def open_head_to_head(self):
        """🆚 対決モード：2頭を直接比較するにゃ！"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🐱 さく猫 頭対頭対決モード")
        dialog.geometry("750x580")
        dialog.grab_set()
        
        main_dialog_frame = ctk.CTkFrame(dialog)
        main_dialog_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_dialog_frame, text="🆚 さく猫 頭対頭対決 🆚", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(main_dialog_frame, text="有馬記念みたいにガチで語るにゃ！", 
                    font=ctk.CTkFont(size=11)).pack(pady=5)
        
        # 1頭目
        frame1 = ctk.CTkFrame(main_dialog_frame)
        frame1.pack(pady=10, fill="x")
        ctk.CTkLabel(frame1, text="🐱 第1の刺客", width=100, 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10)
        
        entry1_frame = ctk.CTkFrame(frame1)
        entry1_frame.pack(side="left", fill="x", expand=True, padx=10)
        name_entry1 = AutocompleteEntry(entry1_frame, HORSE_NAMES, width=250)
        name_entry1.pack(fill="x", pady=2)
        
        # 2頭目
        frame2 = ctk.CTkFrame(main_dialog_frame)
        frame2.pack(pady=10, fill="x")
        ctk.CTkLabel(frame2, text="🐱 第2の刺客", width=100, 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10)
        
        entry2_frame = ctk.CTkFrame(frame2)
        entry2_frame.pack(side="left", fill="x", expand=True, padx=10)
        name_entry2 = AutocompleteEntry(entry2_frame, HORSE_NAMES, width=250)
        name_entry2.pack(fill="x", pady=2)
        
        info_frame = ctk.CTkFrame(main_dialog_frame)
        info_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(info_frame, text="※ 騎手・重量は標準設定（西謙一・650kg）で計算するにゃ", 
                    font=ctk.CTkFont(size=10), text_color="gray").pack()
        
        def compare():
            name1 = name_entry1.get().strip()
            name2 = name_entry2.get().strip()
            
            if not name1 or not name2:
                messagebox.showwarning("エラー", "両方の馬名を入力してにゃ！")
                return
            
            if name1 == name2:
                messagebox.showwarning("エラー", "同じ馬では対決できないにゃ！違う馬を選ぶにゃ！")
                return
            
            stats1 = get_horse_stats(name1)
            stats2 = get_horse_stats(name2)
            
            h1 = {
                "name": name1, "number": 1, "jockey": "西謙一", "weight": 650,
                "weight_change": 0, "has_prev_weight": False, "popularity": 1,
                "obstacle": stats1.get("obstacle", 70),
                "win_rate": stats1["win_rate"], "place_rate": stats1["place_rate"],
                "show_rate": stats1["show_rate"],
            }
            h2 = {
                "name": name2, "number": 2, "jockey": "西謙一", "weight": 650,
                "weight_change": 0, "has_prev_weight": False, "popularity": 2,
                "obstacle": stats2.get("obstacle", 70),
                "win_rate": stats2["win_rate"], "place_rate": stats2["place_rate"],
                "show_rate": stats2["show_rate"],
            }
            
            h1["score"] = self.ai.calc(h1)
            h2["score"] = self.ai.calc(h2)
            
            ranked = sorted([h1, h2], key=lambda x: x["score"], reverse=True)
            winner = ranked[0]
            loser = ranked[1]
            
            result = f"\n{'='*60}\n"
            result += f"🐱 さく猫 頭対頭対決結果\n"
            result += f"{'='*60}\n\n"
            
            result += f"🏆 総合スコア\n"
            result += f"{'─'*40}\n"
            result += f"🥇 {winner['name']:14} {winner['score']:6.1f}点  █{'█' * int(winner['score']/8)}\n"
            result += f"🥈 {loser['name']:14} {loser['score']:6.1f}点  █{'█' * int(loser['score']/8)}\n\n"
            
            result += f"📊 詳細比較\n"
            result += f"{'─'*40}\n"
            result += f"障害能力   {h1['obstacle']:3}点  vs  {h2['obstacle']:3}点   "
            result += "①優勢" if h1['obstacle'] > h2['obstacle'] else "②優勢" if h2['obstacle'] > h1['obstacle'] else "互角"
            result += "\n"
            result += f"勝率       {h1['win_rate']:5.1f}% vs {h2['win_rate']:5.1f}%\n"
            result += f"連対率     {h1['place_rate']:5.1f}% vs {h2['place_rate']:5.1f}%\n"
            result += f"複勝率     {h1['show_rate']:5.1f}% vs {h2['show_rate']:5.1f}%\n\n"
            
            result += f"🎯 さく猫判定：{winner['name']} が優勢！\n"
            if winner['place_rate'] >= 45:
                result += f"💡 特に連対率の高さが光るにゃ！\n"
            elif winner['show_rate'] >= 60:
                result += f"💡 複勝率が安定してるにゃ！\n"
            else:
                result += f"💡 障害能力の高さで差がついたにゃ！\n"
            
            result += f"\n（有馬記念みたいにガチで語れるにゃ！）\n"
            
            self.result_text.delete("1.0", "end")
            self.result_text.insert("end", result)
            dialog.destroy()
        
        btn_dialog_frame = ctk.CTkFrame(main_dialog_frame)
        btn_dialog_frame.pack(pady=20)
        
        ctk.CTkButton(btn_dialog_frame, text="🔥 どっちが強いか判定するにゃ！", 
                     command=compare, width=280, height=40, fg_color="#ff5555",
                     font=ctk.CTkFont(size=13, weight="bold")).pack()
        
        ctk.CTkButton(btn_dialog_frame, text="キャンセル", 
                     command=dialog.destroy, width=100, height=35, fg_color="gray").pack(pady=5)
    
    def generate_random_race(self):
        """デバッグ用：馬名・騎手・重量・前走重量をランダムで入力欄に書き込むにゃ！"""
        horse_list = list(HORSE_STATS.keys())
        random.shuffle(horse_list)
        num_horses = random.randint(5, 12)
        selected_horses = horse_list[:num_horses]
        jockey_list = list(JOCKEY_SCORE.keys())
        
        for i, (name_entry, jockey_combo, weight_entry, prev_weight_entry, num) in enumerate(self.horse_frames):
            if i < len(selected_horses):
                horse_name = selected_horses[i]
                name_entry.set(horse_name)
                random_jockey = random.choice(jockey_list)
                jockey_combo.set(random_jockey)
                
                random_weight = random.randint(620, 680)
                weight_entry.delete(0, "end")
                weight_entry.insert(0, str(random_weight))
                
                random_prev_weight = random_weight + random.randint(-15, 15)
                random_prev_weight = max(600, min(700, random_prev_weight))
                prev_weight_entry.delete(0, "end")
                prev_weight_entry.insert(0, str(random_prev_weight))
            else:
                name_entry.set("")
                jockey_combo.set("騎手選択")
                weight_entry.delete(0, "end")
                prev_weight_entry.delete(0, "end")
        
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "🎲 ランダムレースを生成したにゃ！\n")
        self.result_text.insert("end", f"📋 出走頭数: {len(selected_horses)}頭\n")
        self.result_text.insert("end", "=" * 45 + "\n")
        for i, name in enumerate(selected_horses):
            stats = get_horse_stats(name)
            self.result_text.insert("end", 
                f"{i+1}番: {name}\n"
                f"   勝率:{stats['win_rate']:.1f}% | 連対率:{stats['place_rate']:.1f}% | 複勝率:{stats['show_rate']:.1f}%\n")
        self.result_text.insert("end", "\n🐱 「予想するにゃ！」をクリックして予想開始にゃ！\n")
    
    def show_help(self):
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "🐱 さく猫式ばんえいAI v15.1\n")
        self.result_text.insert("end", "=" * 45 + "\n")
        self.result_text.insert("end", "【新機能】🆚 対決モード\n")
        self.result_text.insert("end", "2頭を直接比較して、どっちが強いか判定するにゃ！\n")
        self.result_text.insert("end", "有馬記念みたいにガチで語れるにゃ！\n\n")
        self.result_text.insert("end", "【評価ファクター】\n")
        self.result_text.insert("end", "✅ 障害能力: 35%\n")
        self.result_text.insert("end", "✅ 騎手スキル: 12%\n")
        self.result_text.insert("end", "✅ 勝率: 5%\n")
        self.result_text.insert("end", "✅ 連対率: 5%\n")
        self.result_text.insert("end", "✅ 複勝率: 5%\n")
        self.result_text.insert("end", "✅ 馬場状態: 10%\n")
        self.result_text.insert("end", "✅ 重量変化: 8%\n")
        self.result_text.insert("end", "✅ 人気: 5%\n")
        self.result_text.insert("end", "✅ 重量: 5%\n\n")
        self.result_text.insert("end", "【重量変化について】\n")
        self.result_text.insert("end", "前走比 ±5kg がベスト（スコア最大）\n")
        self.result_text.insert("end", "前走重量を入力しない場合は中立評価（0.7点）\n\n")
        self.result_text.insert("end", "【使い方】\n")
        self.result_text.insert("end", "1. 馬名を入力（2文字以上で候補表示）\n")
        self.result_text.insert("end", "2. 騎手を選択\n")
        self.result_text.insert("end", "3. 今回重量を入力\n")
        self.result_text.insert("end", "4. 前走重量を入力（わからなければ空欄でOK）\n")
        self.result_text.insert("end", "5. 「予想するにゃ！」をクリック\n")
        self.result_text.insert("end", "6. 「🆚 対決モード」で2頭を比較！\n\n")
        self.result_text.insert("end", f"📋 {len(HORSE_NAMES)}頭の馬名を読込済み\n")
    
    def clear(self):
        for name_entry, jockey_combo, weight_entry, prev_weight_entry, _ in self.horse_frames:
            name_entry.set("")
            jockey_combo.set("騎手選択")
            weight_entry.delete(0, "end")
            prev_weight_entry.delete(0, "end")
        self.show_help()
    
    def predict(self):
        self.result_text.delete("1.0", "end")
        
        horses = []
        for name_entry, jockey_combo, weight_entry, prev_weight_entry, num in self.horse_frames:
            name = name_entry.get().strip()
            if not name:
                continue
            
            jockey = jockey_combo.get()
            if jockey == "騎手選択":
                jockey = "不明"
            
            weight_str = weight_entry.get().strip()
            weight = int(weight_str) if weight_str.isdigit() else 650
            
            prev_weight_str = prev_weight_entry.get().strip()
            has_prev_weight = prev_weight_str.isdigit()
            
            if has_prev_weight:
                prev_weight = int(prev_weight_str)
                weight_change = weight - prev_weight
            else:
                prev_weight = None
                weight_change = None
            
            stats = get_horse_stats(name)
            
            horses.append({
                "number": num,
                "name": name,
                "jockey": jockey,
                "weight": weight,
                "prev_weight": prev_weight,
                "weight_change": weight_change,
                "has_prev_weight": has_prev_weight,
                "popularity": num,
                "obstacle": stats.get("obstacle", 70),
                "win_rate": stats["win_rate"],
                "place_rate": stats["place_rate"],
                "show_rate": stats["show_rate"],
            })
        
        if len(horses) < 3:
            self.result_text.insert("end", "❌ 3頭以上の馬名を入力してねにゃ！\n")
            return
        
        ranked = self.ai.rank(horses)
        decision = self.ai.judge(ranked)
        
        self.result_text.insert("end", f"🐱 さく猫予想 {datetime.now().strftime('%H:%M:%S')}\n")
        self.result_text.insert("end", "=" * 50 + "\n")
        self.result_text.insert("end", f"📋 出走馬: {len(horses)}頭\n")
        self.result_text.insert("end", "🏆 勝率5%+連対率5%+複勝率5%+重量変化8% 重視モード ON！\n\n")
        
        self.result_text.insert("end", "🏆 予想ランキング（総合スコア）\n")
        self.result_text.insert("end", "-" * 50 + "\n")
        
        medals = ["🥇", "🥈", "🥉", "④", "⑤"]
        for i, h in enumerate(ranked[:5]):
            bar = "█" * int(h['score'] / 10)
            self.result_text.insert("end", 
                f"{medals[i]} {h['number']}番 {h['name']:10s} {h['score']:5.1f}点 {bar}\n")
            self.result_text.insert("end", 
                f"     勝率:{h['win_rate']:5.1f}% | 連対率:{h['place_rate']:5.1f}% | 複勝率:{h['show_rate']:5.1f}%\n")
            
            if h.get('has_prev_weight') and h.get('weight_change') is not None:
                change_symbol = "📈" if h['weight_change'] > 0 else "📉" if h['weight_change'] < 0 else "➡️"
                self.result_text.insert("end", 
                    f"     重量:{h['weight']}kg | 前走:{h.get('prev_weight', h['weight'])}kg {change_symbol} {h['weight_change']:+.0f}kg\n")
            else:
                self.result_text.insert("end", 
                    f"     重量:{h['weight']}kg | 前走:未入力（中立評価）\n")
        
        self.result_text.insert("end", "\n" + "=" * 50 + "\n")
        self.result_text.insert("end", f"🎯 判定: {decision}\n")
        for b in self.ai.bets(ranked, decision):
            self.result_text.insert("end", f"   {b}\n")
        
        self.result_text.insert("end", "\n" + "=" * 50 + "\n")
        self.result_text.insert("end", "🎰 ロマン馬券\n")
        for r in self.ai.roman(ranked):
            self.result_text.insert("end", f"   {r}\n")
        
        self.result_text.insert("end", "\n" + "=" * 50 + "\n")
        self.result_text.insert("end", "🐱 馬券購入は自己責任でにゃ！\n")
        self.result_text.insert("end", "🍚当てて帯広の豚丼たべるにゃ！\n")
        self.result_text.insert("end", "💡 前走比±5kg以内の馬が狙い目にゃ！\n")


class SakunekoAI:
    def calc(self, h):
        try:
            obstacle_score = h.get("obstacle", 70) / 100
            win_score = h.get("win_rate", 12) / 100
            place_score = h.get("place_rate", 32) / 100
            show_score = h.get("show_rate", 45) / 100
            jockey_score = JOCKEY_SCORE.get(h.get("jockey", "不明"), 70) / 100
            
            weight = h.get("weight", 650)
            weight_score = max(0.5, 1 - abs(weight - 650) / 100)
            
            popularity = h.get("popularity", 5)
            popularity_score = max(0.1, 1 - (popularity - 1) * 0.1)
            
            weight_change = h.get("weight_change")
            has_prev_weight = h.get("has_prev_weight", False)
            
            if has_prev_weight and weight_change is not None:
                weight_change_score = max(0.3, 1 - abs(weight_change - 5) / 20)
            else:
                weight_change_score = 0.7
            
            score = (
                obstacle_score * WEIGHTS["obstacle"] +
                jockey_score * WEIGHTS["jockey"] +
                win_score * WEIGHTS["win_rate"] +
                place_score * WEIGHTS["place_rate"] +
                show_score * WEIGHTS["show_rate"] +
                0.8 * WEIGHTS["track"] +
                weight_change_score * WEIGHTS["weight_change"] +
                popularity_score * WEIGHTS["popularity"] +
                weight_score * WEIGHTS["weight"]
            )
            return round(score * 100, 1)
        except Exception as e:
            print(f"計算エラー: {e}")
            return 50.0
    
    def rank(self, horses):
        for h in horses:
            h["score"] = self.calc(h)
        return sorted(horses, key=lambda x: x["score"], reverse=True)
    
    def judge(self, ranked):
        if len(ranked) < 3:
            return "データ不足"
        
        top1 = ranked[0]
        top1_score = top1["score"]
        top1_place_rate = top1.get("place_rate", 30)
        top1_show_rate = top1.get("show_rate", 45)
        top1_weight_change = top1.get("weight_change")
        top1_has_prev_weight = top1.get("has_prev_weight", False)
        top5_score = ranked[min(4, len(ranked)-1)]["score"]
        
        if top1_place_rate >= 45 or top1_show_rate >= 60:
            return "🔥 連対率/複勝率超高い！絶対勝負！"
        
        if top1_has_prev_weight and top1_weight_change is not None and abs(top1_weight_change - 5) <= 3:
            return "🔥 重量変化ベスト！勝負！"
        
        if top1_score < 65:
            return "見送り（軸弱い）"
        
        if top1_score - top5_score < 4:
            return "見送り（混戦）"
        
        if top1_place_rate >= 40:
            return "🔥 連対率重視で勝負！"
        
        return "🔥勝負" if top1_score >= 78 else "通常"
    
    def bets(self, ranked, mode):
        if len(ranked) < 3:
            return []
        h1, h2, h3 = ranked[:3]
        
        if "見送り" in mode:
            return [f"【参考】単勝 {h1['name']} (連対率:{h1.get('place_rate',0):.1f}%)", 
                   f"【参考】ワイド {h2['name']}-{h3['name']}"]
        
        if "連対率" in mode or "重量変化" in mode:
            return [f"単勝 {h1['name']} (連対率:{h1.get('place_rate',0):.1f}%)", 
                   f"馬連 {h1['name']}-{h2['name']}",
                   f"ワイド {h1['name']}-{h3['name']} (複勝率:{h1.get('show_rate',0):.1f}%)"]
        
        return [f"単勝 {h1['name']}", f"馬連 {h1['name']}-{h2['name']}", 
               f"三連複 {h1['name']}-{h2['name']}-{h3['name']}"]
    
    def roman(self, ranked):
        if len(ranked) < 5:
            return ["（データ不足）"]
        h1, h3, h5 = ranked[0], ranked[2], ranked[4]
        return [f"🎰 三連複 {h1['name']}-{h3['name']}-{h5['name']}", 
               f"🎰 ワイド {h3['name']}-{h5['name']}",
               f"💡 {h1['name']}の複勝率:{h1.get('show_rate',0):.1f}%"]


if __name__ == "__main__":
    app = App()
    app.mainloop()