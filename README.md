# XPSFit Studio

XPS peak fitting 데스크톱 앱 — **XPSPEAK 4.1의 워크플로**를 현대적으로 재현하고,
거기에 **문헌 기반 레퍼런스 DB**와 **한국어 분석 가이드**를 내장했습니다.
맥/윈도우 양쪽에서 네이티브로 동작합니다 (1999년산 XPSPEAK + Parallels VM 조합 대체).

![screenshot](docs/screenshot.png)

## 핵심 기능

| | |
|---|---|
| **백그라운드** | Shirley(반복법) · Shirley+Linear · Tougaard(U2) · Linear — 끝점 드래그 조절 |
| **라인섀입** | GL sum(XPSPEAK 기본) · GL product(CasaXPS) · Voigt · 지수꼬리 비대칭 · Doniach-Šunjić |
| **Constraint** | 피크 간 관계식 (`p0_center + 1.18`, `p0_area * 0.5`, `p0_fwhm`) — XPSPEAK의 "Relation with another peak" |
| **레퍼런스 DB** | 24원소 binding energy + spin-orbit splitting/면적비 + RSF, 전 항목 문헌 출처 (Biesinger, Moulder, NIST SRD 20) |
| **Recipe** | Ni 2p/Co 2p/Fe 2p/C 1s/O 1s/N 1s/S 2p/Pt 4f/Mo 3d… 원클릭 멀티피크 세트 (constraint 자동) |
| **내 레퍼런스** | 직접 참고하는 문헌값을 DB에 추가/수정(★) — `~/.xpsfit/user_refdb.json` 오버레이라 앱 업데이트에도 유지, 새 원소/오비탈도 등록 가능 |
| **Doublet 삽입** | splitting·면적비·FWHM 자동 고정된 spin-orbit 쌍 |
| **한국어 가이드** | 백그라운드/라인섀입/constraint/대전보정/권장절차/정량 — 컨텍스트 도움말 패널 |
| **임포트** | .dat/.txt/.csv/.xlsx/.xls/.vms — 미리보기에서 열 직접 선택, KE→BE 변환, 자동 감지. Thermo Avantage 엑셀 export(시트별 스펙트럼+파라미터 블록) 자동 인식, 텍스트를 .xls로 위장한 장비 export도 처리 |
| **붙여넣기** | 📋 Paste (⌘⇧V) — 엑셀/오리진에서 복사한 BE·강도 열을 표에 바로 붙여넣어 region 생성 |
| **정량** | Scofield RSF 기반 atomic % (doublet 자동 합산, RSF 수정 가능) |
| **배치** | 같은 모델을 여러 파일에 일괄 적용 (반응 전후 비교) |
| **내보내기** | 파라미터/곡선 CSV · 전체 Excel · 논문용 figure (PNG/SVG/PDF, residual 포함) |
| **도구** | BE Shift(대전 보정 — ±값을 전체/선택 region에 일괄 적용, C-C→284.8 자동 계산) · Optimise Peak/Region/All |

## 실행

### 개발 환경에서

```bash
cd ~/xpsfit
.venv/bin/python -m xpsfit.app
```

### 패키징된 앱

- **맥**: `dist/XPSFit Studio.app` — 첫 실행은 우클릭 → "열기" (서명 미등록 경고 우회)
- **윈도우**: [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) 참고 (Parallels VM에서 빌드)

## 5분 튜토리얼

1. **File → Import Data…** → `samples/Ni2p_NiFoam.dat` 선택
   - 위저드에서 구분자/시작 행이 자동 감지됨 → 열 매핑 확인 → Region 이름 "Ni 2p" → OK
2. 우측 **Reference DB** 패널이 Ni 2p로 자동 전환됨
   - 상태 선택 후 **가이드선 표시** → 문헌 BE 위치와 데이터 비교
3. Recipe 콤보에서 **"Ni 2p3/2 — metal / NiO / hydroxide screen"** → **Recipe 삽입**
4. **⚡ Fit Region** → 하단 테이블에서 파라미터·Area % 확인
5. 피크 핸들을 드래그해 위치/높이 조절 가능 (constraint 걸린 피크는 자동 보호)
6. **File → Export → Figure…** 로 논문용 그림 저장

샘플 데이터: `Ni2p_NiFoam.dat`(탭 구분+헤더), `C1s_carbon.csv`, `S2p_MoS2.xlsx`(doublet 연습),
`Pt4f_kinetic.txt`(KE축 변환 연습)

## 프로젝트 구조

```
src/xpsfit/
├── core/        # GUI 독립 엔진: 백그라운드·라인섀입·lmfit fitting·정량·배치·세션
├── io/          # 임포터(.dat/.txt/.csv/.xlsx/VAMAS) · 내보내기(CSV/Excel/figure)
├── refdb/       # binding_energies.json · recipes.json · explanations/*.md (한국어)
└── ui/          # PySide6 + pyqtgraph GUI
tests/           # 49 tests: Shirley 수렴·골든 fit 복원·constraint 정확성·GUI 스모크
```

레퍼런스 DB는 일반 JSON이라 직접 항목을 추가/수정할 수 있습니다
(`src/xpsfit/refdb/binding_energies.json`).

## 테스트 / 빌드

```bash
.venv/bin/python -m pytest               # 전체 테스트
.venv/bin/python build_scripts/launch_check.py   # 실화면 E2E 체크 + 스크린샷
# 맥 .app 빌드: build_scripts의 pyinstaller 명령 (아래 한 줄)
.venv/bin/pyinstaller --noconfirm --windowed --name "XPSFit Studio" \
  --icon build_scripts/icon.icns --add-data "src/xpsfit/refdb:xpsfit/refdb" \
  --paths src build_scripts/entry.py
```

## 데이터 출처

- M.C. Biesinger et al., *Appl. Surf. Sci.* 257 (2011) 2717 — Cr/Mn/Fe/Co/Ni 2p
- M.C. Biesinger et al., *Surf. Interface Anal.* 41 (2009) 324 — Ni 2p
- M.C. Biesinger et al., *Appl. Surf. Sci.* 257 (2010) 887 — Sc/Ti/V/Cu/Zn
- Moulder et al., *Handbook of XPS*, Perkin-Elmer (1992)
- NIST XPS Database SRD 20 · Scofield (1976) RSF

> DB 값은 문헌 출발점입니다. 정밀 multiplet 정량은 인용된 원논문의 Table을 확인하세요.

## 로드맵 (미구현)

- Undo/Redo · 백그라운드 동시 fitting(active background) · Biesinger multiplet 고정비율 envelope
- 장비별 네이티브 포맷(Thermo .avg, Kratos .des) 직접 파싱 · GitHub Actions 자동 빌드
