---
title: PikaXPS 다운로드
description: 맥·윈도우용 무료 PikaXPS XPS 피크 피팅 프로그램 다운로드.
---

PikaXPS는 무료 오픈소스(GPLv3)입니다. 계정도, 파이썬 설치도 필요 없습니다.

## 다운로드 (최신 버전)

- **⬇ macOS (Apple Silicon) — [PikaXPS-macOS.dmg](https://github.com/contact993/pikaxps/releases/latest/download/PikaXPS-macOS.dmg)**
- **⬇ Windows 10 / 11 (x64) — [PikaXPS-Windows-x64.zip](https://github.com/contact993/pikaxps/releases/latest/download/PikaXPS-Windows-x64.zip)**

위 링크는 파일을 바로 받습니다. (모든 버전을 보려면
[릴리스 페이지](https://github.com/contact993/pikaxps/releases)에서 **Assets** 아래의 `.dmg` / `.zip`을
받으세요 — 자동 생성되는 "Source code"는 소스코드라 받지 마세요.)

이 앱은 **무서명**(유료 Apple/Microsoft 인증서 없음)이라 첫 실행 시 OS가 경고를 띄웁니다. 정상이며,
아래 한 번만 해주면 됩니다.

### macOS (Apple Silicon)에서 열기

1. `.dmg`를 열고 **PikaXPS**를 **응용 프로그램**으로 드래그합니다.
2. 무서명 앱 허용 (본인 macOS에서 되는 방법으로):
   - **권장:** **터미널**에서 `xattr -cr "/Applications/PikaXPS.app"` 실행 후 평소처럼 열기. ("손상되어 열 수 없습니다"가 뜨는 건 다운로드 격리 플래그 때문이고, 이 명령이 그걸 지웁니다.)
   - **또는 설정에서:** PikaXPS를 한 번 더블클릭(차단됨) → **시스템 설정 → 개인정보 보호 및 보안** → 아래로 스크롤 → **"확인 없이 열기"** → **열기**.
   - **구형 macOS:** 앱 **우클릭 → 열기 → 열기**.

:::caution[Apple Silicon 전용]
이 빌드는 **Apple Silicon(M1–M4)** 맥에서만 돌아갑니다. **Intel 맥에서는 실행되지 않습니다.**
Intel/Linux 빌드가 필요하면 [이슈로 알려주세요](https://github.com/contact993/pikaxps/issues/new/choose).
:::

### Windows (10 / 11, x64)에서 열기

1. **`.zip` 우클릭 → 압축 풀기.** 압축 안에서 바로 실행하지 마세요 — 앱이 폴더 전체를 필요로 합니다.
2. 압축 푼 **PikaXPS** 폴더에서 **PikaXPS.exe**를 실행합니다.
3. 파란 **SmartScreen** 창이 뜨면: **추가 정보 → 실행** (무서명이라 그렇고, 다운로드가 늘면 경고가 사라집니다).

## 소스에서 실행

```bash
git clone https://github.com/contact993/pikaxps && cd pikaxps
python -m venv .venv && . .venv/bin/activate
pip install -e .
python -m xpsfit.app
```

## ⭐ 설치 후

PikaXPS는 **광고 없는 100% 무료**입니다. 도움이 되셨다면 두 가지가 도구를 살립니다:

- **[GitHub에서 Star →](https://github.com/contact993/pikaxps)** — 도구가 실제로 쓰인다는 가장 강한 신호입니다.
- **[논문에 인용 →](/pikaxps/ko/cite/)** — 인용은 무료 학술 도구의 지속 개발을 정당화합니다.
