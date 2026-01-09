def simulate_sip_change(current_savings, target, years, roi):
    results = []

    for delta in [2000, 5000, 8000, 12000]:
        new_sip = current_savings + delta
        future_value = new_sip * 12 * years * (1 + roi/100)
        probability = min(100, (future_value / target) * 100)

        results.append({
            "additional_sip": delta,
            "new_probability": round(probability, 2)
        })

    return results