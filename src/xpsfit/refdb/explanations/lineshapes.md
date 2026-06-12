# 피크 라인섀입 (Lineshape)

XPS 피크의 모양은 물리적 폭(수명에 의한 Lorentzian)과 장비 분해능(Gaussian)의 결합입니다.

## GL Sum — Gaussian-Lorentzian 합 (기본값)

`(1-m)·Gaussian + m·Lorentzian`. **%L-G (mix)** 파라미터가 Lorentzian 비율입니다
(XPSPEAK 표기: 0 = 순수 Gaussian, 100 = 순수 Lorentzian).

- 일반적인 시작값: **mix = 30** (GL(30))
- 산화물/절연체처럼 넓은 피크 → Gaussian 비중↑, 금속의 좁은 피크 → Lorentzian 비중↑

## GL Product — 곱 형태

CasaXPS의 GL(m) 곱 형태: `exp(-4ln2(1-m)u²)·/(1+4mu²)`. Sum과 거의 비슷하지만 꼬리가
다릅니다. **다른 논문 결과를 재현할 때는 그 논문과 같은 형태를 쓰세요** (Casa 사용 논문 → Product).

## Voigt

Gaussian과 Lorentzian의 진짜 컨볼루션. 물리적으로 가장 올바르지만 GL 근사로도 실무에선 충분한
경우가 많습니다. 여기서는 mix가 전체 FWHM 중 Lorentzian 폭의 비율을 정합니다.

## GL + Tail (비대칭, XPSPEAK의 TS)

GL 피크를 고BE 쪽으로 지수 꼬리(decay 길이 = asym 파라미터, eV)와 컨볼루션한 형태.
**asym = 0이면 대칭 GL과 동일.**

## Doniach-Šunjić (금속용 비대칭)

전도띠 전자의 스크리닝 때문에 **금속 피크는 본질적으로 비대칭**입니다 (고BE 쪽 꼬리).
asym 파라미터가 α (0 = Lorentzian). 금속 Ni, Pt, Ru, Ir 등의 정밀 fitting에 사용하세요.

> **금속을 대칭 피크로 fitting하면 안 되는 이유**: 금속의 고BE 꼬리를 대칭 피크가 못 따라가면,
> 그 잔차를 "산화물 성분"이 흡수해서 **산화물 함량이 과대평가**됩니다. 금속+산화물 혼합 시료에서
> 가장 흔한 정량 오류 중 하나입니다.

## FWHM 가이드

- 같은 화학종의 FWHM은 **링크(constraint)**로 묶는 것이 원칙
- 일반적 범위: 0.7–2.5 eV. 절연체/multiplet envelope는 더 넓을 수 있음
- FWHM이 비정상적으로 커지면 → 성분이 더 있다는 신호이거나, 대전(charging) 문제

#### 참고문헌
- S. Doniach, M. Šunjić, *J. Phys. C* 3 (1970) 285
- G.K. Wertheim, S.B. DiCenzo, *J. Electron Spectrosc.* 37 (1985) 57
- CasaXPS 라인섀입 문서: casaxps.com
