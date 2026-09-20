"""Emergency green-corridor controller with restoration."""
import networkx as nx

class EmergencyCorridor:
    def __init__(self):
        self.active=False; self.path=[]; self.source=None; self.target=None; self.travel_time_saved=0.0; self.original={}

    def dispatch(self,graph,source,target,weight="weight"):
        try: normal=nx.dijkstra_path_length(graph,source,target,weight=weight)
        except nx.NetworkXNoPath: normal=None
        try:
            path=nx.dijkstra_path(graph,source,target,weight="free_flow_time")
            emergency=nx.dijkstra_path_length(graph,source,target,weight="free_flow_time")
        except nx.NetworkXNoPath:
            return {"success":False,"message":"No route found."}
        if self.active:self.clear(graph)
        self.active=True;self.path=path;self.source=source;self.target=target
        self.travel_time_saved=max(0.0,(normal if normal is not None else emergency)-emergency)
        self.original={}
        for u,v in zip(path[:-1],path[1:]):
            d=graph.edges[u,v];self.original[(u,v)]={"queue":d["queue_length"],"weight":d.get("weight")}
            d["queue_length"]=0;d["weight"]=d["free_flow_time"];d["emergency_corridor"]=True
        for n in path:
            graph.nodes[n]["signal_phase"]="EMERGENCY_GREEN"
            graph.nodes[n]["green_duration"]=90
        return {"success":True,"path":path,"normal_time_min":round(normal,2) if normal is not None else None,"emergency_time_min":round(emergency,2),"time_saved_min":round(self.travel_time_saved,2)}

    def clear(self,graph):
        for (u,v),old in self.original.items():
            if graph.has_edge(u,v):
                graph.edges[u,v]["queue_length"]=old["queue"]
                graph.edges[u,v]["emergency_corridor"]=False
        for n in self.path:
            if n in graph.nodes:
                graph.nodes[n]["signal_phase"]="NS_GREEN";graph.nodes[n]["green_duration"]=30
        self.active=False;self.path=[];self.original={}

    def status(self):
        return {"active":self.active,"path":self.path,"time_saved_min":round(self.travel_time_saved,2) if self.active else 0.0}
