"""
Script pour créer un deployment du Pipeline 1 sur CraftAI
"""

import sys
sys.path.append('/app')

from craft_ai_sdk import CraftAiSdk, DEPLOYMENT_EXECUTION_RULES


def main():
    print("="*80)
    print("Déploiement du Pipeline 1 - extract_legal_concepts")
    print("="*80)

    sdk = CraftAiSdk()

    deployment_name = "extract-legal-concepts-deploy"

    print(f"\n🚀 Création du deployment '{deployment_name}'...")

    try:
        # Supprimer l'ancien deployment s'il existe
        try:
            sdk.delete_deployment(deployment_name)
            print("  - Ancien deployment supprimé\n")
        except:
            pass

        # Créer le deployment avec execution_rule ENDPOINT
        deployment = sdk.create_deployment(
            deployment_name=deployment_name,
            pipeline_name="extract-legal-concepts",
            execution_rule=DEPLOYMENT_EXECUTION_RULES.ENDPOINT,
            description="Deployment du pipeline d'extraction de concepts juridiques"
        )

        print(f"\n✅ Deployment créé avec succès!")
        print(f"   Name: {deployment.get('deployment_name')}")
        print(f"   Pipeline: {deployment.get('pipeline_name')}")
        print(f"   Status: {deployment.get('status')}")

        # Afficher l'endpoint si disponible
        if 'endpoint_url' in deployment:
            print(f"   Endpoint URL: {deployment.get('endpoint_url')}")
        if 'endpoint_token' in deployment:
            print(f"   Endpoint Token: {deployment.get('endpoint_token')}")

    except Exception as e:
        print(f"\n❌ Erreur lors du déploiement: {e}")
        print(f"\nℹ️ Vérifiez:")
        print(f"   - Que le pipeline 'extract-legal-concepts' existe")
        print(f"   - Que vous avez les permissions pour créer un deployment")


if __name__ == "__main__":
    main()
