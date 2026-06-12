# Satellite 피크 — shake-up, plasmon, multiplet

주피크 옆(거의 항상 **높은 BE 쪽**)에 나타나는 넓고 약한 구조들입니다.
새로운 화학종이 아니라 **같은 화학종의 광전자 방출이 추가 에너지를 잃은 것**입니다.

## 종류

**Shake-up** — 광전자가 나가면서 가전자 하나를 비점유 준위로 들뜨게 함
(π→π*, 전이금속의 charge-transfer). 그만큼 운동에너지를 잃어 겉보기 BE가 올라갑니다.
- 대표 지문: **Cu(II)** 주피크 +~8.5 eV의 강한 위성 (Cu(I)/Cu(0)에는 없음 → 산화수 판별!)
- **Ni(II)** +~6.1 eV, **Co(II)** +~6.3 eV (강한 위성 = high-spin 2가 지문)
- sp² 탄소의 **π-π\*** : C 1s 주피크 +~6.6 eV (290.5–291.5 eV)

**Plasmon loss** — 금속에서 전도전자의 집단 진동을 들뜨게 하며 생기는 손실 피크.
플라즈몬 에너지 간격으로 **여러 개가 연달아** 나타날 수 있음 (Al, Mg, Si 등에서 뚜렷).

**Shake-off / multiplet** — 가전자가 완전히 떨어져 나가거나(연속준위),
홀전자와 코어홀의 결합으로 갈라지는 구조 (Cr³⁺, Mn²⁺, Fe³⁺ 등의 넓은 envelope).

## 왜 중요한가

1. **다른 화학종으로 오인 금지** — 위성을 새 산화 상태로 해석하는 것이 가장 흔한 오독
2. **정량에 포함** — 위성 강도는 그 화학종 방출의 일부입니다. 빼고 정량하면
   해당 종이 과소평가됩니다 (Biesinger의 Cu(0):Cu(II) 정량 프로토콜이 대표 사례)
3. **산화수 판별 지문** — 위성의 유무/강도/간격 자체가 정보 (예: CuO vs Cu₂O)

## 이 프로그램에서 쓰는 법

피크 테이블 맨 앞 **Type 칸에서 "Satellite" 선택** → 주피크와 Δ(간격)를 지정하면:

- 위치가 **주피크 + Δ**로 묶입니다 (주피크가 움직이면 따라감; Δ는 🔗에서 수정/해제)
- FWHM은 넓게 시작 (위성은 본질적으로 broad)
- **Quantify에서 면적이 주피크 화학종에 자동 합산**됩니다
- 🔍 진단이 위성으로 인식해 "알려진 상태 아님" 같은 오경고를 내지 않습니다

> Reference DB의 상태 설명에 "satellite ~786" 같은 힌트가 있으면 그 간격을 Δ로 쓰세요.

#### 참고문헌
- M.C. Biesinger, XPS Reference Pages (xpsfitting.com) — Shake-up Structure / Cu(0):Cu(II) Calculations
- HarwellXPS Guru — Shake-up Peaks (harwellxps.guru)
- M.C. Biesinger 외, *Appl. Surf. Sci.* 257 (2011) 2717
