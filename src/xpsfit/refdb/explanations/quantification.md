# 정량 분석 (Atomic %)

원소 i의 원자 분율: **nᵢ ∝ Aᵢ / RSFᵢ** — 피크 면적을 감도 인자(RSF)로 나눠 비교합니다.

```
atomic % = (Aᵢ/RSFᵢ) / Σⱼ(Aⱼ/RSFⱼ) × 100
```

## RSF (Relative Sensitivity Factor)

이 프로그램의 기본 RSF는 **Scofield 광이온화 단면적**(Al Kα, C 1s = 1.0 기준)입니다.
중요한 한계:

- Scofield 값은 **순수 단면적**입니다. 실제 감도는 장비의 transmission function,
  IMFP(비탄성 평균자유행로), 분석기 각도에 따라 달라집니다
- **장비 제조사 RSF가 있으면 그것을 우선 사용**하세요 (Quantify 표에서 직접 수정 가능)
- 같은 장비, 같은 조건에서 측정한 시료끼리의 **상대 비교**가 가장 신뢰성 높습니다

## 사용 규칙

1. 모든 영역을 **같은 백그라운드 방식**으로 처리
2. doublet은 **두 성분 면적의 합**으로 계산 (이 프로그램은 자동 합산)
3. 면적은 같은 pass energy로 측정된 영역끼리만 비교
4. 표면 민감도: XPS는 상위 ~5-10 nm만 봅니다. "bulk 조성"이 아니라 **표면 조성**입니다

## 불확실성

XPS 정량의 현실적 정확도는 **±10% (상대)** 수준입니다. atomic % 소수점 둘째 자리는
의미가 없습니다.

#### 참고문헌
- J.H. Scofield, *J. Electron Spectrosc. Relat. Phenom.* 8 (1976) 129
- C.J. Powell, A. Jablonski, *J. Electron Spectrosc.* 178-179 (2010) 331 (IMFP)
- M.P. Seah, *Surf. Interface Anal.* 31 (2001) 721
