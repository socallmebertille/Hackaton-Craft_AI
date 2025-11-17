"""
Script pour uploader le Pipeline 3 (generate_legal_debate) sur CraftAI
"""

import sys
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, Input, Output


def main():
    print("="*80)
    print("Upload Pipeline 3 - generate_legal_debate sur CraftAI")
    print("="*80)

    # Initialiser le SDK CraftAI
    sdk = CraftAiSdk()

    # Définir les inputs
    question_input = Input(
        name="question",
        data_type="string",
        description="Question juridique posée par l'utilisateur"
    )

    articles_input = Input(
        name="articles",
        data_type="json",
        description="Liste des articles juridiques trouvés avec leur texte complet"
    )

    # Définir l'output
    debate_output = Output(
        name="debate",
        data_type="json",
        description="Débat juridique en 2 rounds avec thèse/antithèse croisées et synthèse"
    )

    # Configuration du container
    container_config = {
        "local_folder": "/app",
        "language": "python:3.12-slim",
        "requirements_path": "requirements.txt",
        "included_folders": [
            "pipelines/generate_legal_debate.py",
            "services/mistral_debate_service.py",
            "requirements.txt"
        ]
    }

    print(f"\n📤 Upload du pipeline...")

    try:
        # Supprimer l'ancien pipeline s'il existe
        try:
            sdk.delete_pipeline("generate-legal-debate")
            print("  - Ancien pipeline supprimé\n")
        except:
            pass

        # Créer le pipeline sur CraftAI
        result = sdk.create_pipeline(
            pipeline_name="generate-legal-debate",
            function_path="pipelines/generate_legal_debate.py",
            function_name="generate_legal_debate",
            description="Génère un débat juridique contradictoire en 2 rounds à partir des articles trouvés",
            inputs=[question_input, articles_input],
            outputs=[debate_output],
            container_config=container_config,
            wait_for_completion=True
        )

        print(f"\n✅ Pipeline uploadé avec succès!")
        print(f"   Nom: {result['parameters']['pipeline_name']}")
        print(f"   Status: {result['creation_info']['status']}")
        print(f"   Origin: {result['creation_info']['origin']}")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'upload: {e}")
        print(f"\nℹ️ Vérifiez:")
        print(f"   - Que CRAFT_AI_SDK_TOKEN est bien définie")
        print(f"   - Que CRAFT_AI_ENVIRONMENT_URL est bien définie")
        print(f"   - Que vous êtes bien connecté à CraftAI")


if __name__ == "__main__":
    main()
