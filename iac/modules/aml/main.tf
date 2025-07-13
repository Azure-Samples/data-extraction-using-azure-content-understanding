data "azurerm_resource_group" "resource_group" {
  name = var.resource_group_name
}

module "aml" {
  source                  = "Azure/avm-res-machinelearningservices-workspace/azurerm"
  version                 = "0.7.0"
  location                = var.location
  name                    = var.name
  workspace_friendly_name = var.name
  kind                    = var.kind

  resource_group_name     = var.resource_group_name
  create_compute_instance = var.create_compute_instance

  customer_managed_key = var.customer_managed_key

  primary_user_assigned_identity = {
    resource_id = var.user_assigned_identity_id != null ? var.user_assigned_identity_id[0] : null
  }

  managed_identities = {
    system_assigned            = var.customer_managed_key != null ? false : true
    user_assigned_resource_ids = var.user_assigned_identity_id
  }

  storage_account = {
    resource_id = var.storage_account_resource_id
    create_new  = false
  }

  storage_access_type = "identity" # We use only identity based access for the associated storage account

  key_vault = {
    resource_id = replace(var.key_vault_resource_id, "Microsoft.KeyVault", "Microsoft.Keyvault")
    create_new  = false
  }

  container_registry = {
    resource_id = var.container_registry_resource_id
    create_new  = false
  }

  application_insights = {

    create_new  = false # We pre-create App Insights before if var.deploy_app_insights_for_aml is true
    resource_id = var.application_insights_resource_id
    log_analytics_workspace = {
      create_new  = false
      resource_id = var.log_analytics_workspace_resource_id
    }
  }

  aiservices = var.deploy_ai_services ? {
    create_new                = false
    name                      = var.ai_service_name
    location                  = var.location
    resource_group_id         = data.azurerm_resource_group.resource_group.id
    enable_telemetry          = var.enable_telemetry
    create_service_connection = true
    tags                      = var.tags
    } : {
    create_new                = false
    name                      = null
    location                  = null
    resource_group_id         = null
    enable_telemetry          = null
    create_service_connection = null
    tags                      = null
  }

  outbound_rules            = var.outbound_rules
  workspace_managed_network = var.workspace_managed_network

  enable_telemetry = var.enable_telemetry
  tags             = var.tags
  is_private       = false
}

# Create RBAC roles and groups for AML workspace
resource "azurerm_role_assignment" "aml_workspace_ds" {
  count                = var.aml_workspace_ds_adgroup_id != null ? 1 : 0
  principal_id         = var.aml_workspace_ds_adgroup_id
  scope                = module.aml.resource_id
  role_definition_name = "AzureML Data Scientist"
  lifecycle {
    ignore_changes = [
      # Ignore changes to these attributes to prevent force-replacement
      scope,
      role_definition_id,
      principal_type
    ]
  }
}

resource "azurerm_role_assignment" "aml_workspace_ml_operator" {
  count                = var.aml_workspace_ml_operator_adgroup_id != null ? 1 : 0
  principal_id         = var.aml_workspace_ml_operator_adgroup_id
  scope                = module.aml.resource_id
  role_definition_name = "AzureML Compute Operator"
  lifecycle {
    ignore_changes = [
      # Ignore changes to these attributes to prevent force-replacement
      scope,
      role_definition_id,
      principal_type
    ]
  }
}
