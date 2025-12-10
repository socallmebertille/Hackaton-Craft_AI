"""
Script pour créer un deployment du Pipeline debate sur CraftAI
"""

import sys
import os
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, DEPLOYMENT_EXECUTION_RULES


def main():
    print("=" * 80)
    print("Déploiement du Pipeline - debate")
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

    sdk = CraftAiSdk()

    deployment_name = "debate-deploy"

    # Variables d'environnement à configurer dans le deployment
    environment_variables = {
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
        "MISTRAL_MODEL_SMALL": os.getenv("MISTRAL_MODEL_SMALL", "mistral-small-latest")
    }

    print(f"\n🚀 Création du deployment '{deployment_name}'...")

    try:
        # Supprimer l'ancien deployment s'il existe
        try:
            sdk.delete_deployment(deployment_name)
            print("  ✓ Ancien deployment supprimé\n")
        except Exception as e:
            print(f"  ℹ️  Aucun ancien deployment à supprimer\n")

        # Créer le deployment avec execution_rule ENDPOINT
        deployment = sdk.create_deployment(
            deployment_name=deployment_name,
            pipeline_name="debate",
            execution_rule=DEPLOYMENT_EXECUTION_RULES.ENDPOINT,
            description="Deployment du pipeline de débat juridique contradictoire"
        )

        print(f"\n✅ Deployment créé avec succès!")
        print(f"   Name: {deployment.get('deployment_name')}")
        print(f"   Pipeline: {deployment.get('pipeline_name')}")
        print(f"   Status: {deployment.get('status')}")

        # Configurer les variables d'environnement après la création
        print(f"\n🔧 Configuration des variables d'environnement...")
        try:
            sdk.set_deployment_environment_variables(
                deployment_name=deployment_name,
                environment_variables=environment_variables
            )
            print(f"   ✓ Variables d'environnement configurées")
        except Exception as env_error:
            print(f"   ⚠️  Impossible de configurer les variables automatiquement: {env_error}")
            print(f"   ℹ️  Vous devrez les configurer manuellement dans l'interface CraftAI")
            print(f"   Variables nécessaires:")
            for key in environment_variables.keys():
                print(f"     - {key}")

        # Afficher l'endpoint si disponible
        if 'endpoint_url' in deployment:
            print(f"\n🔗 Endpoint:")
            print(f"   URL: {deployment.get('endpoint_url')}")
        if 'endpoint_token' in deployment:
            print(f"   Token: {deployment.get('endpoint_token')[:20]}...")

        print(f"\n📝 Configuration .env:")
        print(f"   Ajoutez ces lignes à votre fichier .env:")
        print(f"   PIPELINE_3_ENDPOINT_URL={deployment.get('endpoint_url', 'ENDPOINT_URL')}")
        print(f"   PIPELINE_3_ENDPOINT_TOKEN={deployment.get('endpoint_token', 'ENDPOINT_TOKEN')}")

        print(f"\n💡 Vous pouvez maintenant utiliser ce pipeline via l'endpoint!")
        print(f"   Exemple d'appel:")
        print(f"   curl -X POST {deployment.get('endpoint_url', 'ENDPOINT_URL')}")
        print(f"        -H 'Authorization: EndpointToken YOUR_TOKEN'")
        print(f"        -H 'Content-Type: application/json'")
        print(f"        -d '{{\"message\": \"Question juridique\", \"legal_data\": {{...}}}}'")

    except Exception as e:
        print(f"\n❌ Erreur lors du déploiement: {e}")
        print(f"\nℹ️  Vérifiez:")
        print(f"   - Que le pipeline 'debate' existe")
        print(f"   - Que vous avez les permissions pour créer un deployment")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
