"""
Script pour uploader le Pipeline 2 (search_legal_texts) sur CraftAI
"""

import sys
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, Input, Output


def main():
    print("="*80)
    print("Upload Pipeline 2 - search_legal_texts sur CraftAI")
    print("="*80)

    # Initialiser le SDK CraftAI
    sdk = CraftAiSdk()

    # Définir les inputs
    codes_input = Input(
        name="codes",
        data_type="array",
        description="Liste des codes juridiques concernés"
    )

    concepts_input = Input(
        name="concepts",
        data_type="array",
        description="Liste des concepts juridiques clés"
    )

    nature_filter_input = Input(
        name="nature_filter",
        data_type="array",
        description="Liste des types de documents"
    )

    # Définir l'output
    articles_output = Output(
        name="articles",
        data_type="json",
        description="Liste des articles juridiques trouvés avec leur texte complet"
    )

    # Configuration du container
    container_config = {
        "local_folder": "/app",
        "language": "python:3.12-slim",
        "requirements_path": "requirements.txt",
        "included_folders": [
            "pipelines/search_legal_texts.py",
            "services/legifrance_service.py",
            "requirements.txt"
        ]
    }

    print(f"\n📤 Upload du pipeline...")

    try:
        # Supprimer l'ancien pipeline s'il existe
        try:
            sdk.delete_pipeline("search-legal-texts")
            print("  - Ancien pipeline supprimé\n")
        except:
            pass

        # Créer le pipeline sur CraftAI
        result = sdk.create_pipeline(
            pipeline_name="search-legal-texts",
            function_path="pipelines/search_legal_texts.py",
            function_name="search_legal_texts",
            description="Recherche les textes juridiques sur Legifrance à partir des concepts extraits",
            inputs=[codes_input, concepts_input, nature_filter_input],
            outputs=[articles_output],
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
