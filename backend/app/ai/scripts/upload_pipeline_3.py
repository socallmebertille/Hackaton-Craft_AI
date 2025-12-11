"""
Script pour uploader Pipeline 3 (Débat juridique) sur CraftAI
"""

import os
import sys
from pathlib import Path
from craft_ai_sdk import CraftAiSdk, Input, Output

# Configuration
PIPELINE_NAME = "debate"
PIPELINE_DESCRIPTION = "Pipeline 3 : Génère un débat contradictoire (pour/contre) basé sur des sources juridiques"

# Déterminer les chemins
script_dir = Path(__file__).parent.absolute()
ai_dir = script_dir.parent
pipelines_dir = ai_dir / "pipelines"
services_dir = ai_dir / "services"

print(f"📁 Script dir: {script_dir}")
print(f"📁 AI dir: {ai_dir}")
print(f"📁 Pipelines dir: {pipelines_dir}")
print(f"📁 Services dir: {services_dir}")

# Initialiser le SDK CraftAI
sdk = CraftAiSdk()

print(f"\n🚀 Upload de Pipeline 3 : {PIPELINE_NAME}")
print(f"📝 Description: {PIPELINE_DESCRIPTION}")

# Définir les inputs et outputs
message_input = Input(
    name="message",
    data_type="string",
    description="Question juridique de l'utilisateur"
)

legal_data_input = Input(
    name="legal_data",
    data_type="json",
    description="Données juridiques de P1 (codes + jurisprudence)"
)

result_output = Output(
    name="result",
    data_type="json",
    description="Débat structuré avec rounds pour/contre et synthèse"
)

# Fichiers à inclure dans le pipeline
# Note: mistral_service.py n'est pas nécessaire car debate_service.py utilise directement mistralai
included_folders = [
    "pipelines/debate.py",
    "services/debate_service.py",
    "requirements.txt"
]

print(f"\n📦 Fichiers à inclure:")
for f in included_folders:
    full_path = ai_dir / f
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"  ✅ {f} ({size} bytes)")
    else:
        print(f"  ❌ {f} (MANQUANT)")
        sys.exit(1)

# Configuration du container
container_config = {
    "local_folder": str(ai_dir),
    "language": "python:3.12-slim",
    "requirements_path": "requirements.txt",
    "included_folders": included_folders
}

print(f"\n⚙️ Configuration du pipeline:")
print(f"  - Nom: {PIPELINE_NAME}")
print(f"  - Fonction: debate")
print(f"  - Fichier principal: pipelines/debate.py")

try:
    print(f"\n🔄 Upload en cours...")

    # Supprimer l'ancien pipeline s'il existe
    try:
        sdk.delete_pipeline(PIPELINE_NAME)
        print("  ✓ Ancien pipeline supprimé\n")
    except Exception as e:
        print(f"  ℹ️  Aucun ancien pipeline à supprimer\n")

    # Créer le pipeline sur CraftAI
    result = sdk.create_pipeline(
        pipeline_name=PIPELINE_NAME,
        function_path="pipelines/debate.py",
        function_name="debate",
        description=PIPELINE_DESCRIPTION,
        inputs=[message_input, legal_data_input],
        outputs=[result_output],
        container_config=container_config,
        wait_for_completion=True
    )

    print(f"\n✅ Pipeline uploadé avec succès!")
    print(f"   Nom: {result['parameters']['pipeline_name']}")
    print(f"   Status: {result['creation_info']['status']}")
    print(f"   Origin: {result['creation_info']['origin']}")

    print(f"\n💡 Prochaine étape: Exécutez le script de déploiement")
    print(f"   python app/ai/scripts/deploy_pipeline_3.py")

except Exception as e:
    print(f"\n❌ Erreur lors de l'upload: {e}")
    print(f"\nℹ️  Vérifiez:")
    print(f"   - Que CRAFT_AI_SDK_TOKEN est bien définie")
    print(f"   - Que CRAFT_AI_ENVIRONMENT_URL est bien définie")
    print(f"   - Que vous êtes bien connecté à CraftAI")
    import traceback
    traceback.print_exc()
    sys.exit(1)
