# Public-source audit — 2026-10-08

This audit verifies the **public numeric facts** used in Tier 1 against currently accessible authoritative or corroborating web sources. It is separate from the external power-engineer review gate; it does **not** set `engineer_reviewed=true`.

## Massachusetts DER trip settings — T1-001 to T1-008

Verified against the Massachusetts Technical Standards Review Group / ISO-NE material:

- OV2 = 1.20 pu
- OV1 = 1.10 pu
- UV1 = 0.88 pu
- UV2 = 0.50 pu
- OF2 = 62.0 Hz
- OF1 = 61.2 Hz
- UF1 = 58.5 Hz
- UF2 = 56.5 Hz

Source:
https://www.mass.gov/doc/tsrg-special-meeting-attachment-agreed-upon-settings-capabilities-operational-modes/download

The searchable copy explicitly reports the four frequency trip settings, including UF2 = 56.5 Hz. The separate ride-through boundary of 57.0 Hz is not the UF2 shall-trip setting and must not be substituted for it.

## Return-to-service values — T1-009 and T1-010

The benchmark values are:

- enter-service delay = 300 s
- enter-service duration/ramp time = 300 s

The Massachusetts source remains the benchmark citation:
https://www.mass.gov/doc/tsrg-meeting-31-attachment-default-new-england-bulk-system-area-settings-requirement/download

A publicly indexed manufacturer grid-protection table independently corroborates ISO-NE-2021 values of 300 s for both enter-service delay and ramp time. This is corroboration only; the benchmark continues to cite the Massachusetts/ISO-NE source.

## OSHA minimum approach distances — T1-011 to T1-028

Verified against the current OSHA 29 CFR 1910.269 page:
https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.269

Table R-6 values used by the benchmark are verified for:
- 0.301–0.750 kV: 0.33 / 0.33 m
- 0.751–5.0 kV: 0.63 / 0.63 m
- 5.1–15.0 kV: 0.65 / 0.68 m
- 15.1–36.0 kV: 0.77 / 0.89 m
- 36.1–46.0 kV: 0.84 / 0.98 m
- 46.1–72.5 kV: 1.00 / 1.20 m

Table R-7 values used by the benchmark are verified for:
- 72.6–121.0 kV: 1.13 / 1.42 m
- 121.1–145.0 kV: 1.30 / 1.64 m
- 145.1–169.0 kV: 1.46 / 1.94 m

Each pair is phase-to-ground / phase-to-phase. The benchmark condition of worksite elevation at or below 900 m matches OSHA's table condition.

## NERC PRC-024-3 frequency boundary points — T1-029 to T1-035

Verified against NERC PRC-024-3:
https://www.nerc.com/pa/Stand/Reliability%20Standards/PRC-024-3.pdf

Western Interconnection points used:
- >=61.6 Hz -> 30 s
- >=60.6 Hz -> 180 s
- <=57.3 Hz -> 0.75 s
- <=57.8 Hz -> 7.5 s
- <=58.4 Hz -> 30 s
- <=59.4 Hz -> 180 s

ERCOT point used:
- >=60.6 Hz -> 540 s

The benchmark correctly treats these as **minimum no-trip times at the named boundary**, not as universal relay-setting prescriptions.

## Audit conclusion

All 35 Tier-1 target values are source-supported or source-supported with independent corroboration as documented above.

This audit verifies transcription and interpretation of the public facts. It does not replace the independent power-engineer plausibility review of the benchmark as a whole, especially Tier 2 synthetic asset values and the Tier 3 conflict design.
