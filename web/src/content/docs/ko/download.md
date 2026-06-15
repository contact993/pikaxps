---
title: PikaXPS 다운로드
description: 맥·윈도우용 무료 PikaXPS XPS 피크 피팅 프로그램 다운로드.
---

PikaXPS는 무료 오픈소스(GPLv3)입니다. 계정도, 파이썬 설치도 필요 없습니다.

## 최신 릴리스

**[GitHub Releases 페이지 →](https://github.com/contact993/pikaxps/releases)** 에서 설치파일을 받으세요.

### macOS (Apple Silicon)
1. `PikaXPS-macOS.dmg`를 열고 **PikaXPS**을 응용 프로그램으로 드래그합니다.
2. 첫 실행: **우클릭 → 열기 → 열기** (App Store 앱이 아니라서 한 번만).
3. "손상되어 열 수 없습니다"가 뜨면: 터미널에서 `xattr -cr "/Applications/PikaXPS.app"` 실행 후 다시 우클릭 → 열기.

### Windows (10 / 11, x64)
1. `.zip`을 받아 압축을 풀고 폴더 안의 **PikaXPS.exe**를 실행합니다.
2. 첫 SmartScreen 경고: **추가 정보 → 실행** (다운로드가 늘면 경고가 사라집니다).

:::note
무서명 빌드라 위 한 번의 우클릭-열기/실행 단계는 정상입니다. Intel 맥이나 Linux 빌드가 필요하면
[이슈로 알려주세요](https://github.com/contact993/pikaxps/issues/new/choose).
:::

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
