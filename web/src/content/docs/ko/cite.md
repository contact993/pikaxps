---
title: Corepeak 인용 방법
description: 논문에서 Corepeak XPS 피크 피팅 소프트웨어를 인용하는 방법.
---

Corepeak이 연구에 도움이 됐다면 언급해 주세요 — 무료 학술 도구가 지속 개발을 정당화하는 방법입니다.

## 가장 간단한 방법 — Methods에 한 줄

분석을 서술하는 곳에 이름만 넣으면 됩니다. 예를 들어:

> *XPS 스펙트럼은 Corepeak (https://github.com/contact993/corepeak)으로 분석(피크 피팅)하였다.*

또는

> *피크 피팅과 정량은 Corepeak으로 수행하였다.*

대부분의 저널에서는 **Methods / Experimental** 섹션에 한 문장 + URL이면 완전하고 유효한 소프트웨어
인용입니다 — 그 이상은 필요 없습니다.

:::tip[이 광고 없는 무료 도구를 지원하는 두 가지 방법]
**⭐ [GitHub에서 Corepeak Star](https://github.com/contact993/corepeak)** 그리고 Methods에 한 줄 언급.
둘 다 무료이고 몇 초면 되며, 광고 없는 학술 도구가 유지되는 방법입니다.
:::

## 형식 인용 (선택)

저널이 참고문헌 목록에 정식 항목을 요구하면 — DOI가 있는 동료심사 소프트웨어 논문을 준비 중이며,
그 전까지는 저장소와 사용한 버전을 인용해 주세요:

```bibtex
@software{corepeak,
  author  = {Kim, Taehee},
  title   = {Corepeak: free cross-platform XPS peak fitting with a built-in fit auditor},
  year    = {2026},
  url     = {https://github.com/contact993/corepeak},
  version = {0.1.3}
}
```

저장소에 [`CITATION.cff`](https://github.com/contact993/corepeak/blob/main/CITATION.cff)가 있어서
GitHub의 "Cite this repository" 버튼이 항상 현재 버전을 알려줍니다.

#### 레퍼런스 데이터 출처
내장 결합에너지 값은 문헌 레퍼런스입니다. 해당하는 경우 원 출처도 함께 인용해 주세요:
M. C. Biesinger 외(*Appl. Surf. Sci.* 2010/2011; *Surf. Interface Anal.* 2009); J. F. Moulder 외,
*Handbook of XPS*(1992); NIST XPS Database SRD 20; RSF는 J. H. Scofield(1976).
