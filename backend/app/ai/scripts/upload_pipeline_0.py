"""
Script pour uploader le Pipeline analyze_intent sur CraftAI
"""

import sys
import os
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, Input, Output


def main():
    print("=" * 80)
    print("Upload Pipeline - analyze_intent sur CraftAI")
    print("=" * 80)

    # Vérifier que les variables d'environnement sont définies
    if not os.getenv("CRAFT_AI_SDK_TOKEN"):
        print("❌ Erreur: CRAFT_AI_SDK_TOKEN n'est pas définie")
        return

    if not os.getenv("CRAFT_AI_ENVIRONMENT_URL"):
        print("❌ Erreur: CRAFT_AI_ENVIRONMENT_URL n'est pas définie")
        return

    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ Erreur: MISTRAL_API_KEY n'est pas définie")
        return

    # Initialiser le SDK CraftAI
    print("\n🔧 Initialisation du SDK CraftAI...")
    sdk = CraftAiSdk()

    # Définir les inputs et outputs
    message_input = Input(
        name="message",
        data_type="string",
        description="Message ou question de l'utilisateur"
    )

    result_output = Output(
        name="result",
        data_type="json",
        description="Analyse d'intention avec message, intention (DEBAT/CITATIONS/HORS_SUJET), confidence et reasoning"
    )

    # Déterminer le chemin du dossier ai
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ai_dir = os.path.dirname(script_dir)

    print(f"📁 Dossier AI: {ai_dir}")

    # Configuration du container
    container_config = {
        "local_folder": ai_dir,
        "language": "python:3.12-slim",
        "requirements_path": "requirements.txt",
        "included_folders": [
            "pipelines/analyze_intent.py",
            "services/mistral_service.py",
            "requirements.txt"
        ]
    }

    # Variables d'environnement pour le pipeline
    # Note: Les secrets doivent être configurés dans CraftAI après le déploiement
    environment_variables = {
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
        "MISTRAL_MODEL_SMALL": os.getenv("MISTRAL_MODEL_SMALL", "mistral-small-latest")
    }

    print(f"\n📤 Upload du pipeline...")

    try:
        # Supprimer l'ancien pipeline s'il existe
        try:
            sdk.delete_pipeline("analyze-intent")
            print("  ✓ Ancien pipeline supprimé\n")
        except Exception as e:
            print(f"  ℹ️  Aucun ancien pipeline à supprimer\n")

        # Créer le pipeline sur CraftAI
        result = sdk.create_pipeline(
            pipeline_name="analyze-intent",
            function_path="pipelines/analyze_intent.py",
            function_name="analyze_intent",
            description="Analyse l'intention d'un message utilisateur (DEBAT, CITATIONS, HORS_SUJET)",
            inputs=[message_input],
            outputs=[result_output],
            container_config=container_config,
            wait_for_completion=True
        )

        print(f"\n✅ Pipeline uploadé avec succès!")
        print(f"   Nom: {result['parameters']['pipeline_name']}")
        print(f"   Status: {result['creation_info']['status']}")
        print(f"   Origin: {result['creation_info']['origin']}")

        print(f"\n💡 Prochaine étape: Exécutez le script de déploiement")
        print(f"   python scripts/deploy_pipeline.py")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'upload: {e}")
        print(f"\nℹ️  Vérifiez:")
        print(f"   - Que CRAFT_AI_SDK_TOKEN est bien définie")
        print(f"   - Que CRAFT_AI_ENVIRONMENT_URL est bien définie")
        print(f"   - Que MISTRAL_API_KEY est bien définie")
        print(f"   - Que vous êtes bien connecté à CraftAI")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
