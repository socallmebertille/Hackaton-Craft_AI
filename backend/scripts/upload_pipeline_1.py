"""
Script pour uploader le Pipeline 1 (extract_legal_concepts) sur CraftAI
"""

import sys
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, Input, Output

def main():
    print("="*80)
    print("Upload Pipeline 1 - extract_legal_concepts sur CraftAI")
    print("="*80)

    # Initialiser le SDK CraftAI
    sdk = CraftAiSdk()

    # Définir les inputs et outputs
    question_input = Input(
        name="question",
        data_type="string",
        description="Question juridique posée par l'utilisateur"
    )

    result_output = Output(
        name="result",
        data_type="json",
        description="Concepts juridiques extraits (codes, concepts, nature_filter)"
    )

    # Configuration du container
    container_config = {
        "local_folder": "/app",
        "language": "python:3.12-slim",
        "requirements_path": "requirements.txt",
        "included_folders": [
            "pipelines/extract_legal_concepts.py",
            "services/mistral_service.py",
            "requirements.txt"
        ]
    }

    print(f"\n📤 Upload du pipeline...")

    try:
        # Supprimer l'ancien pipeline s'il existe
        try:
            sdk.delete_pipeline("extract-legal-concepts")
            print("  - Ancien pipeline supprimé\n")
        except:
            pass

        # Créer le pipeline sur CraftAI
        result = sdk.create_pipeline(
            pipeline_name="extract-legal-concepts",
            function_path="pipelines/extract_legal_concepts.py",
            function_name="extract_legal_concepts",
            description="Extrait les concepts juridiques d'une question pour recherche Legifrance",
            inputs=[question_input],
            outputs=[result_output],
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
