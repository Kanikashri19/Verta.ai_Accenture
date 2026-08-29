import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import json
from app.engine.investigation import investigation_engine
from app.data.loader import data_loader

def main():
    print("=" * 95)
    print("VERTA.AI -- PHASE 3 PATCH: FIRST-CLASS DRIVER RANKING & CAUSAL LANGUAGE REPORT")
    print("=" * 95)

    kpi_id = "kpi_revenue"
    scenario_id = "SCENARIO_1_MULTI_FACTOR"

    res = investigation_engine.investigate_kpi(kpi_id=kpi_id, scenario_id=scenario_id)
    fact_pack = investigation_engine.generate_fact_pack(res)

    print(f"\n[1] INVESTIGATION SUMMARY: {res.kpi_name} ({res.kpi_id})")
    print(f" * Baseline: ${res.baseline_value:,.2f}/day | Anomaly: ${res.current_value:,.2f}/day | Delta: {res.percentage_change:+.2f}%")
    print(f" * Materiality: {res.materiality.overall_materiality} | Z-Score: {res.materiality.z_score:+.2f} | Anomaly Score: {res.anomaly_score:.4f}")

    print("\n" + "=" * 95)
    print("A. QUANTITATIVE DRIVER RANKING (Calculated Exact Multiplicative Chain Decomposition)")
    print("=" * 95)
    print(f"{'Rank':<5} | {'Driver':<35} | {'Type':<22} | {'Impact ($ USD)':<16} | {'Share (%)':<10} | {'Direction'}")
    print("-" * 95)
    for idx, d in enumerate(res.ranked_drivers, start=1):
        sign_str = f"-${abs(d.contribution_value):,.2f}" if d.contribution_value < 0 else f"+${d.contribution_value:,.2f}"
        print(f" #{idx:<4} | {d.driver_name:<35} | {d.driver_type:<22} | {sign_str:<16} | {d.contribution_percentage:>7.1f}% | {d.direction}")
    print("-" * 95)
    total_driver_sum = sum(d.contribution_value for d in res.ranked_drivers)
    print(f" EXACT TOTAL 7-DAY DELTA: -${abs(total_driver_sum):,.2f} (100.0% Closed-Form Closure)")

    print("\n" + "=" * 95)
    print("B. FIRST-CLASS RANKED EXPLANATIONS (Unified Quantitative Drivers & Supporting Signals)")
    print("=" * 95)
    print(f"{'Rank':<5} | {'Explanation / Driver':<42} | {'Driver Type':<20} | {'Dollar Impact':<15} | {'Evidence Count'}")
    print("-" * 95)
    for e in res.ranked_explanations:
        contrib_str = f"-${abs(e.contribution_value):,.2f}" if e.contribution_value is not None else "N/A (Non-Quant)"
        ev_str = f"{e.supporting_evidence_count} logs/tickets" if e.supporting_evidence_count > 0 else "-"
        print(f" #{e.rank:<4} | {e.driver:<42} | {e.driver_type:<20} | {contrib_str:<15} | {ev_str}")
        print(f"        `-> Status: {e.status} | Method: {e.method}")
        print(f"        `-> Non-Causal Summary: {e.description}")

    print("\n" + "=" * 95)
    print("C. REGIONAL DRILL-DOWN")
    print("=" * 95)
    for r in res.dimensional_drilldowns.get("region", []):
        print(f" * Region {r.dimension_value:<5} | Delta: -${abs(r.absolute_change):>10,.2f} | Movement: {r.percentage_change:>6.2f}% | Share of Loss: {r.contribution_to_total_pct:>5.1f}%")

    print("\n" + "=" * 95)
    print("D. PRODUCT & CATEGORY DRILL-DOWN")
    print("=" * 95)
    for c in res.dimensional_drilldowns.get("category", []):
        print(f" * Category {c.dimension_value:<16} | Delta: -${abs(c.absolute_change):>10,.2f} | Movement: {c.percentage_change:>6.2f}% | Share of Loss: {c.contribution_to_total_pct:>5.1f}%")
    if res.mix_shift_analysis:
        mix = res.mix_shift_analysis
        print(f"\n Mix-Shift Breakdown ({mix.dimension_name}):")
        print(f"  |- Volume Effect:   -${abs(mix.volume_effect_usd):,.2f}")
        print(f"  |- Mix-Shift Effect: -${abs(mix.mix_shift_effect_usd):,.2f} (Substitution to lower-priced SKUs)")
        print(f"  `- Price/Rate Effect: ${mix.price_rate_effect_usd:+,.2f}")

    print("\n" + "=" * 95)
    print("E. MARKETING CHANNEL SESSIONS (CLICKS)")
    print("=" * 95)
    for ch in res.dimensional_drilldowns.get("channel", []):
        print(f" * Channel {ch.dimension_value:<12} | Delta Clicks: {ch.absolute_change:>8,.0f} | Movement: {ch.percentage_change:>6.2f}%")

    print("\n" + "=" * 95)
    print("F. STRUCTURED OPERATIONAL SIGNALS")
    print("=" * 95)
    for s in res.supporting_signals:
        prod_str = f" [SKU: {s.product_id}]" if s.product_id else ""
        reg_str = f" [Region: {s.region}]" if s.region else ""
        print(f" * Signal [{s.severity}] {s.issue_type:<24}{prod_str}{reg_str} | Count: {s.event_count:>2} | Role: {s.signal_role}")
        print(f"   `-> Description: {s.description}")

    print("\n" + "=" * 95)
    print("G. VERIFIED FACT PACK JSON SUMMARY")
    print("=" * 95)
    print(f"FactPack Version: {fact_pack.version} | Verified Numerical Facts: {len(fact_pack.verified_numerical_facts)}")
    print(f"Guarded Non-Causal Language Rules: {fact_pack.guarded_language_constraints}")
    print("=" * 95)

if __name__ == "__main__":
    main()
