"""Environmental KPIs and real strategy/scenario simulations."""
import numpy as np
from .simulation_core import TrafficNetwork
from .congestion_detector import update_edge_weights
from .quantum_opt import optimize_signals, build_conflict_pairs

EMISSION_FACTOR=0.21; IDLE_FACTOR=0.045; FUEL_PER_KM=0.08; FUEL_IDLE_PER_MIN=0.02

def environmental_impact(edge_table):
    distance=sum(e["length_km"]*max(1,e["vehicle_count"]) for e in edge_table)
    idle=sum(e["queue_length"] for e in edge_table)
    return {"co2_kg":round(distance*EMISSION_FACTOR+idle*IDLE_FACTOR,2),"fuel_liters":round(distance*FUEL_PER_KM+idle*FUEL_IDLE_PER_MIN,2),"avg_wait_vehicles_queued":round(float(np.mean([e["queue_length"] for e in edge_table])) if edge_table else 0,2),"throughput":sum(min(e["vehicle_count"],int(e["capacity"]*.12)) for e in edge_table)}

def _metrics(net):
    update_edge_weights(net.graph); env=environmental_impact(net.edge_table()); m=net.network_metrics()
    return {"waiting_time":round(m["avg_delay_min"],2),"queue_length":round(m["total_queue"],2),"throughput":round(env["throughput"],2),"travel_time_min":round(m["avg_delay_min"],2),"fuel_liters":env["fuel_liters"],"co2_kg":env["co2_kg"]}

def run_strategy(strategy,steps=16,seed=77,arrival_rate=.6,use_quantum=True,scenario="Normal",pedestrian_intensity=.35):
    net=TrafficNetwork(seed=seed);net.build_default_network(6);net.apply_scenario(scenario)
    for _ in range(steps):
        update_edge_weights(net.graph)
        if strategy=="Classical Adaptive Control":
            plan={n:max(20,min(70,20+sum(d["queue_length"] for _,_,d in net.graph.in_edges(n,data=True)))) for n in net.graph.nodes}
            net.set_signal_plan(plan)
        elif strategy=="QuantumFlow Hybrid":
            q={n:sum(d["queue_length"] for _,_,d in net.graph.in_edges(n,data=True)) for n in net.graph.nodes}
            qr=optimize_signals(net.graph,q,build_conflict_pairs(net.graph),use_quantum=use_quantum)
            net.set_signal_plan(qr["green_durations"])
        else:
            net.set_signal_plan({n:30 for n in net.graph.nodes})
        net.step(arrival_rate=arrival_rate,pedestrian_intensity=pedestrian_intensity)
    return _metrics(net)

def comparison_table(*args,**kwargs):
    steps=kwargs.get("steps",12);use_quantum=kwargs.get("use_quantum",True);scenario=kwargs.get("scenario","Normal");pedestrian_intensity=kwargs.get("pedestrian_intensity",.35)
    rows=[]
    for s in ["Fixed Signal Timing","Classical Adaptive Control","QuantumFlow Hybrid"]:
        r=run_strategy(s,steps=steps,seed=77,arrival_rate=.6,use_quantum=use_quantum,scenario=scenario,pedestrian_intensity=pedestrian_intensity);r["strategy"]=s;rows.append(r)
    return rows

def scenario_comparison(scenario,steps=12,use_quantum=True):
    return comparison_table(steps=steps,use_quantum=use_quantum,scenario=scenario)
