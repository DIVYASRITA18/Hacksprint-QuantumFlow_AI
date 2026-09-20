"""Congestion, bottleneck and sudden-traffic-shock detection."""

def classify_density(density):
    if density < 0.4: return "GREEN"
    if density < 0.75: return "YELLOW"
    return "RED"

def dynamic_cost(free_flow_time, queue_length, incident_penalty=0.0, closed=False):
    if closed: return 1e9
    return free_flow_time * (1 + 0.15 * (queue_length ** 2)) * (1 + incident_penalty)

def update_edge_weights(graph):
    levels = {"GREEN":0,"YELLOW":0,"RED":0}
    for u,v,d in graph.edges(data=True):
        density = d["vehicle_count"] / max(1,d["capacity"])
        d["density"] = density
        d["level"] = classify_density(density)
        d["weight"] = dynamic_cost(d["free_flow_time"], d["queue_length"], d.get("incident_penalty",0), d.get("closed",False))
        levels[d["level"]] += 1
    return levels

def find_bottlenecks(graph, top_n=3):
    rows=[]
    for u,v,d in graph.edges(data=True):
        rows.append({"from":graph.nodes[u]["name"],"to":graph.nodes[v]["name"],"density":d.get("density",0),"queue_length":d["queue_length"],"incident":d.get("incident",False),"closed":d.get("closed",False)})
    return sorted(rows,key=lambda x:(x["closed"],x["density"],x["queue_length"]),reverse=True)[:top_n]

def detect_traffic_shocks(graph, previous=None, threshold=0.18):
    current={}
    shocks=[]
    for u,v,d in graph.edges(data=True):
        key=(u,v); current[key]=d["vehicle_count"]
        if previous and key in previous:
            old=previous[key]
            change=(d["vehicle_count"]-old)/max(1,old)
            if abs(change)>=threshold:
                shocks.append({"edge":key,"from":graph.nodes[u]["name"],"to":graph.nodes[v]["name"],"change_pct":round(change*100,1),"direction":"surge" if change>0 else "drop"})
    shocks.sort(key=lambda x:abs(x["change_pct"]),reverse=True)
    return shocks,current
