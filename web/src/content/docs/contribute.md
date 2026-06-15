---
title: Contribute a reference value
description: Help grow PikaXPS's citation-backed XPS binding-energy database by submitting reference values with sources.
---

PikaXPS's reference database is **citation-backed** — every binding-energy value carries its
literature source. You can help it grow, and the database gets richer with every accepted
submission.

## Submit a value

[📚 Submit a reference value →](https://github.com/contact993/pikaxps/issues/new?template=reference_submission.yml)

You'll be asked for the element, orbital, chemical state, binding energy (and optional range /
lineshape hint), and — **required** — the **literature source** (citation or DOI).

You can also submit straight from the app: **Help ▸ 레퍼런스 값 제보**.

## What happens next
1. The submission is reviewed for a valid literature source.
2. Accepted values are merged into the next release — **with credit to you**.
3. Everyone gets a better, more complete reference database.

:::caution
Please submit individual **values with a citation**, not copyrighted tables. Facts (a measured
binding energy and its source) are fine to share; redistributing a whole copyrighted compilation
(e.g. a handbook table) is not.
:::

## Add private references just for yourself
Don't want to share, or need lab-specific values? Add them directly in the app — they're saved to
`~/.xpsfit/user_refdb.json`, marked with a ★, and kept across updates. Copy that file to move your
references to another computer.
