"""Simulated DuniaWallet agent (cash-in/cash-out) locations."""

from __future__ import annotations

from .models import AgentLocation


def _build_agent_locations() -> list[AgentLocation]:
    """Create agent location data across African cities and diaspora."""
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

        # === Lagos, Nigeria ===
        AgentLocation(
            id="agt_019", name="QuickCash Victoria Island",
            city="Lagos", neighborhood="Victoria Island", country="Nigeria",
            phone="+234 801 111 2222", hours="8am-8pm Mon-Sat",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_020", name="Ikeja Mall Agent Point",
            city="Lagos", neighborhood="Ikeja", country="Nigeria",
            phone="+234 802 222 3333", hours="9am-9pm Mon-Sun",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_021", name="Lekki Express Kiosk",
            city="Lagos", neighborhood="Lekki", country="Nigeria",
            phone="+234 803 333 4444", hours="7am-8pm Mon-Sat",
            services=("cash_in", "cash_out", "registration"),
        ),

        # === Accra, Ghana ===
        AgentLocation(
            id="agt_022", name="Osu MobileMoney Hub",
            city="Accra", neighborhood="Osu", country="Ghana",
            phone="+233 20 111 2222", hours="8am-7pm Mon-Sat",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_023", name="Makola Market Agent",
            city="Accra", neighborhood="Makola", country="Ghana",
            phone="+233 24 222 3333", hours="7am-6pm Mon-Sat",
            services=("cash_in", "cash_out"),
        ),

        # === Nairobi, Kenya ===
        AgentLocation(
            id="agt_024", name="Westlands Digital Hub",
            city="Nairobi", neighborhood="Westlands", country="Kenya",
            phone="+254 722 111 222", hours="8am-8pm Mon-Sat",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_025", name="CBD Money Centre",
            city="Nairobi", neighborhood="CBD", country="Kenya",
            phone="+254 733 222 333", hours="8am-6pm Mon-Fri",
            services=("cash_in", "cash_out"),
        ),
        AgentLocation(
            id="agt_026", name="Kibera Agent Point",
            city="Nairobi", neighborhood="Kibera", country="Kenya",
            phone="+254 722 333 444", hours="7am-9pm Mon-Sun",
            services=("cash_in", "cash_out", "registration"),
        ),

        # === Dar es Salaam, Tanzania ===
        AgentLocation(
            id="agt_027", name="Kariakoo Cash Point",
            city="Dar es Salaam", neighborhood="Kariakoo", country="Tanzania",
            phone="+255 712 111 222", hours="8am-7pm Mon-Sat",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_028", name="Msasani Agent Kiosk",
            city="Dar es Salaam", neighborhood="Msasani", country="Tanzania",
            phone="+255 754 222 333", hours="8am-8pm Mon-Sat",
            services=("cash_in", "cash_out"),
        ),

        # === Johannesburg, South Africa ===
        AgentLocation(
            id="agt_029", name="Sandton Money Transfer",
            city="Johannesburg", neighborhood="Sandton", country="South Africa",
            phone="+27 11 111 2222", hours="9am-5pm Mon-Fri",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_030", name="Soweto Cash Express",
            city="Johannesburg", neighborhood="Soweto", country="South Africa",
            phone="+27 11 222 3333", hours="8am-6pm Mon-Sat",
            services=("cash_in", "cash_out"),
        ),

        # === Casablanca, Morocco ===
        AgentLocation(
            id="agt_031", name="Casa Finance Centre",
            city="Casablanca", neighborhood="Maarif", country="Morocco",
            phone="+212 522 111 222", hours="9h-18h lun-ven",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_032", name="Medina Exchange Point",
            city="Casablanca", neighborhood="Ancienne Medina", country="Morocco",
            phone="+212 522 222 333", hours="8h-20h lun-sam",
            services=("cash_in", "cash_out"),
        ),

        # === Cairo, Egypt ===
        AgentLocation(
            id="agt_033", name="Zamalek Money Hub",
            city="Cairo", neighborhood="Zamalek", country="Egypt",
            phone="+20 2 111 2222", hours="9am-6pm Sun-Thu",
            services=("cash_in", "cash_out", "registration"),
        ),
        AgentLocation(
            id="agt_034", name="Nasr City Agent",
            city="Cairo", neighborhood="Nasr City", country="Egypt",
            phone="+20 2 222 3333", hours="10am-8pm Sun-Thu",
            services=("cash_in", "cash_out"),
        ),

        # === London, United Kingdom ===
        AgentLocation(
            id="agt_035", name="Peckham Remittance Centre",
            city="London", neighborhood="Peckham", country="United Kingdom",
            phone="+44 20 7111 2222", hours="9am-6pm Mon-Sat",
            services=("cash_in", "registration"),
        ),
        AgentLocation(
            id="agt_036", name="Brixton Transfer Hub",
            city="London", neighborhood="Brixton", country="United Kingdom",
            phone="+44 20 7222 3333", hours="10am-7pm Mon-Sat",
            services=("cash_in", "registration"),
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
