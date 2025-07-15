output "output" {
  description = <<DESCRIPTION
The core output of the AI module.

- `resource_group`: The resource group targeted by the deployment.
- `virtual_network_name`: The name of the virtual network targeted by the deployment.
- `container_registry_name`: The name of the Azure Container Registry.
- `key_vault_name`: The name of the Azure Key Vault.
- `storage_account`: Details on the created storage account.
  - `resource_id`: The id of the storage account.
  - `name`: The name of the storage account.
- `workspace`:
  - `resource_id`: The id of the workspace.
  - `resource`:
    - `name`: The name of the workspace.
    - `container_registry_id`: The id of the associated container registry resource, if exists.
    - `storage_account_id`: The id of the associated storage account resource, if exists.
    - `key_vault_id`: The id of the associated key vault resource, if exists.
    - `application_insights_id`: The id of the associated App Insights resource, if exists.
  - `resource_identity`:
    - `principal_id`: The id of the identity assigned to the workspace.
    - `type`: the type of identity assigned to the workspace.
  DESCRIPTION
  value = {
    resource_group          = data.azurerm_resource_group.ai
    virtual_network_name    = var.virtual_network_name
    container_registry_name = var.container_registry_name
    key_vault_name          = var.key_vault_name
    storage_account = {
      resource_id = module.storage_account.output.resource_id
      name        = module.storage_account.output.name
    }
    workspace = module.aml.output
  }
}

output "azure_openai_resource" {
  value       = var.deploy_aoai ? module.azure_openai[0].output : null
  description = "The output for the azure_openai module"
}

output "ai_services_resource" {
  value       = var.deploy_ai_services ? module.ai_services[0].output : null
  description = "The output for the ai_services module"
}

