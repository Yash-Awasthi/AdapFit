"""
Drug interaction network visualization and analysis.

Extracted from drug-interaction-dashboard — network graph patterns.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
import math


@dataclass
class DrugNode:
    id: str
    name: str
    mechanism: str = ""
    phase: str = ""
    approval_status: str = ""
    therapeutic_area: str = ""
    routes: List[str] = field(default_factory=list)
    properties: Dict[str, any] = field(default_factory=dict)


@dataclass
class InteractionEdge:
    source: str
    target: str
    severity: str  # MILD, MODERATE, SEVERE, CRITICAL
    interaction_type: str  # SYNERGISTIC, ANTAGONISTIC, ADDITIVE, NEUTRAL
    description: str = ""
    mechanism: str = ""


@dataclass
class NetworkGraph:
    nodes: Dict[str, DrugNode]
    edges: List[InteractionEdge]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def build_drug_network(drugs: List[DrugNode], interactions: List[InteractionEdge]) -> NetworkGraph:
    """Build a drug interaction network graph."""
    nodes = {drug.id: drug for drug in drugs}
    return NetworkGraph(nodes=nodes, edges=interactions)


def find_interactions(graph: NetworkGraph, drug_id: str) -> List[InteractionEdge]:
    """Find all interactions involving a specific drug."""
    return [
        e for e in graph.edges
        if e.source == drug_id or e.target == drug_id
    ]


def find_clusters(graph: NetworkGraph) -> List[Set[str]]:
    """Find connected components (drug clusters) in the network."""
    visited: Set[str] = set()
    clusters: List[Set[str]] = []

    for node_id in graph.nodes:
        if node_id not in visited:
            cluster: Set[str] = set()
            queue = [node_id]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                cluster.add(current)
                for edge in graph.edges:
                    neighbor = edge.target if edge.source == current else edge.source
                    if neighbor not in visited and neighbor in graph.nodes:
                        queue.append(neighbor)
            clusters.append(cluster)

    return clusters


def compute_drug_risk_score(graph: NetworkGraph, drug_id: str) -> float:
    """Compute a risk score for a drug based on its interactions."""
    interactions = find_interactions(graph, drug_id)
    if not interactions:
        return 0.0

    severity_weights = {"MILD": 0.1, "MODERATE": 0.3, "SEVERE": 0.7, "CRITICAL": 1.0}
    total_risk = sum(severity_weights.get(e.severity, 0.5) for e in interactions)
    return min(1.0, total_risk / len(interactions))


def find_high_risk_drugs(graph: NetworkGraph, threshold: float = 0.5) -> List[Tuple[str, float]]:
    """Find drugs with risk scores above threshold."""
    risks = []
    for drug_id in graph.nodes:
        score = compute_drug_risk_score(graph, drug_id)
        if score >= threshold:
            risks.append((drug_id, score))
    return sorted(risks, key=lambda x: x[1], reverse=True)


def shortest_path(
    graph: NetworkGraph, start: str, end: str
) -> Optional[List[str]]:
    """Find shortest path between two drugs in the interaction network."""
    if start not in graph.nodes or end not in graph.nodes:
        return None

    visited: Set[str] = {start}
    queue: List[List[str]] = [[start]]

    while queue:
        path = queue.pop(0)
        current = path[-1]

        if current == end:
            return path

        for edge in graph.edges:
            neighbor = edge.target if edge.source == current else edge.source
            if neighbor not in visited and neighbor in graph.nodes:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def compute_centrality(graph: NetworkGraph) -> Dict[str, float]:
    """Compute betweenness centrality approximation for each drug."""
    centrality = {node_id: 0.0 for node_id in graph.nodes}

    for source in graph.nodes:
        for target in graph.nodes:
            if source != target:
                path = shortest_path(graph, source, target)
                if path and len(path) > 2:
                    for intermediate in path[1:-1]:
                        centrality[intermediate] += 1.0

    max_val = max(centrality.values()) if centrality else 1.0
    if max_val > 0:
        centrality = {k: v / max_val for k, v in centrality.items()}

    return centrality


def suggest_safe_alternatives(
    graph: NetworkGraph, drug_id: str, existing_meds: List[str]
) -> List[str]:
    """Suggest drugs with no interactions with existing medications."""
    candidates = []
    for candidate_id in graph.nodes:
        if candidate_id == drug_id:
            continue
        has_interaction = False
        for med in existing_meds:
            if med == candidate_id:
                continue
            for edge in graph.edges:
                if (edge.source == candidate_id and edge.target == med) or \
                   (edge.source == med and edge.target == candidate_id):
                    if edge.severity in ("SEVERE", "CRITICAL"):
                        has_interaction = True
                        break
            if has_interaction:
                break
        if not has_interaction:
            candidates.append(candidate_id)

    return candidates
