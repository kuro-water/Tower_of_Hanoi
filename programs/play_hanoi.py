import tkinter as tk
from tkinter import ttk
from functools import partial
from threading import Thread
from typing import Literal
import json
import time
from hanoi_socket import grobal_data

DISK_COLORS = [
    "#FF0000",
    "#FF7F00",
    "#FFFF00",
    "#00FF00",
    "#0000FF",
    "#4B0082",
    "#8B00FF",
    "#FF00FF",
    "#00FFFF",
]

DISK_MAX = 9
DISK_MIN = 2

HALF_ROD_WIDTH = 10
Y_TOP = 100  # ロッドの上端のy座標
Y_BOT = 350
ROD_HEIGHT = 65  # Y_TOPからディスクまでの高さ
DISK_STEP_WIDTH = 13  # ディスク一段の横幅の差
DISK_HEIGHT = 20

POS_X = [200, 500, 800]  # left, mid, right
POS_Y = []
for i in range(DISK_MAX):
    POS_Y.append(Y_BOT - DISK_HEIGHT - 21 * i)


class hanoi:
    def __init__(
        self,
        frame: tk.Frame,
        is_auto_play: bool,
        disk_total: tk.IntVar,
        is_multi_play: bool = False,
        grobal_data: grobal_data = None,
    ) -> None:
        """
        Parameters
        ----------
        frame : tk.Frame
            描画するフレーム
        is_auto_play : bool
            True  : auto play
            False : nomal play
        disk_total : tk.IntVar
            使用するディスクの枚数
        is_multi_play : bool, optional
            True  : multi play
            False : solo play
            default = None
        grobal_data : grobal_data, optional
            default = None
        """
        print("init hanoi")
        self.frame: tk.Frame = frame
        self.is_auto_play = is_auto_play
        self.disk_total = disk_total
        self.is_multi_play = is_multi_play

        self.canvas = tk.Canvas(self.frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.rod: list = []
        self.disk: list = []
        self.collider: list = []
        self.disk_pos: list = [[], [], []]  # left,mid,right
        self.move_from: int = 0
        self.click_flag: bool = False

        # 正規化
        if self.disk_total.get() < DISK_MIN:
            self.disk_total.set(DISK_MIN)
        elif self.disk_total.get() > DISK_MAX:
            self.disk_total.set(DISK_MAX)

        # ロッド設置
        for i in range(3):
            self.rod.append(
                self.canvas.create_rectangle(
                    POS_X[i] - HALF_ROD_WIDTH,
                    Y_TOP,
                    POS_X[i] + HALF_ROD_WIDTH,
                    Y_TOP + ROD_HEIGHT + DISK_HEIGHT * self.disk_total.get(),
                    fill="black",
                )
            )

        # ディスク設置
        for i in range(self.disk_total.get()):
            self.disk.append(
                self.canvas.create_rectangle(
                    POS_X[0]
                    - HALF_ROD_WIDTH
                    + DISK_STEP_WIDTH * (i - self.disk_total.get()),
                    POS_Y[i + DISK_MAX - self.disk_total.get()],
                    POS_X[0]
                    + HALF_ROD_WIDTH
                    - DISK_STEP_WIDTH * (i - self.disk_total.get()),
                    POS_Y[i + DISK_MAX - self.disk_total.get()] + DISK_HEIGHT,
                    fill=DISK_COLORS[i],
                    outline=DISK_COLORS[i],
                )
            )

            # 初期配置は左
            self.disk_pos[0].append(i)

        # 当たり判定設置
        for i in range(3):
            self.collider.append(
                self.canvas.create_rectangle(
                    # +1:少し余裕をもたせるため
                    POS_X[i] - HALF_ROD_WIDTH - DISK_STEP_WIDTH * (DISK_MAX + 1),
                    Y_TOP - DISK_HEIGHT,
                    POS_X[i] + HALF_ROD_WIDTH + DISK_STEP_WIDTH * (DISK_MAX + 1),
                    Y_TOP + ROD_HEIGHT + DISK_HEIGHT * (self.disk_total.get() + 1),
                    fill="",
                    outline="",
                )
            )
            self.canvas.tag_bind(
                self.collider[i],
                "<ButtonPress-1>",
                partial(self.click_collider, i, grobal_data),
            )

        if self.is_auto_play:
            # sloveアルゴリズムを別スレッドで開始
            print("opening auto play thread")
            self.auto_play_thread = Thread(
                target=self.slove, args=(self.disk_total.get(), 0, 2, 1), daemon=True
            )
            self.auto_play_thread.start()

        if self.is_multi_play:
            # 同期を別スレッドで開始
            print("opening multi play thread")
            self.multi_play_thread = Thread(
                target=self.sync, args=[grobal_data], daemon=True
            )
            self.multi_play_thread.start()

        print("end init hanoi")

    def sync(self, grobal_data: grobal_data):
        """.recieved_dataを読み取り、self.drawを呼び出す

        Parameters
        ----------
        grobal_data : grobal_data
            .is_connecting, .received_data. .received_event を使用する
        """
        while grobal_data.is_connecting:
            grobal_data.receive_event.wait()
            if not grobal_data.is_connecting:
                break

            self.disk_pos = json.loads(grobal_data.received_data.decode("utf-8"))
            self.draw()

            grobal_data.received_data = None
            self.canvas.itemconfig(self.collider[self.move_from], outline="")
            self.click_flag = False
            grobal_data.receive_event.clear()

    def click_collider(self, place: int, grobal_data: grobal_data, event=None):
        """移動の管理

        Parameters
        ----------
        place : int
            クリックされたコライダーのインデックス
        grobal_data : grobal_data
            .sending_data, send_event を使用する
        event : _type_, optional
            クリックイベントが飛んでくるが使わない
        """
        if not self.click_flag:
            # 移動元指定
            if len(self.disk_pos[place]) != 0:
                # そこにディスクがあるなら
                print(f"from:{place}")
                self.move_from = place
                self.canvas.itemconfig(self.collider[place], outline="red")
                self.click_flag = True
        else:
            # 移動先指定
            try:
                if self.disk_pos[self.move_from][-1] < self.disk_pos[place][-1]:
                    # 置けない
                    print("cannot move!")
                else:
                    raise IndexError
            # 移動先にディスクがないとIndexErrorとなる
            except IndexError:
                # 置ける場合
                print(f"to:{place}")
                self.disk_pos[place].append(self.disk_pos[self.move_from].pop())
                if self.is_multi_play:
                    grobal_data.sending_data = json.dumps(self.disk_pos).encode("utf-8")
                    grobal_data.send_event.set()
                self.draw()

            self.canvas.itemconfig(self.collider[self.move_from], outline="")
            self.click_flag = False

    def draw(self):
        """リストの配置通り描画"""
        for place in range(3):
            for i, disk_idx in enumerate((self.disk_pos[place])):
                self.canvas.moveto(
                    # movetoはなぜか1pixelズレる
                    self.disk[disk_idx],
                    POS_X[place]
                    - HALF_ROD_WIDTH
                    + DISK_STEP_WIDTH * (disk_idx - self.disk_total.get())
                    - 1,
                    POS_Y[i + DISK_MAX - self.disk_total.get()] - 1,
                )

    def slove(self, n, a, c, b):
        """再帰で解く"""
        try:
            if n > 0:
                self.slove(n - 1, a, b, c)

                time.sleep(0.05)
                self.disk_pos[c].append(self.disk_pos[a].pop())
                print(f"{a} to {c}")
                self.draw()

                self.slove(n - 1, b, c, a)
        except tk.TclError:
            # draw()内のmovetoによるエラー 中断対策
            print("auto play has ended abnormally")
        except IndexError:
            # 人間が動かしてしまってディスクが無い場合
            print("it was moved.")
