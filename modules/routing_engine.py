"""Dynamic Dijkstra routing and congestion-triggered rerouting."""
import networkx as nx

def shortest_path(graph, source, target, weight="weight"):
    try:
        path=nx.dijkstra_path(graph,source,target,weight=weight)
        return path,nx.dijkstra_path_length(graph,source,target,weight=weight)
    except nx.NetworkXNoPath:
        return None,float("inf")

def path_is_congested(graph,path,red_threshold=0.75):
    if not path:return False
    return any(graph.edges[u,v].get("closed",False) or graph.edges[u,v].get("density",0)>=red_threshold for u,v in zip(path[:-1],path[1:]))

def reroute_if_needed(graph,source,target,current_path,weight="weight"):
    if current_path and not path_is_congested(graph,current_path):
        cost=sum(graph.edges[u,v][weight] for u,v in zip(current_path[:-1],current_path[1:]))
        return current_path,cost,False
    path,cost=shortest_path(graph,source,target,weight)
    return path,cost,True

def all_pairs_congestion_report(graph,weight="weight"):
    nodes=list(graph.nodes); total=count=0.0
    for s in nodes:
        for t in nodes:
            if s==t:continue
            _,c=shortest_path(graph,s,t,weight)
            if c!=float("inf"): total+=c;count+=1
    return total/count if count else 0.0
