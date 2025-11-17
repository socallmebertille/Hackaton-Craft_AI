"""
Stockage en mémoire pour les débats

NOTE: En production, remplacer par une vraie base de données (PostgreSQL, MongoDB, etc.)
"""
from typing import Dict

# Dict qui stocke les débats en cours et terminés
# Structure: {debate_id: {question, status, results, ...}}
debates_storage: Dict[str, Dict] = {}
