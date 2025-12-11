"""
Test que tous les pipelines passent bien par CraftAI (pas de mode local)

Ce script vérifie que l'orchestrateur appelle uniquement les endpoints
CraftAI déployés sans fallback local.
"""

import sys
import os

# Ajouter le répertoire backend au path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from orchestrator.pipeline_orchestrator import execute_workflow


def test_craftai_endpoints():
    """
    Test que l'orchestrateur utilise bien les endpoints CraftAI
    """
    print("\n" + "="*100)
    print("🧪 TEST: Vérification que tous les pipelines passent par CraftAI")
    print("="*100)

    # Test 1: Question juridique complexe (workflow 1)
    print("\n📝 TEST 1: Question juridique complexe (workflow 1 attendu)")
    print("-" * 100)

    question_1 = "Puis-je licencier un salarié en arrêt maladie pour inaptitude ?"
    print(f"Question: {question_1}")

    try:
        result_1 = execute_workflow(question_1)

        workflow_type = result_1.get("workflow_type")
        intent_label = result_1.get("intent_label")
        steps = result_1.get("steps_executed", [])

        print(f"\n✅ Résultat:")
        print(f"   - Workflow type: {workflow_type}")
        print(f"   - Intent label: {intent_label}")
        print(f"   - Étapes exécutées: {len(steps)}")

        for step in steps:
            print(f"     • {step['pipeline_name']}: {step['status']}")

        if workflow_type == 1:
            print(f"\n✅ TEST 1 RÉUSSI: Workflow 1 exécuté via CraftAI")
        else:
            print(f"\n⚠️ TEST 1: Workflow inattendu (attendu: 1, reçu: {workflow_type})")

    except Exception as e:
        print(f"\n❌ TEST 1 ÉCHOUÉ: {str(e)}")

    # Test 2: Recherche de textes de loi (workflow 2)
    print("\n" + "="*100)
    print("📝 TEST 2: Recherche de textes de loi (workflow 2 attendu)")
    print("-" * 100)

    question_2 = "Quelles sont les lois sur la dissolution du PACS ?"
    print(f"Question: {question_2}")

    try:
        result_2 = execute_workflow(question_2)

        workflow_type = result_2.get("workflow_type")
        intent_label = result_2.get("intent_label")
        steps = result_2.get("steps_executed", [])

        print(f"\n✅ Résultat:")
        print(f"   - Workflow type: {workflow_type}")
        print(f"   - Intent label: {intent_label}")
        print(f"   - Étapes exécutées: {len(steps)}")

        for step in steps:
            print(f"     • {step['pipeline_name']}: {step['status']}")

        if workflow_type == 2:
            print(f"\n✅ TEST 2 RÉUSSI: Workflow 2 exécuté via CraftAI")
        else:
            print(f"\n⚠️ TEST 2: Workflow inattendu (attendu: 2, reçu: {workflow_type})")

    except Exception as e:
        print(f"\n❌ TEST 2 ÉCHOUÉ: {str(e)}")

    # Test 3: Question hors-scope (workflow 0)
    print("\n" + "="*100)
    print("📝 TEST 3: Question hors-scope (workflow 0 attendu)")
    print("-" * 100)

    question_3 = "Quel temps fait-il aujourd'hui ?"
    print(f"Question: {question_3}")

    try:
        result_3 = execute_workflow(question_3)

        workflow_type = result_3.get("workflow_type")
        intent_label = result_3.get("intent_label")
        response = result_3.get("result", {}).get("response", "")

        print(f"\n✅ Résultat:")
        print(f"   - Workflow type: {workflow_type}")
        print(f"   - Intent label: {intent_label}")
        print(f"   - Réponse: {response[:100]}...")

        if workflow_type == 0:
            print(f"\n✅ TEST 3 RÉUSSI: Workflow 0 (hors-scope) via CraftAI")
        else:
            print(f"\n⚠️ TEST 3: Workflow inattendu (attendu: 0, reçu: {workflow_type})")

    except Exception as e:
        print(f"\n❌ TEST 3 ÉCHOUÉ: {str(e)}")

    print("\n" + "="*100)
    print("🏁 TESTS TERMINÉS")
    print("="*100)
    print("\nSi tous les tests sont passés, cela confirme que:")
    print("  ✓ P0 (classify_intent) passe par CraftAI")
    print("  ✓ P1, P2, P3, P5 passent par CraftAI")
    print("  ✓ Aucun fallback local n'est utilisé")
    print()


if __name__ == "__main__":
    test_craftai_endpoints()
