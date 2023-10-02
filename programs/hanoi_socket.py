import socket
from threading import Event
from typing import Literal


class grobal_data:
    """関数に引数として渡すことでidを変えずに共有できる"""

    def __init__(self) -> None:
        self.received_data: bytes = None
        self.sending_data: bytes = None
        self.receive_event = Event()
        self.receive_event.clear()
        self.send_event = Event()
        self.send_event.clear()
        self.is_connecting: bool = False
        self.error: Exception = None


class hanoi_socket:
    def __init__(
        self,
        mode: Literal["host", "client"],
        grobal_data: grobal_data,
        ip_address: str = "localhost",
        port_num: int = 55555,
    ) -> None:
        print(mode)
        if mode == "host":
            self.open(ip_address, port_num)
            self.accept(grobal_data)
        else:
            self.connect(grobal_data, ip_address, port_num)
        if grobal_data.is_connecting:
            print("connected.")
        else:
            print("connection rejected.")

    def open(self, host: str, port: int = 55555):
        """サーバーをホスト

        Parameters
        ----------
        host : str
            exp.
            "123.456.7.89"
            "localhost"
        port : int, optional
            by default 55555
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(1)  # 1つの接続要求を待つ

    def accept(self, grobal_data: grobal_data):
        """サーバーへの接続要求を待機し、接続"""
        self.connection, self.address = self.server.accept()  # 要求が来るまでブロック
        del self.server
        grobal_data.is_connecting = True
        print("connected by" + str(self.address))

    def connect(self, grobal_data: grobal_data, host: str, port: int = 55555):
        """クライアントとして対象のサーバーに接続

        Parameters
        ----------
        host : str
            exp.
            "123.456.7.89"
            "localhost"
        port : int, optional
            by default 55555
        """
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connection.connect((host, port))
        except ConnectionRefusedError:
            grobal_data.is_connecting = False
            return
        grobal_data.is_connecting = True
        print(f"connected to {(host,port)}")

    def receive(self, grobal_data: grobal_data):
        """切断されるまで受信したデータを読み、 receive_event を送る

        Parameters
        ----------
        grobal_data : grobal_data
            .is_connecting, .received_data, .received_event, .error を使用する
        """
        try:
            while grobal_data.is_connecting:
                self.received_bytes = self.connection.recv(1024)
                if self.received_bytes != "":
                    grobal_data.received_data = self.received_bytes
                    grobal_data.receive_event.set()
                    print(f"recieved:{grobal_data.received_data}")
        except Exception as e:
            # 自分から切断した場合  : ConnectionAbortedError
            # 相手が切断した場合    : ConnectionResetError
            # 相手がcloseせずに切断した場合 : OSError
            print(f"receive error:{e}")
            grobal_data.error = e
        finally:
            self.close(grobal_data)

    def send(self, grobal_data: grobal_data):
        """.send_event を受けて送信する

        Parameters
        ----------
        grobal_data : grobal_data
            .is_connecting, .send_event, .sending_data を使用する
        """
        while grobal_data.is_connecting:
            grobal_data.send_event.wait()
            if not grobal_data.is_connecting:
                break
            self.connection.send(grobal_data.sending_data)
            print(f"send:{grobal_data.sending_data}")
            grobal_data.sending_data = None
            grobal_data.send_event.clear()

    def receive_byte(self, buf_size: int) -> bytes:
        return self.connection.recv(buf_size)

    def send_byte(self, data: bytes):
        self.connection.send(data)

    def close(self, grobal_data: grobal_data):
        """通信切断

        Parameters
        ----------
        grobal_data : grobal_data
            .is_connecting, .send_event, .receive_event を使用する
        """
        if grobal_data.is_connecting:
            grobal_data.is_connecting = False
            self.connection.close()
            del self.connection

            # whileを抜けさせる
            grobal_data.send_event.set()
            grobal_data.receive_event.set()

            print("close:切断しました")
        else:
            print("close:接続していません")
