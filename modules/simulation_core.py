"""Core urban traffic simulation with adaptive feedback and dynamic events."""
import random
import networkx as nx
import numpy as np


class TrafficNetwork:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.graph = nx.DiGraph()
        self.time_step = 0
        self.history = []
        self.event_log = []
        self.shock_events = []
        self.adaptive_memory = []
        self.active_events = {}
        self.closed_edges = set()
        self.last_signal_plan = {}

    def build_default_network(self, num_intersections: int = 6):
        num_intersections = max(4, min(8, num_intersections))
        coords = self._grid_coords(num_intersections)
        for i in range(num_intersections):
            self.graph.add_node(
                i, name=f"Intersection-{i}", lat=coords[i][0], lon=coords[i][1],
                signal_phase="NS_GREEN", green_duration=30, pedestrian_wait=0,
                pedestrian_crossing_demand=0.0,
            )
        edges = []
        for i in range(num_intersections):
            j = (i + 1) % num_intersections
            edges += [(i, j), (j, i)]
        if num_intersections >= 5:
            edges += [(0, 2), (2, 0), (1, 4), (4, 1)]
        if num_intersections >= 7:
            edges += [(3, 6), (6, 3)]
        for u, v in edges:
            if self.graph.has_edge(u, v):
                continue
            length = round(self.rng.uniform(0.4, 2.0), 2)
            speed_limit = self.rng.choice([40, 50, 60])
            capacity = self.rng.randint(40, 90)
            self.graph.add_edge(
                u, v, length=length, speed_limit=speed_limit, capacity=capacity,
                vehicle_count=self.rng.randint(0, capacity // 3),
                queue_length=self.rng.randint(0, 5), avg_speed=speed_limit * 0.8,
                free_flow_time=length / speed_limit * 60, weight=length / speed_limit * 60,
                density=0.0, level="GREEN", incident=False, closed=False,
                incident_penalty=0.0,
            )
        self._record_snapshot()
        return self.graph

    def _grid_coords(self, n):
        base_lat, base_lon = 11.1085, 77.3411
        layout = [(0, 0), (1, 0), (2, 0.3), (2.2, 1.2), (1.1, 1.6), (0, 1.3), (-0.6, 0.6), (1.4, -0.8)]
        return [(base_lat + layout[i][1] * 0.01, base_lon + layout[i][0] * 0.01) for i in range(n)]

    def set_signal_plan(self, durations):
        self.last_signal_plan = dict(durations)
        for node, duration in durations.items():
            if node in self.graph.nodes:
                d = int(max(15, min(90, duration)))
                self.graph.nodes[node]["green_duration"] = d
                self.graph.nodes[node]["signal_phase"] = "NS_GREEN" if d >= 35 else "EW_GREEN"

    def step(self, arrival_rate: float = 0.6, dt_minutes: float = 1.0, pedestrian_intensity: float = 0.35):
        self.time_step += 1
        pedestrian_intensity = float(max(0.0, min(1.0, pedestrian_intensity)))
        for node in self.graph.nodes:
            # Pedestrian demand is modeled at intersections and influences available vehicle service time.
            demand = pedestrian_intensity
            if self.graph.nodes[node].get("pedestrian_surge", False):
                demand = max(demand, 0.85)
            self.graph.nodes[node]["pedestrian_crossing_demand"] = round(demand, 2)
            self.graph.nodes[node]["pedestrian_wait"] = int(2 + 10 * demand)

        for u, v, data in self.graph.edges(data=True):
            if data.get("closed"):
                data["vehicle_count"] = 0
                data["queue_length"] = min(60, data.get("queue_length", 0) + 1)
                continue
            capacity = data["capacity"]
            arrivals = self.np_rng.poisson(arrival_rate * capacity / 20)
            node_green = self.graph.nodes[v].get("green_duration", 30)
            green_factor = min(1.5, max(0.5, node_green / 30.0))
            pedestrian_demand = self.graph.nodes[v].get("pedestrian_crossing_demand", pedestrian_intensity)
            pedestrian_penalty = 1.0 + 0.35 * pedestrian_demand
            service_rate = max(2, int(capacity * 0.12 * green_factor / pedestrian_penalty))
            if self.graph.nodes[v].get("signal_phase") == "EMERGENCY_GREEN":
                service_rate = int(capacity * 0.22)
            departures = min(data["vehicle_count"], service_rate)
            new_count = max(0, min(capacity, data["vehicle_count"] + arrivals - departures))
            density = new_count / capacity
            if density >= 0.75:
                data["queue_length"] = min(60, data["queue_length"] + self.rng.randint(1, 3))
            elif density < 0.4:
                data["queue_length"] = max(0, data["queue_length"] - self.rng.randint(0, 2))
            else:
                data["queue_length"] = max(0, data["queue_length"] + self.rng.choice([-1, 0, 1]))
            data["vehicle_count"] = new_count
            data["avg_speed"] = max(5.0, data["speed_limit"] * (1 - 0.6 * density))

        self._expire_events()
        self._record_snapshot()

    def _expire_events(self):
        for event_id, event in list(self.active_events.items()):
            if self.time_step >= event["until"]:
                self.clear_event(event_id)

    def add_incident(self, u, v, severity=0.8, duration=6, close=False, label="Accident"):
        if not self.graph.has_edge(u, v):
            return False
        event_id = f"incident_{u}_{v}_{self.time_step}"
        d = self.graph.edges[u, v]
        d["incident"] = True
        d["incident_penalty"] = float(max(0.1, severity))
        d["closed"] = bool(close)
        if close:
            self.closed_edges.add((u, v))
        self.active_events[event_id] = {"u": u, "v": v, "until": self.time_step + max(1, duration), "label": label}
        self.event_log.append({"t": self.time_step, "event": label, "edge": f"{u}→{v}", "duration": duration})
        return event_id

    def clear_event(self, event_id):
        event = self.active_events.pop(event_id, None)
        if not event:
            return
        u, v = event["u"], event["v"]
        if self.graph.has_edge(u, v):
            d = self.graph.edges[u, v]
            d["incident"] = False
            d["incident_penalty"] = 0.0
            d["closed"] = False
        self.closed_edges.discard((u, v))

    def apply_scenario(self, scenario):
        if scenario == "Normal":
            return
        edges = list(self.graph.edges())
        if not edges:
            return
        if scenario == "Rush Hour":
            for u, v in edges:
                self.graph.edges[u, v]["queue_length"] = min(60, self.graph.edges[u, v]["queue_length"] + 5)
        elif scenario == "Heavy Rain":
            for u, v in edges:
                self.graph.edges[u, v]["speed_limit"] *= 0.72
        elif scenario == "Accident":
            u, v = max(edges, key=lambda e: self.graph.edges[e]["queue_length"])
            self.add_incident(u, v, severity=2.0, duration=8, close=False, label="Accident")
        elif scenario == "Road Closure":
            u, v = max(edges, key=lambda e: self.graph.edges[e]["vehicle_count"])
            self.add_incident(u, v, severity=3.0, duration=8, close=True, label="Road Closure")
        elif scenario == "Stadium Surge":
            for u, v in edges[:max(2, len(edges)//3)]:
                self.graph.edges[u, v]["vehicle_count"] = min(self.graph.edges[u, v]["capacity"], self.graph.edges[u, v]["vehicle_count"] + 10)
        elif scenario == "Pedestrian Surge":
            for n in self.graph.nodes:
                self.graph.nodes[n]["pedestrian_surge"] = True
                self.graph.nodes[n]["pedestrian_crossing_demand"] = 0.85
                self.graph.nodes[n]["pedestrian_wait"] = 11

    def record_adaptive_memory(self, result, before_queue, after_queue):
        improvement = before_queue - after_queue
        if result:
            self.adaptive_memory.append({
                "t": self.time_step,
                "improvement": round(improvement, 2),
                "priorities": dict(result.get("priorities", {})),
                "green_durations": dict(result.get("green_durations", {})),
            })
            self.adaptive_memory = self.adaptive_memory[-12:]

    def best_memory_plan(self):
        if not self.adaptive_memory:
            return None
        good = sorted(self.adaptive_memory, key=lambda x: x["improvement"], reverse=True)
        return good[0] if good else None

    def _record_snapshot(self):
        edges = list(self.graph.edges(data=True))
        total_vehicles = sum(d["vehicle_count"] for _, _, d in edges)
        total_queue = sum(d["queue_length"] for _, _, d in edges)
        avg_speed = float(np.mean([d["avg_speed"] for _, _, d in edges])) if edges else 0
        throughput = sum(min(d["vehicle_count"], int(d["capacity"] * 0.12)) for _, _, d in edges)
        avg_density = float(np.mean([d["vehicle_count"] / d["capacity"] for _, _, d in edges])) if edges else 0
        self.history.append({"t": self.time_step, "total_vehicles": total_vehicles, "total_queue": total_queue, "avg_speed": avg_speed, "throughput": throughput, "avg_density": avg_density})
        if len(self.history) > 120:
            self.history = self.history[-120:]

    def network_metrics(self):
        edges = list(self.graph.edges(data=True))
        delays = [d["free_flow_time"] * (1 + 0.15 * (d["queue_length"] ** 2)) - d["free_flow_time"] for _, _, d in edges]
        return {
            "avg_delay_min": float(np.mean(delays)) if delays else 0.0,
            "total_queue": sum(d["queue_length"] for _, _, d in edges),
            "total_vehicles": sum(d["vehicle_count"] for _, _, d in edges),
            "avg_density": float(np.mean([d["vehicle_count"] / d["capacity"] for _, _, d in edges])) if edges else 0,
        }

    def edge_table(self):
        rows = []
        for u, v, d in self.graph.edges(data=True):
            density = d["vehicle_count"] / d["capacity"]
            rows.append({"from": self.graph.nodes[u]["name"], "to": self.graph.nodes[v]["name"], "from_id": u, "to_id": v,
                         "vehicle_count": d["vehicle_count"], "capacity": d["capacity"], "queue_length": d["queue_length"],
                         "density": round(density, 2), "avg_speed": round(d["avg_speed"], 1), "length_km": d["length"],
                         "level": d.get("level", "GREEN"), "closed": d.get("closed", False), "incident": d.get("incident", False)})
        return rows
