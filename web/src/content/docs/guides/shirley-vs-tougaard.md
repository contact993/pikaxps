---
title: Shirley vs Tougaard background in XPS
description: When to use a Shirley, Tougaard, or linear background for XPS peak fitting, and how the choice changes your peak areas.
---

The background you subtract directly determines your peak areas, so the choice matters as much as
the peaks themselves. PikaXPS offers Linear, Shirley, Shirley + Linear, and Tougaard (U2), plus an
*active Shirley* that co-fits with the peaks.

## Linear
A straight line between the two endpoints. Use it for weak peaks on a nearly flat background
(C 1s, N 1s, O 1s) and narrow windows. Avoid it for transition-metal 2p regions, where the step
across the peak is large.

## Shirley
The standard choice for most metal / transition-metal regions. The background rises toward higher
binding energy in proportion to the integrated peak area above it, computed iteratively. It's
**sensitive to where you place the endpoints** — keep them on flat regions well away from the peak
tails, and nudge them ±1 eV to check how much the area moves.

### Active Shirley
Derives the background from the *peak model* instead of the raw data, and optimises it together
with the peaks. Less sensitive to noise and to other structure inside the window — switch it on
when a plain Shirley looks wrong.

## Tougaard (U2)
The most physically rigorous option: it integrates the universal inelastic-loss cross-section. Use
it when absolute quantification matters and you measured a wide window (30+ eV past the peak). It's
inaccurate over narrow windows, where Shirley is usually enough.

## Practical summary
| Situation | Recommended |
|---|---|
| Transition-metal 2p (Ni, Co, Fe…) | Shirley (or active Shirley) |
| C 1s, N 1s, O 1s | Shirley or Linear |
| Absolute quantification, wide window | Tougaard |
| Background looks wrong under plain Shirley | Active Shirley |

Always report which background and energy range you used — changing it changes your areas.

[Download PikaXPS →](/download/) and try **Fit BG** to settle the background before adding peaks.
