---
title: 기능
description: 백그라운드, 라인섀입, doublet/satellite, fit auditor, 출처 명시 레퍼런스 DB, 정량, 배치 피팅, 유연한 임포트 — PikaXPS의 모든 기능.
---

## 백그라운드
Shirley(반복법), Shirley + Linear, Tougaard(U2), Linear — 그리고 피크 모델에서 유도해 피크와 함께
최적화하는 **active Shirley**. 끝점은 드래그 가능하고, **Fit BG**로 피크 추가 전에 백그라운드를 먼저
맞춥니다.

## 라인섀입
Gaussian-Lorentzian(합·곱), Voigt, 지수꼬리 비대칭, 그리고 금속용 **Doniach-Šunjić**.

## 피크 종류: 단일 / Doublet / Satellite
피크 테이블에서 각 피크의 역할을 지정합니다:
- **Doublet** — spin-orbit 간격·면적비(2:1 / 3:2 / 4:3)·FWHM 자동 고정.
- **Satellite** — 주피크에 위치를 묶고, 정량 시 면적을 주피크 화학종에 합산(shake-up/plasmon 강도는
  같은 화학 상태에 속합니다).
- 피크를 **📌 고정**해 나머지만 최적화하거나, 위치만 잠글 수 있습니다.

## 🔍 fit auditor
한 번의 클릭으로 숙련된 리뷰어가 볼 항목을 검사합니다:
FWHM 타당성, 레퍼런스 DB 결합에너지 대조, doublet 무결성, 금속 라인섀입 비대칭, 예상 satellite,
과적합 신호, 대전 보정, 잔차(밴드패스 z-score), 그리고 데이터가 요구하지 않는 피크를 잡아내는
**leave-one-out 필요성 검정(BIC)**. [작동 원리 →](/pikaxps/ko/guides/fit-audit/)

## 레퍼런스 데이터베이스
24개 원소의 결합에너지·spin-orbit 파라미터·RSF — **모든 값에 문헌 출처**(Biesinger, Moulder,
NIST SRD 20). 원클릭 recipe(Ni 2p, Co 2p, Fe 2p, C 1s, O 1s, S 2p, Pt 4f, Mo 3d, …). 직접 쓰는
레퍼런스를 추가하면 로컬에 저장되고 업데이트해도 유지되며, [공유 DB에 제보](/pikaxps/ko/contribute/)할
수도 있습니다.

## 정량 & 대전 보정
Scofield-RSF 기반 atomic %(doublet·satellite 면적 자동 합산). 피팅된 C-C 피크에서 모든 region을
C 1s = 284.8 eV로 한 번에 보정.

## 임포트 & 익스포트
.dat / .txt / .csv / .xlsx / .xls, Thermo Avantage 멀티시트, VAMAS .vms, 또는 엑셀/오리진에서 두 열
붙여넣기(KE→BE 변환 내장). 파라미터·성분 곡선을 CSV/Excel로, 논문용 figure를 PNG/SVG/PDF로 출력.

## 한국어 도움말 내장
백그라운드 · 라인섀입 · constraint · 대전 보정 · 권장 절차 · 정량 가이드 — 출처 포함.
