# Peak Lineshape (Lineshape)

The shape of an XPS peak arises from the combination of the physical width (lifetime-driven Lorentzian) and the instrumental resolution (Gaussian).

## GL Sum — Gaussian-Lorentzian Sum (default)

`(1-m)·Gaussian + m·Lorentzian`. The **%L-G (mix)** parameter is the Lorentzian fraction
(XPSPEAK convention: 0 = pure Gaussian, 100 = pure Lorentzian).

- Typical starting value: **mix = 30** (GL(30))
- Broad peaks such as oxides/insulators → higher Gaussian weight; narrow metallic peaks → higher Lorentzian weight

## GL Product — product form

CasaXPS's GL(m) product form: `exp(-4ln2(1-m)u²)·/(1+4mu²)`. Nearly identical to the Sum form, but with different
tails. **When reproducing results from another paper, use the same form as that paper** (papers using Casa → Product).

## Voigt

A true convolution of Gaussian and Lorentzian. Physically the most correct, although the GL approximation is often
sufficient in practice. Here, mix sets the fraction of the total FWHM that is the Lorentzian width.

## GL + Tail (asymmetric, XPSPEAK's TS)

A GL peak convolved with an exponential tail toward higher BE (decay length = asym parameter, eV).
**If asym = 0, this is identical to a symmetric GL.**

## Doniach-Šunjić (asymmetric, for metals)

Because of screening by conduction-band electrons, **metal peaks are intrinsically asymmetric** (with a tail toward higher BE).
The asym parameter is α (0 = Lorentzian). Use it for precise fitting of metals such as Ni, Pt, Ru, Ir, etc.

> **Why you should not fit metals with a symmetric peak**: if a symmetric peak cannot follow the high-BE tail of a metal,
> that residual is absorbed by an "oxide component," leading to **overestimation of the oxide content**. This is one of the
> most common quantitation errors for mixed metal+oxide samples.

## FWHM Guide

- As a rule, link the FWHM of the same chemical species together with a **constraint (link)**
- Typical range: 0.7–2.5 eV. Insulators/multiplet envelopes can be broader
- If the FWHM becomes abnormally large → this signals that there is an additional component, or a charging problem

#### References
- S. Doniach, M. Šunjić, *J. Phys. C* 3 (1970) 285
- G.K. Wertheim, S.B. DiCenzo, *J. Electron Spectrosc.* 37 (1985) 57
- CasaXPS lineshape documentation: casaxps.com
