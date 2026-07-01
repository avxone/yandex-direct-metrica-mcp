# Session: GEO-9 manual SERP evidence

Date: 2026-06-30

## Completed

- Recorded operator-supplied browser-visible SERP evidence for `GEO-9`.
- Confirmed the operator screenshots were taken on a desktop browser session with:
  - region: `Moscow, Russia`
  - interface language: `Russian`
- Recorded that the screenshot export is narrow/full-page capture output from the desktop browser, not a separate mobile-device run.

## Manual validation summary

The evidence is sufficient to clear the previously missing `operator-browser` input for the feature-stage validation.

Observed browser-visible comparisons against the normalized `search_serp` output:

1. `гарнитура для колл центра купить`
   - browser-visible structure shows a top shopping/promo carousel followed by promo/text blocks before organic results;
   - overlapping visible domains with normalized output include `mango-office.ru`, `citilink.ru`, `voicexpert.ru`, `ozon.ru`, and `voltacom.ru`;
   - result: structure and major domains are consistent; exact top-ad count is time-sensitive in live SERP.

2. `jabra evolve2 75 купить`
   - browser-visible structure shows a top shopping/promo carousel followed by multiple promoted/store results before and alongside organic results;
   - overlapping visible domains with normalized output include `headset.ru`, `onlinetrade.ru`, `citilink.ru`, `doctorhead.ru`, `xcom-shop.ru`, `ozon.ru`, and `dns-shop.ru`;
   - result: structure and major domains are consistent; exact ordering is live-SERP dependent.

3. `гарнитуры voicexpert для офиса`
   - browser-visible structure shows one top promo `voicexpert.ru` result before the first clearly organic result;
   - this is consistent with the normalized `ads_count_top=1`;
   - overlapping visible domains with normalized output include `voicexpert.ru`, `xcom-shop.ru`, `headset.ru`, `onlinetrade.ru`, `chipdip.ru`, `skomplekt.com`, and `ozon.ru`;
   - result: consistent.

4. `профессиональная гарнитура для call центра`
   - browser-visible structure shows a top shopping/promo carousel and promo blocks before the first organic result;
   - overlapping visible domains with normalized output include `mango-office.ru`, `citilink.ru`, `voltacom.ru`, `headset.ru`, `ozon.ru`, and `voicexpert.ru`;
   - result: structure is consistent with the normalized ad/organic split.

## To Do

- Add a concise Linear comment for `GEO-9` summarizing the operator evidence.
- Move `GEO-9` from `Backlog` back to `Todo` so Symphony can continue the feature stage with the operator evidence now satisfied.
