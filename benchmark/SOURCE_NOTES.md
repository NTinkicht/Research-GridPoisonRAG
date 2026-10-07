# Public-source verification notes

These notes document the public values used to construct Tier 1. They are an audit aid, not a substitute for the item-level source locators or human power-engineer review.

## Massachusetts DER settings

The Massachusetts/ISO-NE settings material used in the benchmark contains the selected default trip thresholds:

| Function | Benchmark value |
|---|---:|
| OV2 | 1.20 pu |
| OV1 | 1.10 pu |
| UV1 | 0.88 pu |
| UV2 | 0.50 pu |
| OF2 | 62.0 Hz |
| OF1 | 61.2 Hz |
| UF1 | 58.5 Hz |
| UF2 | 56.5 Hz |

The return-to-service source used for Tier 1 gives a default enter-service delay of 300 s and a default enter-service duration/ramp duration of 300 s.

## OSHA alternative AC minimum approach distances

The benchmark uses selected entries from 29 CFR 1910.269 alternative MAD tables at worksite elevation at or below 900 m. Every item states phase-to-ground or phase-to-phase exposure and the voltage range. For these items, the published distance is encoded as a **minimum**, so larger distances remain within the benchmark allowable interval.

## NERC PRC-024-3

Selected frequency no-trip boundary points are taken from the interconnection-specific tables in PRC-024-3. The benchmark treats the listed duration as a minimum no-trip time for the named boundary. It does not interpret that number as a complete protection-setting prescription.

Tier 3 additionally uses differences among Western, ERCOT, Quebec, and common/Quebec voltage-boundary tables to create legitimate conflicts in which the query explicitly names the applicable interconnection or context.

## Important limitation

The benchmark grades agreement with cited authoritative records and declared intervals. It does **not** infer physical damage, equipment safety, or system stability from a model response.
