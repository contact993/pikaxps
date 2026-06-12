# Windows .exe 빌드 가이드 (Parallels Windows 11 VM)

맥의 Parallels Windows 11 VM 안에서 한 번만 수행하면 됩니다.
결과물 `XPSFit Studio.exe`는 어느 Windows PC에서나 더블클릭으로 실행됩니다 (Python 설치 불필요).

## 1. 준비 (VM 안에서)

1. [python.org](https://www.python.org/downloads/)에서 Python 3.12+ 설치
   - 설치 시 **"Add python.exe to PATH" 체크 필수**
2. 프로젝트 폴더를 VM으로 복사
   - Parallels 공유 폴더: 맥의 `~/xpsfit`가 보통 `\\Mac\Home\xpsfit` 로 보입니다
   - VM 로컬 디스크로 복사하는 것을 권장 (예: `C:\xpsfit`) — 공유 폴더에서 직접 빌드하면 느리고 권한 문제가 생길 수 있음
   - `.venv/`, `build/`, `dist/` 폴더는 복사하지 않아도 됩니다

## 2. 빌드 (PowerShell 또는 cmd)

```powershell
cd C:\xpsfit
python -m venv .venv
.venv\Scripts\activate
pip install -e . pyinstaller

pyinstaller --noconfirm --clean --windowed --name "XPSFit Studio" ^
  --add-data "src\xpsfit\refdb;xpsfit\refdb" ^
  --paths src ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick ^
  build_scripts\entry.py
```

> PowerShell에서는 줄바꿈 문자를 `^` 대신 백틱(`` ` ``)으로 바꾸거나 한 줄로 입력하세요.
> 아이콘을 넣으려면 `--icon build_scripts\icon.ico` 추가 (icon_1024.png을
> [온라인 변환기나 ImageMagick]으로 .ico로 변환).

## 3. 결과물

- `dist\XPSFit Studio\XPSFit Studio.exe` — 이 **폴더 전체**를 배포하면 됩니다
- 단일 파일을 원하면 위 명령에 `--onefile`을 추가 (시작 속도는 느려짐)

## 4. 배포 시 주의

- Windows Defender SmartScreen이 서명 없는 exe에 경고를 띄울 수 있습니다 →
  "추가 정보" → "실행". 연구실 내부 배포면 문제없습니다
- **CPU 아키텍처 주의** (Apple Silicon Mac의 Parallels = ARM Windows):
  - exe는 **빌드에 사용한 Python의 아키텍처**를 따라갑니다
  - 일반 연구실 PC(x64)용 exe가 필요하면 VM에 **x64용 Python 설치 파일**
    ("Windows installer (64-bit)")을 설치하고 그걸로 빌드하세요 — ARM Windows의
    x64 에뮬레이션 덕분에 빌드는 그대로 되고, 결과물은 x64 PC에서 네이티브로 동작합니다
  - 빌드가 너무 느리면 실제 x64 PC에서 한 번 빌드하거나 GitHub Actions 사용 (아래)

## 5. (선택) GitHub Actions 자동 빌드

저장소를 GitHub에 올리면 macOS/Windows(x64) 빌드를 CI에서 자동 생성할 수 있습니다.
원하면 `.github/workflows/build.yml` 작성을 요청하세요.
