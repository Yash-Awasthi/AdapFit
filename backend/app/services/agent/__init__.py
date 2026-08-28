# Lazy imports to avoid circular dependencies
agent_orchestrator = None
evolution_engine = None
supervisor_agent = None

def _get_orchestrator():
    global agent_orchestrator
    if agent_orchestrator is None:
        from app.services.agent.orchestrator import AgentOrchestrator
        agent_orchestrator = AgentOrchestrator()
    return agent_orchestrator

def _get_evolution():
    global evolution_engine
    if evolution_engine is None:
        from app.services.agent.evolution_engine import EvolutionEngine
        evolution_engine = EvolutionEngine()
    return evolution_engine

def _get_supervisor():
    global supervisor_agent
    if supervisor_agent is None:
        from app.services.agent.supervisor import SupervisorAgent
        supervisor_agent = SupervisorAgent()
    return supervisor_agent
