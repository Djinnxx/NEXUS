"""
Builds an entity-relationship graph from collected OSINT data.
Nodes = discovered entities (IPs, domains, emails, usernames …).
Edges = relationships between them.
"""

import networkx as nx
from .base import ScanWorker

# Node colours per entity type
NODE_COLORS = {
    "target":   "#e94560",
    "ip":       "#0f3460",
    "domain":   "#533483",
    "email":    "#0099cc",
    "username": "#00b894",
    "service":  "#fdcb6e",
    "darkweb":  "#2d3436",
    "ioc":      "#d63031",
    "default":  "#636e72",
}


def build_graph(target: str, all_results: dict) -> nx.DiGraph:
    """
    Build a directed graph from aggregated scan results.

    all_results = {
        "ip":       { "data": { "geo": {...} }, ... },
        "whois":    { "data": { "whois": {...} }, ... },
        "dns":      { "data": { "records": {...}, "subdomains": [...] }, ... },
        ...
    }
    """
    G = nx.DiGraph()
    G.add_node(target, label=target, entity_type="target", color=NODE_COLORS["target"])

    def add_node(name, etype):
        if not G.has_node(name):
            G.add_node(name, label=name, entity_type=etype,
                       color=NODE_COLORS.get(etype, NODE_COLORS["default"]))
        G.add_edge(target, name)

    # IPs from geo
    ip_data = all_results.get("ip", {}).get("data", {}).get("geo", {})
    if ip_data.get("ip"):
        add_node(ip_data["ip"], "ip")
        if ip_data.get("isp"):
            isp = ip_data["isp"][:30]
            G.add_node(isp, label=isp, entity_type="service",
                       color=NODE_COLORS["service"])
            G.add_edge(ip_data["ip"], isp)

    # Subdomains from DNS
    subs = all_results.get("dns", {}).get("data", {}).get("subdomains", [])
    for s in subs[:20]:
        add_node(s["subdomain"], "domain")
        for ip in s.get("ips", [])[:2]:
            G.add_node(ip, label=ip, entity_type="ip", color=NODE_COLORS["ip"])
            G.add_edge(s["subdomain"], ip)

    # Domains from cert transparency
    cert_domains = all_results.get("cert", {}).get("data", {}).get("unique_domains", [])
    for d in cert_domains[:15]:
        add_node(d, "domain")

    # Emails from WHOIS / breach
    whois_data = all_results.get("whois", {}).get("data", {}).get("whois", {})
    if whois_data.get("emails") and whois_data["emails"] != "N/A":
        for e in whois_data["emails"].split(", ")[:5]:
            add_node(e.strip(), "email")

    # Usernames
    found_profiles = all_results.get("username", {}).get("data", {}).get("found", [])
    for p in found_profiles[:10]:
        add_node(p["platform"], "username")

    # Dark web mentions
    dw_results = all_results.get("darkweb", {}).get("data", {}).get("results", [])
    for r in dw_results[:5]:
        label = r.get("title", r.get("onion", "unknown"))[:40]
        G.add_node(label, label=label, entity_type="darkweb",
                   color=NODE_COLORS["darkweb"])
        G.add_edge(target, label)

    # IOCs
    ioc_threats = all_results.get("ioc", {}).get("data", {}).get("threats", [])
    for t in ioc_threats[:5]:
        label = t.get("malware", t.get("source", "IOC"))[:30]
        G.add_node(label, label=label, entity_type="ioc", color=NODE_COLORS["ioc"])
        G.add_edge(target, label)

    return G


def run_scan(target: str, all_results: dict = None, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    G      = build_graph(target, all_results or {})

    result["data"]["graph"]    = G
    result["data"]["nodes"]    = G.number_of_nodes()
    result["data"]["edges"]    = G.number_of_edges()
    result["data"]["node_list"] = [
        {"id": n, **d} for n, d in G.nodes(data=True)
    ]

    result["findings"].append(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    for n in list(G.nodes())[:20]:
        result["findings"].append(f"  Node: {n}")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log("Building relationship map…", "INFO")
        self.progress.emit(30)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Map ready – {result['data']['nodes']} entities", "SUCCESS")
        self.result_ready.emit(result)
