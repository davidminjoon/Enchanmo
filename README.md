# Enchanmo

For NMIXX: 엔써들의 찬란한 모임 / 엔끌벅적 엔써들의 소통방 (카카오톡 오픈채팅)

우주최강 아이돌 엔믹스의 사진을 종합적으로 관리하기 위한 소프트웨어입니다.

응용 프로그램(exe)으로 배포된 파일이 있으나, 원작자의 허가를 받지 않은 재배포는 금지하므로
EXE파일 없이 직접 git으로부터 빌드하고자 한다면 아래 절차를 따라주시기 바랍니다.

## 깃으로부터 빌드하여 실행하기
배포된 파일 (고독한 조수.exe)를 사용하지 않고 직접 빌드할 경우 다음과 같이 진행합니다.
### 파이썬 버전
고독한 조수는 파이썬 버전 3.11 이상을 요구합니다.
### 빌드 명령어
명령 프롬프트를 열고 다음 명령을 순서대로 실행하세요.
```bash
git clone https://github.com/davidminjoon/Enchanmo.git
cd Enchanmo
pip install -r dependencies.txt
```
### 실행
명령 프롬프트를 열거나 Visual Studio Code와 같은 IDE를 사용하여 ``godok_assistant\src\godok_ui.py``를 실행하세요.

명령 프롬프트를 사용하는 경우, 아래 명령어를 쓰면 됩니다.
```bash
python3 godok_assistant/src/godok_ui.py
```
