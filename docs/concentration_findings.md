# Delivery concentration: initial evidence

Source: user-supplied screenshots of SQL Results 10 and 5, reviewed 30 October 2026. Screenshots show partial result sets; no claim is made about unseen rows. Historical Brazilian Olist data, 2016–2018. Region is customer state. Eligible delivered orders require both delivery dates. Overall late rate: 6,534 / 96,470, approximately 6.77%.

## Selected visible regional results
| Customer state | Eligible orders | Late orders | Late rate |
|---|---:|---:|---:|
| SP | 40,494 | 1,820 | 4.49% |
| RJ | 12,350 | 1,495 | 12.11% |
| MG | 11,354 | 519 | 4.57% |
| BA | 3,256 | 396 | 12.16% |
| RS | 5,344 | 325 | 6.08% |
| SC | 3,546 | 291 | 8.21% |
| ES | 1,995 | 214 | 10.73% |
| CE | 1,279 | 176 | 13.76% |
| MA | 717 | 125 | 17.43% |
| AL | 397 | 85 | 21.41% |

SP and RJ together account for 3,315 / 6,534, approximately 50.73% of late orders. They require different interpretations: SP has the highest observed late-order count but a below-overall rate; RJ combines substantial volume with an above-overall rate.

RJ's descriptive late count above the overall-rate benchmark is approximately 659 orders; BA's is approximately 176. These are arithmetic comparisons against the pooled rate, not estimates of preventable delays or intervention benefits. Geography, purchase month, seller and product mix may differ. AL and MA have high visible rates with lower volume; do not rank solely by rate. The region query excludes states with fewer than 100 eligible orders, so it is not a complete all-state rate ranking.

## Seller evidence
Result 5 ranks sellers with at least 100 eligible orders by late rate. The first visible seller has 389 eligible orders and 74 late orders, a 19.02% rate. This warrants investigation; it does not establish seller responsibility. The underlying delivery label applies to the whole order, including multi-seller orders. Export the full result to preserve exact seller identifiers and compare volume as well as rate. Do not sum seller late counts across sellers.

## Proposed case-study actions, pending further analysis
1. Prioritise a diagnostic review of RJ delivery routes, promise windows and seller mix, followed by BA. Test whether the pattern persists by purchase month and comparable seller/customer routes.
2. Maintain a volume-focused queue for SP: its large late count can matter operationally even with a below-overall rate. Avoid treating high volume as evidence of poor relative performance.
3. Review high-rate sellers with adequate samples, examining single-seller orders and shipment-stage timings before assigning responsibility. No staffing capacity or improvement target has been validated.

These actions are proposals, not measured operational outcomes. Reviews demonstrate association with delays, not causal effects. The dataset cannot supply a current live-order investigation queue; the later model will simulate approval-time prioritisation on historical held-out orders.

## Next evidence required
Export complete Results 2, 5, 6, 9 and 10 to CSV. Inspect monthly continuity, category patterns, response coverage and rankings before final recommendations or dashboard publication.
