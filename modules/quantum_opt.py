"""
quantum_opt.py
---------------
Formulates the traffic-signal timing problem as a QUBO and solves it
with QAOA (Qiskit) when available, falling back to a fast classical
simulated-annealing solver otherwise. This dual-path design is what
lets the dashboard show a genuine "Quantum vs Classical" comparison
even on machines/environments where a full quantum SDK stack isn't
installed or is too slow for a live demo.

QUBO objective (as specified):
    minimize   sum(queue_weight * queue_length_i * x_i)
             + sum(conflict_weight * conflict_ij * x_i * x_j)

x_i in {0,1} represents whether intersection i is given priority
(extended green) in this optimization round. Conflicting neighbors
(adjacent intersections that cannot both get priority, e.g. to avoid
grid-lock feeding each other) are penalized.
"""

import itertools
import numpy as np


# ----------------------------------------------------------------------
# QUBO construction
# ----------------------------------------------------------------------
def build_qubo(intersections, queue_lengths, conflicts, queue_weight=1.0, conflict_weight=5.0):
    """
    intersections : list of node ids, e.g. [0,1,2,3,4,5]
    queue_lengths : dict {node_id: total queue length at that intersection}
    conflicts     : list of (i, j) tuples that conflict (can't both be prioritized)
    Returns Q, a dict {(i,j): coefficient} representing the QUBO matrix
    (upper-triangular, i<=j).
    """
    idx = {node: k for k, node in enumerate(intersections)}
    n = len(intersections)
    Q = {}

    for node in intersections:
        i = idx[node]
        q = queue_lengths.get(node, 0)
        # Linear term: rewards prioritizing high-queue intersections
        # (negative coefficient because we MINIMIZE the QUBO but want
        # to prioritize / "turn on" high-queue nodes).
        Q[(i, i)] = Q.get((i, i), 0.0) - queue_weight * q

    for (a, b) in conflicts:
        if a not in idx or b not in idx:
            continue
        i, j = sorted((idx[a], idx[b]))
        if i == j:
            continue
        Q[(i, j)] = Q.get((i, j), 0.0) + conflict_weight

    return Q, idx


def qubo_energy(Q, x):
    """Evaluate the QUBO objective for a given binary vector x (list/array)."""
    e = 0.0
    for (i, j), coeff in Q.items():
        e += coeff * x[i] * x[j]
    return e


# ----------------------------------------------------------------------
# Classical fallback solver: simulated annealing (fast, deterministic seed)
# ----------------------------------------------------------------------
def classical_solve(Q, n, seed=7, iterations=2000):
    rng = np.random.default_rng(seed)
    x = rng.integers(0, 2, size=n).tolist()
    best_x, best_e = list(x), qubo_energy(Q, x)

    temp = 2.0
    cooling = 0.995
    for _ in range(iterations):
        flip = rng.integers(0, n)
        x_new = list(x)
        x_new[flip] = 1 - x_new[flip]
        e_new = qubo_energy(Q, x_new)
        delta = e_new - qubo_energy(Q, x)
        if delta < 0 or rng.random() < np.exp(-delta / max(temp, 1e-6)):
            x = x_new
            if e_new < best_e:
                best_x, best_e = list(x_new), e_new
        temp *= cooling

    return best_x, best_e


# ----------------------------------------------------------------------
# Quantum solver: QAOA via Qiskit (falls back automatically if unavailable)
# ----------------------------------------------------------------------
def quantum_solve(Q, n, reps=2, seed=7):
    """
    Attempts a real QAOA run using Qiskit + Qiskit Aer. If the quantum
    stack isn't installed, or the problem is too large for a snappy
    live demo, it transparently falls back to the classical solver but
    labels the result accordingly so the UI stays honest.
    """
    try:
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
        from qiskit_algorithms import QAOA
        from qiskit_algorithms.optimizers import COBYLA
        from qiskit.primitives import Sampler

        if n > 12:
            # Keep the live demo fast; QAOA simulation cost grows quickly.
            x, e = classical_solve(Q, n, seed=seed)
            return x, e, "classical_fallback_large_n"

        qp = QuadraticProgram()
        for i in range(n):
            qp.binary_var(name=f"x{i}")

        linear = {f"x{i}": Q.get((i, i), 0.0) for i in range(n)}
        quadratic = {}
        for (i, j), coeff in Q.items():
            if i != j:
                quadratic[(f"x{i}", f"x{j}")] = coeff

        qp.minimize(linear=linear, quadratic=quadratic)

        sampler = Sampler()
        qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=100), reps=reps)
        solver = MinimumEigenOptimizer(qaoa)
        result = solver.solve(qp)

        x = [int(round(v)) for v in result.x]
        e = float(result.fval)
        return x, e, "qaoa"

    except Exception:
        # Any missing package / backend issue -> classical fallback,
        # clearly labeled so the comparison chart stays truthful.
        x, e = classical_solve(Q, n, seed=seed)
        return x, e, "classical_fallback_no_quantum_stack"


# ----------------------------------------------------------------------
# High-level API used by the dashboard
# ----------------------------------------------------------------------
def optimize_signals(graph, queue_by_node, conflict_pairs, use_quantum=True):
    """
    queue_by_node: dict {node_id: aggregated incoming queue length}
    conflict_pairs: list of (i,j) node id pairs that conflict
    Returns a dict with priority assignments and green-duration suggestions.
    """
    nodes = list(graph.nodes)
    Q, idx = build_qubo(nodes, queue_by_node, conflict_pairs)
    n = len(nodes)

    if use_quantum:
        x, energy, method = quantum_solve(Q, n)
    else:
        x, energy = classical_solve(Q, n)
        method = "classical"

    rev_idx = {v: k for k, v in idx.items()}
    priorities = {rev_idx[i]: bool(x[i]) for i in range(n)}

    # Convert priority bits into suggested green durations (simple heuristic:
    # prioritized intersections with bigger queues get proportionally more
    # green time out of a fixed 90s cycle).
    base = 20
    extra_pool = 70
    prioritized_nodes = [node for node, p in priorities.items() if p]
    total_q = sum(queue_by_node.get(node, 0) for node in prioritized_nodes) or 1
    green_durations = {}
    for node in nodes:
        if priorities[node]:
            share = queue_by_node.get(node, 0) / total_q
            green_durations[node] = int(base + share * extra_pool)
        else:
            green_durations[node] = base

    max_q = max(queue_by_node.values()) if queue_by_node else 0
    reasons = {}
    for node in nodes:
        q = queue_by_node.get(node, 0)
        if priorities[node]:
            reasons[node] = f"Priority: queue pressure {q:.0f} vehicles" + (
                f" ({q/max_q*100:.0f}% of peak queue)" if max_q else ""
            )
        else:
            reasons[node] = f"Normal phase: queue pressure {q:.0f} vehicles"

    return {
        "priorities": priorities,
        "green_durations": green_durations,
        "energy": energy,
        "method": method,
        "reasons": reasons,
        "objective": "Minimize queue pressure + adjacent-intersection conflict penalty",
    }


def build_conflict_pairs(graph):
    """Adjacent intersections (connected by an edge) are treated as conflicting,
    since giving both extended green simultaneously can worsen downstream queues."""
    seen = set()
    pairs = []
    for u, v in graph.edges():
        key = tuple(sorted((u, v)))
        if key not in seen:
            seen.add(key)
            pairs.append(key)
    return pairs
