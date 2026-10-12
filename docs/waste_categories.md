# PPC Waste Leak Taxonomy & Detection Mechanics

`ppc-waste-detector` identifies six distinct budget waste categories across search and display advertising networks. This guide breaks down each leak type, its economic impact, and the algorithmic threshold used for detection.

---

## 1. Search Query Bleed (`search_query_bleed`)
- **Category Description**: Non-converting or low-intent search queries triggered by broad match or phrase match keywords that consume budget without generating conversions.
- **Root Cause**: Overly broad keyword match types, aggressive smart bidding exploration, or insufficient negative keyword lists.
- **Detection Logic**:
  - Triggers on negative intent keywords (e.g., `free`, `torrent`, `salary`, `jobs`, `login`, `cracked`, `portal`, `tutorial`, `diy`, `pdf`).
  - Flags queries with high spend and zero conversions:
    $$\text{Spend} \ge \text{cost\_threshold} \quad \text{AND} \quad \text{Conversions} = 0$$
  - Flags queries with high click volume and zero conversions:
    $$\text{Clicks} \ge \text{clicks\_threshold} \quad \text{AND} \quad \text{Conversions} = 0$$
- **Remediation**:
  - Add search term to exact negative keyword list at campaign or ad group level.
  - Review matching broad keyword for semantic drift.

---

## 2. Keyword Cannibalization (`keyword_cannibalization`)
- **Category Description**: Multiple campaigns or ad groups actively bidding on the same search queries, triggering internal auction competition and artificially inflating CPCs.
- **Root Cause**: Overlapping geo-targets, mixed match types across campaigns, or fragmented ad group structures.
- **Detection Logic**:
  - Groups performance by normalized query string across distinct campaigns and ad groups.
  - Flags any query appearing in $\ge 2$ campaigns or ad groups where total spend $\ge \$20.00$.
  - Calculates wasted spend as total combined spend minus the highest-converting campaign's spend.
- **Remediation**:
  - Consolidate keywords into a single campaign using ad group theme segmentation.
  - Add campaign-level cross-negatives to route traffic to the intended ad group.

---

## 3. Junk Placement Leak (`junk_placement_leak`)
- **Category Description**: Budget drain on mobile gaming apps, click-farm domains, and MFA (Made-For-Advertising) websites on the Google Display Network (GDN) and Performance Max (PMax).
- **Root Cause**: Default network expansion settings ("Include Google Display Network") on Search campaigns or unconstrained PMax placement serving.
- **Detection Logic**:
  - Matches placement domains and app IDs against known junk patterns (`.xyz`, `.top`, `.online`, `anonymous.google`, `mobileapp::*`, `game*`, `kids*`, `arcade*`).
  - Flags placements with high click volume/cost and CTR anomalies ($> 8.0\%$ CTR with zero conversions indicates accidental or fraudulent taps).
- **Remediation**:
  - Exclude `mobileapp::*` placements account-wide.
  - Add domain placement exclusions at the account/MCC level.

---

## 4. Geographic Bleed (`geo_bleed`)
- **Category Description**: Ad spend recorded in locations outside the advertiser's designated service area or target market.
- **Root Cause**: Google Ads default location option: *"Presence or interest: People in, regularly in, or who've shown interest in your targeted locations"*.
- **Detection Logic**:
  - Cross-references impression and click geo-tags against configured target region codes and country whitelist.
  - Flags all non-zero spend originating from unapproved locations.
- **Remediation**:
  - Change location setting to *"Presence: People in or regularly in your targeted locations"*.
  - Add explicit country and territory negative location exclusions.

---

## 5. Dayparting Waste (`dayparting_waste`)
- **Category Description**: Costly ad impressions and clicks during off-hours (e.g., 1:00 AM - 5:00 AM) when call centers are closed, lead response times are nil, or buyer purchase propensity is negligible.
- **Root Cause**: 24/7 continuous ad delivery without hour-of-day bid adjustments or conversion window alignment.
- **Detection Logic**:
  - Analyzes hourly performance distributions.
  - Flags hours where average cost exceeds threshold but conversion rate is less than $10\%$ of account average.
- **Remediation**:
  - Implement custom ad schedules.
  - Apply negative bid adjustments ($-50\%$ to $-100\%$) during non-operating hours.

---

## 6. Smart Bidding Runaway (`smart_bidding_runaway`)
- **Category Description**: Severe CPC inflation driven by automated bidding algorithms (Target CPA, Max Conversions, Target ROAS) pursuing spurious signals or unconstrained by bid caps.
- **Root Cause**: Bidding algorithms aggressively bidding during conversion volume dips or unconstrained portfolio bidding strategies.
- **Detection Logic**:
  - Flags search terms or placement entities where average CPC exceeds $3.0\times$ the account median CPC without a corresponding increase in conversion value or ROAS.
- **Remediation**:
  - Set a portfolio target bid ceiling (Max CPC limit).
  - Reset learning phase or audit conversion tag reliability.
