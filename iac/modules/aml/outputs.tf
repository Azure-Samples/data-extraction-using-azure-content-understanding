output "output" {
  description = <<DESCRIPTION
  An object with relevant details on the created resource (AML workspace, AI Foundry hub or AI Foundry project).

  - `resource_id`: the id of the resource.
  - `resource`:
    - `name`: resource name
    - `container_registry_id`: id of the associated container registry resource, if exists.
    - `storage_account_id`: id of the associated storage account resource, if exists.
    - `key_vault_id`: id of the associated key vault resource, if exists.
    - `application_insights_id`: id of the associated App Insights resource, if exists.
  - `resource_identity`:
    - `principal_id`: the id of the identity entity
    - `type`: the type of the identity entity
  DESCRIPTION
  value = {
    resource_id       = module.aml.resource_id
    resource          = module.aml.workspace
    resource_identity = module.aml.workspace_identity
  }
}
