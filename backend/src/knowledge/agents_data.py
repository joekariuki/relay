"""Simulated DuniaWallet agent (cash-in/cash-out) locations."""

from __future__ import annotations

from .models import AgentLocation


def _build_agent_locations() -> list[AgentLocation]:
    """Create agent location data across West African cities."""
    return [
        # === Dakar, Senegal ===
        AgentLocation(
            id="agt_001", name="Boutique Chez Moussa",
            city="Dakar", neighborhood="Medina", country="Senegal",
            phone="+221 77 111 2222", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_002", name="Kiosque DuniaWallet Plateau",
            city="Dakar", neighborhood="Plateau", country="Senegal",
            phone="+221 77 222 3333", hours="8h-19h lun-ven",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_003", name="Alimentation Ndiaye",
            city="Dakar", neighborhood="Parcelles Assainies", country="Senegal",
            phone="+221 78 333 4444", hours="7h-21h lun-dim",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_004", name="Telecentre Pikine",
            city="Dakar", neighborhood="Pikine", country="Senegal",
            phone="+221 77 444 5555", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_005", name="Station Total Ouakam",
            city="Dakar", neighborhood="Ouakam", country="Senegal",
            phone="+221 76 555 6666", hours="6h-22h lun-dim",
            services=("cash_in", "cash_out"),
        ),

        # === Bamako, Mali ===
        AgentLocation(
            id="agt_006", name="Boutique Traore Telecom",
            city="Bamako", neighborhood="Hamdallaye ACI 2000", country="Mali",
            phone="+223 66 111 2222", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_007", name="Kiosque Grand Marche",
            city="Bamako", neighborhood="Centre Commercial", country="Mali",
            phone="+223 79 222 3333", hours="7h-19h lun-sam",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_008", name="Cyber Cafe Badalabougou",
            city="Bamako", neighborhood="Badalabougou", country="Mali",
            phone="+223 66 333 4444", hours="8h-21h lun-dim",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_009", name="Pharmacie Kalaban Coura",
            city="Bamako", neighborhood="Kalaban Coura", country="Mali",
            phone="+223 79 444 5555", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out"),
        ),

        # === Abidjan, Cote d'Ivoire ===
        AgentLocation(
            id="agt_010", name="Boutique Mobile Plateau",
            city="Abidjan", neighborhood="Plateau", country="Cote d'Ivoire",
            phone="+225 07 111 2222", hours="8h-19h lun-ven",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_011", name="Kiosque Cocody Angre",
            city="Abidjan", neighborhood="Cocody", country="Cote d'Ivoire",
            phone="+225 05 222 3333", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_012", name="Centre Yopougon Marche",
            city="Abidjan", neighborhood="Yopougon", country="Cote d'Ivoire",
            phone="+225 07 333 4444", hours="7h-20h lun-dim",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_013", name="Superette Adjame",
            city="Abidjan", neighborhood="Adjame", country="Cote d'Ivoire",
            phone="+225 05 444 5555", hours="8h-21h lun-sam",
            services=("cash_in", "cash_out"),
        ),

        # === Ouagadougou, Burkina Faso ===
        AgentLocation(
            id="agt_014", name="Boutique Centrale Ouaga",
            city="Ouagadougou", neighborhood="Centre-ville", country="Burkina Faso",
            phone="+226 70 111 2222", hours="8h-19h lun-ven",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_015", name="Kiosque Ouaga 2000",
            city="Ouagadougou", neighborhood="Ouaga 2000", country="Burkina Faso",
            phone="+226 70 222 3333", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_016", name="Telecentre Dassasgho",
            city="Ouagadougou", neighborhood="Dassasgho", country="Burkina Faso",
            phone="+226 71 333 4444", hours="7h-20h lun-sam",
            services=("cash_in", "cash_out", "registration"),
        ),

        # === Other cities ===
        AgentLocation(
            id="agt_017", name="Boutique Saint-Louis Centre",
            city="Saint-Louis", neighborhood="Centre", country="Senegal",
            phone="+221 77 777 8888", hours="8h-19h lun-sam",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_018", name="Kiosque Bobo-Dioulasso",
            city="Bobo-Dioulasso", neighborhood="Marche Central", country="Burkina Faso",
            phone="+226 70 888 9999", hours="8h-18h lun-sam",
            services=("cash_in", "cash_out", "registration"),
        ),
    ]


AGENT_LOCATIONS: list[AgentLocation] = _build_agent_locations()


def find_agents(location: str) -> list[AgentLocation]:
    """Find agents matching a city, neighborhood, or country. Case-insensitive partial match."""
    query = location.lower().strip()
    results: list[AgentLocation] = []
    for agent in AGENT_LOCATIONS:
        if (
            query in agent.city.lower()
            or query in agent.neighborhood.lower()
            or query in agent.country.lower()
            or query in agent.name.lower()
        ):
            results.append(agent)
    return results
