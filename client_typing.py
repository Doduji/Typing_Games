import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import simpledialog
import time
import re
import socket
import threading

server_host = 'localhost'  # 서버 주소
server_port = 55555  # 서버 포트
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_host, server_port))

ranking_result = [] #서버로부터 받은 타자 연습 결과를 저장할 리스트

class TypingGame:
    def __init__(self, root):
        self.root = root
        self.root.title('Typing Game')

        self.sentences = [
            "",
            "호랑이 그리려다 고양이 그린다",  # 주어진 문장들
            "사촌이 땅을 사면 배가 아프다",
            "숲에서는 꿩을 길들이지 못하며 못에서는 게를 기르지 못한다",
            "나는 내가 더 노력할수록 운이 더 좋아지는 걸 발견했다",
            "기운과 끈기는 모든 것을 이겨낸다",
            "모든 스트라이크는 나의 다음 홈런을 더욱 가까이 오게 한다",
            "천재는 노력하는 자를 이길 수 없고 노력하는 자는 즐기는 자를 결코 이길 수 없다"
        ]

        # 쓰레드 생성 및 실행
        receive_thread = threading.Thread(target=self.receive_message)
        receive_thread.start()

        self.current_sentence_index = 0
        self.current_sentence = ""  # 현재 문장

        self.start_time = 0
        self.total_time = 0
        self.total_chars = 0  # 전체 입력 글자 수
        self.correct_chars = 0  # 정확하게 입력한 글자 수

        self.hangul_count = 0
        self.space_count = 0

        # 문장 표시 라벨
        self.sentence_label = tk.Label(root, text="", font=('Arial', 16), padx=10, pady=10)
        self.sentence_label.pack()

        # 사용자 입력 엔트리
        self.input_entry = tk.Entry(root, font=('Arial', 16), width=40)
        self.input_entry.pack(pady=10)
        self.input_entry.focus_set()
        self.input_entry.bind("<Return>", self.check_input)

        # 결과 표시 라벨
        self.result_label = tk.Label(root, text="", font=('Arial', 12), pady=10)
        self.result_label.pack()

        self.result_window = None  # 결과 창

        # 입력 기록 프레임
        self.input_history_frame = tk.Frame(root)
        self.input_history_frame.pack()

        self.input_history_labels = []  # 사용자 입력 기록을 저장할 라벨 리스트
        self.max_input_history = 100  # 최대 입력 기록 개수 설정
    
        self.start_game()

    def start_game(self):
        self.start_time = time.time()  # 게임 시작 시간 기록
        self.next_sentence()

    def next_sentence(self):
        self.input_entry.delete(0, tk.END)  # 입력창 비우기

        if self.current_sentence_index >= len(self.sentences):  # 마지막 문장을 쳤을 경우
            self.display_result()
            self.input_entry.config(state='disabled')  # 입력 비활성화
            return

        self.current_sentence = self.sentences[self.current_sentence_index]  # 다음 문장 불러오기
        self.sentence_label.config(text=self.current_sentence)

        self.current_sentence_index += 1

    def check_input(self, event):
        input_text = self.input_entry.get().strip()  # 사용자 입력
        self.total_chars += len(self.current_sentence)

        for i in range(min(len(self.current_sentence), len(input_text))):  # 글자 비교 후 정확도 계산
            if self.current_sentence[i] == input_text[i]:
                self.correct_chars += 1

        self.hangul_count += len(re.findall("[ㄱ-ㅎㅏ-ㅣ가-힣]", input_text))  # 한글 개수
        self.space_count += input_text.count(" ")  # 띄어쓰기 개수

        self.add_input_history(self.current_sentence, is_user=False)  # 주어진 문장 추가
        self.add_input_history(input_text, is_user=True)  # 사용자 입력 문장 추가

        if self.current_sentence_index >= len(self.sentences):
            self.display_result()
            self.input_entry.config(state='disabled')  # 입력 비활성화
            self.input_entry.unbind("<Return>")  # 엔터 키 입력 해제
            return

        self.next_sentence()  # 다음 문장 불러오기

    def add_input_history(self, text, is_user=False):
        label = tk.Label(
            self.input_history_frame,
            text=text,
            font=('Arial', 12)
        )

        if is_user:
            label.config(fg="black")  # 사용자 입력은 검은색으로 설정
        else:
            label.config(fg="blue")  # 주어진 문장은 파란색으로 설정

        label.pack()
        self.input_history_labels.append(label)

        if len(self.input_history_labels) > self.max_input_history:
            label_to_remove = self.input_history_labels.pop(0)
            label_to_remove.pack_forget()

    def display_result(self):
        accuracy = (self.correct_chars / self.total_chars) * 100 if self.total_chars > 0 else 0
        hangul = self.hangul_count * 2 + self.space_count
        time_taken = time.time() - self.start_time
        speed = (hangul / time_taken) * 60
        result = f"정확도: {accuracy:.2f}%   타수: {speed:.2f} 글자/분   시간: {time_taken:.2f} 초"
        message = (f"{self.nickname}", f"{accuracy:.2f}%", f"{speed:.2f} 글자/분", f"{time_taken:.2f} 초")
        client_socket.sendall(str(message).encode())

        def show_result_window():
            result_window = tk.Toplevel(self.root)
            result_window.title("게임 결과")

            # 표 생성
            treeview = ttk.Treeview(result_window)
            treeview["columns"] = ("사용자", "정확도", "타수", "시간")
            treeview.column("#0", width=0, stretch=tk.NO)
            treeview.column("사용자", anchor=tk.CENTER, width=100)
            treeview.column("정확도", anchor=tk.CENTER, width=100)
            treeview.column("타수", anchor=tk.CENTER, width=100)
            treeview.column("시간", anchor=tk.CENTER, width=100)

            treeview.heading("사용자", text="사용자")
            treeview.heading("정확도", text="정확도")
            treeview.heading("타수", text="타수")
            treeview.heading("시간", text="시간")

            treeview.insert("", tk.END, text="", values=(f"{self.nickname}", f"{accuracy:.2f}%", f"{speed:.2f} 글자/분", f"{time_taken:.2f} 초"))
            treeview.pack()

        def show_ranking_window():
            
            ranking_window = tk.Toplevel(self.root)
            ranking_window.title("순위 확인")
            #print(ranking_result)
            # 표 생성
            treeview = ttk.Treeview(ranking_window)
            treeview["columns"] = ("사용자", "정확도", "타수", "시간")
            treeview.column("#0", width=0, stretch=tk.NO)
            treeview.column("사용자", anchor=tk.CENTER, width=100)
            treeview.column("정확도", anchor=tk.CENTER, width=100)
            treeview.column("타수", anchor=tk.CENTER, width=100)
            treeview.column("시간", anchor=tk.CENTER, width=100)

            treeview.heading("사용자", text="사용자")
            treeview.heading("정확도", text="정확도")
            treeview.heading("타수", text="타수")
            treeview.heading("시간", text="시간")

            #랭킹 정보를 정렬 후 삽입
            ranking_data = ranking_result[0]
            ranking_list = eval(ranking_data)  

            for rank, (user, accuracy, speed, time) in enumerate(ranking_list, start=1):
                treeview.insert("", tk.END, text=rank, values=(user, accuracy, speed, time))

            treeview.pack()

        show_result_window()

        # 순위 확인 버튼 추가
        ranking_button = tk.Button(self.root, text="순위 확인", font=('Arial', 12), command=show_ranking_window)
        ranking_button.pack(pady=10)

    
    def receive_message(self):
        while True:
            try:
                re_message = client_socket.recv(1024).decode()
                ranking_result.append(re_message)
                
            except ConnectionError:
                print("서버 연결이 종료되었습니다.")
                break

if __name__ == '__main__':
    root = tk.Tk()
    game = TypingGame(root)
    root.withdraw()  # 게임 창을 숨김

    # 닉네임 입력 창
    nickname_window = tk.Toplevel(root)
    nickname_window.title("닉네임 입력")

    # 닉네임 라벨
    nickname_label = tk.Label(nickname_window, text="게임을 시작할 닉네임을 입력하세요:", font=('Arial', 12), padx=10, pady=10)
    nickname_label.pack()

    # 닉네임 입력 엔트리
    nickname_entry = tk.Entry(nickname_window, font=('Arial', 12), width=30)
    nickname_entry.pack(pady=10)
    nickname_entry.focus_set()

    def start_game(event=None):
        nickname = nickname_entry.get()
        if nickname:
            game.nickname = nickname  # 게임 객체의 닉네임 설정
            nickname_window.destroy()  # 닉네임 입력 창 닫기
            root.deiconify()  # 게임 창 표시
            game.start_game()

    start_button = tk.Button(nickname_window, text="시작", font=('Arial', 12), command=start_game)
    start_button.pack(pady=10)

    nickname_window.bind("<Return>", start_game)
    root.mainloop()
