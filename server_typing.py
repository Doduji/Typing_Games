import socketserver
import threading
import time
import socket
import pymysql

clients = []  # 클라이언트 정보를 저장할 리스트
results = []  # 클라이언트로부터 받은 타자 연습 결과를 저장할 리스트
ranking = []  # 랭킹 정보를 저장할 리스트
class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client_info = self.client_address  # 클라이언트 정보
        clients.append(client_info)  # 클라이언트 정보를 리스트에 추가
        client_port = client_info[1]  # 클라이언트 포트

        print(f"클라이언트가 연결되었습니다. IP: {client_info[0]}, 포트: {client_port}")

        # 클라이언트로부터 메시지 수신 및 처리
        while True:
            try :
                received_data = self.request.recv(1024).decode()
                if not received_data:
                    break

                print(f"클라이언트로부터 받은 메시지: {received_data}")

                # 클라이언트로부터 받은 타자 연습 결과 저장
                results.append(received_data)

                # 데이터베이스에 결과 삽입
                try:
                    conn = pymysql.connect(host='127.0.0.1', user='root', password='root', db='windows_programming', charset='utf8')
                    cur = conn.cursor()
                    username, accuracy, speed, time_taken = received_data.split(",")

                    #username 필터링
                    username = username.strip("'")
                    username = username.strip("(")
                    username = username.strip("'")

                    # 정확도에서 '%' 문자 제거하고 숫자 값만 추출
                    accuracy = accuracy.strip().replace('%', '')
                    accuracy = accuracy.strip("'")

                    # 정확도를 float으로 변환
                    accuracy = float(accuracy)

                    # 속도에서 숫자 부분만 추출
                    speed = speed.split()[0]
                    speed = speed.strip("'")
                    # 속도를 float으로 변환
                    speed = float(speed)

                    #시간 문자열 필터링
                    time_taken = time_taken.split()[0]
                    time_taken = time_taken.strip("'")
                
                    # INSERT 쿼리 실행
                    sql = "INSERT INTO user_ranking (username, accuracy, speed, time_taken) VALUES (%s, %s, %s, %s)"
                    cur.execute(sql, (username, accuracy, speed, time_taken))

                    conn.commit()
                    print("결과를 데이터베이스에 삽입했습니다.")

                    # 랭킹 정보 전송
                    ranking_table_search()
                    message = str(ranking)
                    self.request.send(message.encode())

                except Exception as e:
                    print(f"데이터베이스 삽입 오류: {e}")
                    conn.rollback()
                finally:
                    conn.close()

            except ConnectionResetError :
                break
       
        print(f"클라이언트와의 연결이 종료되었습니다. IP: {client_info[0]}, 포트: {client_port}")

def ranking_table_search():
    conn = pymysql.connect(host='127.0.0.1', user='root', password='root', db='windows_programming', charset='utf8')
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_ranking")
    rows = cur.fetchall()
    ranking.clear()
    for row in rows:

        new_row = (row[0], f"{row[1]}%", f"{row[2]} 글자/분", f"{row[3]} 초")
        ranking.append(new_row)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run_server():
    # 서버 주소와 포트
    server_host = 'localhost'
    server_port = 55555

    # 멀티스레드 TCP 서버 생성
    server = ThreadedTCPServer((server_host, server_port), MyTCPHandler)
    print("서버가 시작되었습니다. 클라이언트의 연결을 기다립니다...")

    # 클라이언트 연결 대기
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # 종료 시그널이 입력될 때까지 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # 서버 종료
    server.shutdown()
    server.server_close()

run_server()
