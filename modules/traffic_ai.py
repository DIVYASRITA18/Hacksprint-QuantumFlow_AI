"""Offline Traffic Copilot for QuantumFlow AI.

No external AI service, API key, network request, or cloud model is used.
All insights are generated from the current local simulation state.
"""

def _local_fallback(metrics, bottlenecks=None, quantum_result=None, scenario="Normal"):
    bottlenecks = bottlenecks or []
    quantum_result = quantum_result or {}
    lines = [
        f"- Network density: {metrics.get('avg_density', 0)*100:.0f}%.",
        f"- Current queue: {metrics.get('total_queue', 0)} vehicles.",
        f"- Average delay: {metrics.get('avg_delay_min', 0):.1f} minutes.",
    ]
    if bottlenecks:
        b = bottlenecks[0]
        lines.append(f"- Main bottleneck: {b['from']} → {b['to']} at {b['density']*100:.0f}% density.")
    if quantum_result:
        lines.append(f"- Signal optimizer: {quantum_result.get('method', 'Hybrid')}; objective energy {quantum_result.get('energy', 0):.2f}.")
    if scenario != "Normal":
        lines.append(f"- Active scenario: {scenario}.")
    return "\n".join(lines)


def traffic_analyst(metrics, bottlenecks, *args, **kwargs):
    return _local_fallback(metrics, bottlenecks)


def optimization_advisor(quantum_result, metrics=None, *args, **kwargs):
    quantum_result = quantum_result or {}
    return (
        f"- Optimizer: {quantum_result.get('method', 'Hybrid')}.\n"
        f"- QUBO energy: {quantum_result.get('energy', 0):.2f}.\n"
        "- Signal priorities are selected from the current simulated traffic state."
    )


def emergency_response_assistant(status, *args, **kwargs):
    if not status.get("active"):
        return "- No active emergency corridor.\n- Normal signal coordination can continue."
    return f"- Emergency corridor active across {len(status.get('path', []))} intersections.\n- Priority signals are being coordinated along the emergency route."


def smart_city_report(metrics, env, quantum_result, *args, **kwargs):
    return _local_fallback(metrics, quantum_result=quantum_result) + (
        f"\n- Estimated fuel: {env.get('fuel_liters', 0):.2f} L."
        f"\n- Estimated CO₂: {env.get('co2_kg', 0):.2f} kg."
    )


def copilot(metrics, bottlenecks, quantum_result, scenario, *args, **kwargs):
    return _local_fallback(metrics, bottlenecks, quantum_result, scenario)
