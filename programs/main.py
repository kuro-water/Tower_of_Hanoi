import tkinter as tk
from tkinter import ttk, font
from threading import Thread
from typing import Literal
from play_hanoi import hanoi
from hanoi_socket import grobal_data
from hanoi_socket import hanoi_socket

# import IO_server

# about 16:9
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 562

DISK_MAX = 9
DISK_MIN = 2


class gui(tk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        print("init GUI")
        self.disk_total = tk.IntVar(value=5)
        self.ip_address = tk.StringVar(value="localhost")
        self.port_num = tk.IntVar(value=55555)
        self.auto_speed = tk.DoubleVar(value=0.05)
        self.grobal_data = grobal_data()
        self.is_multi_play = False
        self.hanoi: hanoi
        self.thread_connect: Thread
        self.thread_send: Thread
        self.thread_receive: Thread

        # 画面サイズ取る
        width = root.winfo_screenwidth()
        hight = root.winfo_screenheight()

        self.main_window: tk.Tk = root
        self.main_window.title("Tower of Hanoi")
        # self.main_window.protocol("WM_DELETE_WINDOW", self.close)
        self.main_window.geometry(  # 画面の中心に置く
            str(WINDOW_WIDTH)
            + "x"
            + str(WINDOW_HEIGHT)
            + "+"
            + str(int((width - WINDOW_WIDTH) / 2))
            + "+"
            + str(int((hight - WINDOW_HEIGHT) / 2))
        )
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_columnconfigure(0, weight=1)

        self.frame_main_menu = tk.Frame(self.main_window)
        self.frame_multi_menu = tk.Frame(self.main_window)
        self.frame_connecting = tk.Frame(self.main_window)
        self.frame_hanoi = tk.Frame(self.main_window)

        self.frame_main_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_multi_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_connecting.grid(row=0, column=0, sticky="nsew")
        self.frame_hanoi.grid(row=0, column=0, sticky="nsew")

        self.frame_main_menu.tkraise()

        # ---------- main menu ----------

        self.button_solo_play = ttk.Button(
            self.frame_main_menu,
            text="ソロプレイ",
            command=lambda: self.change_frame(self.frame_hanoi, "solo"),
        )
        self.button_multi_play = ttk.Button(
            self.frame_main_menu,
            text="マルチプレイ",
            command=lambda: self.change_frame(self.frame_multi_menu, "change"),
        )
        self.button_auto_play = ttk.Button(
            self.frame_main_menu,
            text="オートプレイ",
            command=lambda: self.change_frame(self.frame_hanoi, "auto"),
        )
        self.label_disk_total = ttk.Label(
            self.frame_main_menu, text=f"枚数({DISK_MIN}~{DISK_MAX})："
        )
        self.entry_disk_total = ttk.Entry(
            self.frame_main_menu, textvariable=self.disk_total
        )

        self.button_solo_play.place(anchor="center", relx=0.5, rely=0.1, width=130)
        self.button_multi_play.place(anchor="center", relx=0.5, rely=0.2, width=130)
        self.button_auto_play.place(anchor="center", relx=0.5, rely=0.3, width=130)
        self.label_disk_total.place(anchor="e", relx=0.5, rely=0.4, width=65)
        self.entry_disk_total.place(anchor="w", relx=0.5, rely=0.4, width=65)

        # ---------- multi play menu ----------

        self.button_back = ttk.Button(
            self.frame_multi_menu,
            text="戻る",
            command=lambda: self.change_frame(self.frame_main_menu, "change"),
        )
        self.label_ip_address = ttk.Label(self.frame_multi_menu, text="IPアドレス：")
        self.entry_ip_address = ttk.Entry(
            self.frame_multi_menu, textvariable=self.ip_address
        )
        self.label_port_num = ttk.Label(self.frame_multi_menu, text="ポート番号：")
        self.entry_port_num = ttk.Entry(
            self.frame_multi_menu, textvariable=self.port_num
        )
        self.button_host_server = ttk.Button(
            self.frame_multi_menu,
            text="サーバーをホストする",
            command=lambda: self.start_multi_play("host"),
        )
        self.button_join_server = ttk.Button(
            self.frame_multi_menu,
            text="サーバーに接続する",
            command=lambda: self.start_multi_play("client"),
        )

        self.button_back.pack(pady=5, padx=10, side=tk.TOP, anchor="w")
        self.label_ip_address.place(anchor="e", relx=0.5, rely=0.1, width=60)
        self.entry_ip_address.place(anchor="w", relx=0.5, rely=0.1, width=120)
        self.label_port_num.place(anchor="e", relx=0.5, rely=0.2, width=60)
        self.entry_port_num.place(anchor="w", relx=0.5, rely=0.2, width=120)
        self.button_host_server.place(anchor="center", relx=0.5, rely=0.3, width=130)
        self.button_join_server.place(anchor="center", relx=0.5, rely=0.4, width=130)

        # ---------- connecting ----------
        self.label_connecting = ttk.Label(
            self.frame_connecting,
            text="接続中..",
            font=(font.nametofont("TkDefaultFont"), "20", "bold"),
        )

        self.label_connecting.pack()

        # ---------- hanoi menu ----------
        self.button_back_ = ttk.Button(
            self.frame_hanoi, text="戻る", command=lambda: self.del_hanoi()
        )

        self.button_back_.pack(pady=5, padx=10, side=tk.TOP, anchor="w")

        print("end init GUI")
        # ---------- end init ----------

    def change_frame(
        self,
        to_frame: tk.Frame,
        mode: Literal["change", "solo", "multi", "auto"],
    ):
        """
        ----------
        to_frame : tk.Frame
            交代先のフレーム
        mode : Literal["change", "solo", "multi", "auto"]
            "change"    : フレーム変更のみ
            "solo"      : ソロプレイ起動
            "multi"     : マルチプレイ起動
            "auto"      : オートプレイ起動
        """

        if mode == "solo":
            self.hanoi = hanoi(self.frame_hanoi, False, self.disk_total)
        elif mode == "multi":
            self.hanoi = hanoi(
                self.frame_hanoi, False, self.disk_total, True, self.grobal_data
            )
        elif mode == "auto":
            self.hanoi = hanoi(self.frame_hanoi, True, self.disk_total)

        to_frame.tkraise()
        print("frame changed.")

    def del_hanoi(self):
        """ハノイの塔リセット"""
        if self.grobal_data.is_connecting:
            self.connection.close(self.grobal_data)
            self.grobal_data.__init__()
            self.thread_send.join()
            self.thread_receive.join()
            del self.connection
            del self.grobal_data
        self.hanoi.canvas.destroy()
        del self.hanoi
        print("end hanoi")
        self.change_frame(self.frame_main_menu, "change")

    def start_multi_play(self, mode: Literal["host", "client"]):
        """通信待機中メインスレッドを動かす"""
        self.change_frame(self.frame_connecting, "change")
        self.thread_connect = Thread(target=self.connect, args=[mode], daemon=True)
        self.thread_connect.start()

    def connect(self, mode: Literal["host", "client"]):
        """通信を開始"""
        self.grobal_data = grobal_data()

        self.connection = hanoi_socket(
            mode, self.grobal_data, self.ip_address.get(), self.port_num.get()
        )
        if not self.grobal_data.is_connecting:
            del self.grobal_data
            self.change_frame(self.frame_main_menu, "change")
            return

        # disk_totalをホストに合わせる
        if mode == "host":
            self.connection.send_byte(self.disk_total.get().to_bytes())
        else:
            self.disk_total.set(int.from_bytes(self.connection.receive_byte(1024)))

        self.thread_send = Thread(
            target=self.connection.send, args=[self.grobal_data], daemon=True
        )
        self.thread_receive = Thread(
            target=self.connection.receive,
            args=[self.grobal_data],
            daemon=True,
        )

        self.thread_send.start()
        self.thread_receive.start()

        self.change_frame(self.frame_hanoi, "multi")


if __name__ == "__main__":
    hanoi_gui = gui(tk.Tk())
    hanoi_gui.main_window.mainloop()
