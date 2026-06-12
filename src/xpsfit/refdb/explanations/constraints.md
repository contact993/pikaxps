# 피크 간 Constraint (XPSPEAK의 "Relation with another peak")

Constraint는 과적합을 막는 가장 강력한 도구입니다. "피크 하나 더 넣으면 fit은 항상 좋아진다"
— 그래서 **물리로 정해진 관계는 전부 고정**해야 자유도가 줄고 결과가 화학적으로 의미를 가집니다.

## Spin-orbit doublet — 반드시 고정

p, d, f 오비탈은 spin-orbit 결합으로 두 개의 피크로 갈라지며, **간격과 면적비는 물리 상수**입니다:

| 오비탈 | 성분 | 면적비 (이론) |
|---|---|---|
| p | p3/2 : p1/2 | 2 : 1 |
| d | d5/2 : d3/2 | 3 : 2 |
| f | f7/2 : f5/2 | 4 : 3 |

splitting(eV)은 원소·오비탈마다 다릅니다 (레퍼런스 DB 패널에서 확인 — 예: S 2p 1.18,
Mo 3d 3.15, Pt 4f 3.33 eV). 이 프로그램의 "Insert doublet"은 세 가지를 자동으로 겁니다:

- partner center = main center + splitting (고정)
- partner area = main area × 비율 (고정)
- partner FWHM = main FWHM (링크)

> 예외: 일부 금속(Ti 등)은 Coster-Kronig 효과로 2p1/2가 더 넓어져 비율이 이론값에서 약간
> 벗어날 수 있습니다. 그래도 출발은 이론값으로.

## FWHM 링크

같은 원소의 다른 화학 상태(예: C-C와 C-O)는 보통 비슷한 폭 → FWHM을 묶어 시작하고,
화학적 근거가 있을 때만 풉니다 (산화물은 금속보다 넓은 것이 정상).

## Center 범위 제한

각 성분의 center는 문헌값 ±0.2~0.5 eV로 제한하세요. 레퍼런스 DB에서 피크를 삽입하면
자동으로 설정됩니다. fitting이 center를 문헌 범위 밖으로 끌고 가면 모델이 틀렸다는 신호입니다.

## 표현식 문법

이 프로그램의 constraint는 lmfit 표현식입니다. 피크 번호 i의 파라미터는 `p{i}_center`,
`p{i}_area`, `p{i}_fwhm`, `p{i}_mix`, `p{i}_asym`:

```
p0_center + 1.18      # 0번 피크에서 +1.18 eV
p0_area * 0.5         # 0번 피크 면적의 절반
p0_fwhm               # 0번 피크와 같은 폭
```

## 과적합 체크리스트

- 성분 수보다 **화학적 근거**가 먼저 (이 시료에 이 상태가 왜 있어야 하나?)
- 잔차(residual)가 구조 없이 평평하면 충분 — χ²를 더 줄이려고 성분 추가 금지
- 같은 데이터를 다른 초기값으로 fitting해도 같은 답이 나오는지 확인 (해의 유일성)
- 보고할 때 모든 constraint를 명시 (재현 가능성)

#### 참고문헌
- M.C. Biesinger 외, *Appl. Surf. Sci.* 257 (2011) 2717 — 전이금속 fitting 권장 파라미터
- 분석 보고 권장사항: D.R. Baer 외, *J. Vac. Sci. Technol. A* 37 (2019) 031401
