resource "azurerm_management_lock" "this" {
  count = var.lock != null ? 1 : 0

  lock_level = var.lock.kind
  name       = coalesce(var.lock.name, "lock-${var.lock.kind}")
  scope      = data.azurerm_resource_group.ai.id
  notes      = var.lock.kind == "CanNotDelete" ? "Cannot delete the resource or its child resources." : "Cannot delete or modify the resource or its child resources."
}

resource "azurerm_role_assignment" "this" {
  for_each = var.role_assignments

  role_definition_id                     = each.value.role_definition_id
  role_definition_name                   = each.value.role_definition_name
  principal_id                           = each.value.principal_id
  scope                                  = data.azurerm_resource_group.ai.id
  condition                              = each.value.condition
  condition_version                      = each.value.condition_version
  delegated_managed_identity_resource_id = each.value.delegated_managed_identity_resource_id
  skip_service_principal_aad_check       = each.value.skip_service_principal_aad_check
}

module "application_insights" {
  count                                          = var.deploy_app_insights_for_aml ? 1 : 0
  source                                         = "../appinsights"
  resource_group_name                            = var.resource_group_name
  log_analytics_workspace_resource_id            = var.log_analytics_workspace_resource_id
  local_authentication_disabled                  = var.ai_app_insights_local_authentication_disabled
  internet_ingestion_enabled                     = var.ai_app_insights_internet_ingestion_enabled
  internet_query_enabled                         = var.ai_app_insights_internet_query_enabled
  name                                           = local.ai_app_insights_name
  location                                       = var.location
  tags                                           = var.tags
}

module "storage_account" {
  source                = "../storage_account"
  location              = var.location
  name                  = local.aml_storage_account_name
  resource_group_name   = var.resource_group_name
  tags                  = var.tags
  enable_telemetry      = var.enable_telemetry

  infrastructure_encryption_enabled = var.infrastructure_encryption_enabled

  # DoD IL4 and IL5 settings
  user_assigned_identity_id = var.customer_managed_key != null ? (can(list(var.customer_managed_key.user_assigned_identity.resource_id)) ? [var.customer_managed_key.user_assigned_identity.resource_id] : var.customer_managed_key.user_assigned_identity.resource_id) : null
  customer_managed_key      = var.customer_managed_key
}

module "azure_openai" {
  count                 = var.deploy_aoai ? 1 : 0
  source                = "../azure_openai"
  location              = var.location
  name                  = local.azureopenai_name
  resource_group_name   = var.resource_group_name
  enable_telemetry      = var.enable_telemetry
  sku                   = var.azureopenai_sku
  cognitive_deployments = var.cognitive_deployments
  diagnostic_settings   = var.diagnostic_settings
  tags                  = var.tags
}

module "aml" {
  source                              = "../aml"
  location                            = var.location
  name                                = local.machine_learning_workspace_name
  resource_group_name                 = var.resource_group_name
  enable_telemetry                    = var.enable_telemetry
  tags                                = var.tags
  kind                                = var.kind # pass "Hub" for AI Foundry Hub creation
  create_compute_instance             = var.create_compute_instance
  workspace_managed_network           = var.workspace_managed_network
  storage_account_resource_id         = module.storage_account.output.resource_id
  container_registry_resource_id      = var.container_registry_resource_id
  key_vault_resource_id               = var.key_vault_resource_id
  application_insights_resource_id    = module.application_insights[0].output.resource_id
  log_analytics_workspace_resource_id = var.log_analytics_workspace_resource_id
  customer_managed_key      = var.customer_managed_key
  user_assigned_identity_id = var.customer_managed_key != null ? [var.customer_managed_key.user_assigned_identity.resource_id] : null

  deploy_ai_services = var.deploy_ai_services
  ai_service_name    = var.deploy_ai_services && var.kind == "Hub" ? local.aiservices_name : null

  depends_on = [module.application_insights, module.ai_services]
}

module "aiproject" {
  source   = "../aiproject"
  for_each = var.deploy_ai_projects && var.kind == "Hub" && length(var.ai_projects) > 0 ? { for idx, project in var.ai_projects : idx => project } : {}

  location              = var.location
  resource_group_name   = var.resource_group_name
  hub_name              = local.machine_learning_workspace_name
  project_name          = each.value.name
  project_description   = each.value.description
  project_friendly_name = each.value.friendly_name
  workspace_managed_network = var.workspace_managed_network

  depends_on = [module.aml]
}

module "ai_services" {
  count                 = var.deploy_ai_services ? 1 : 0
  source                = "../aiservices"
  location              = var.location
  name                  = local.aiservices_name
  resource_group_name   = var.resource_group_name
  enable_telemetry      = var.enable_telemetry
  tags = var.tags
  public_network_access_enabled = true
}

resource "azapi_resource" "aoai_connection" {
  count     = var.deploy_aoai ? 1 : 0
  type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01"
  name      = "openai-connection"
  parent_id = module.aml.output.resource_id
  body = {
    properties = {
      authType       = "AAD"
      category       = "AzureOpenAI"
      isSharedToAll  = false
      sharedUserList = var.ds_group_members
      metadata = {
        ApiType    = "Azure",
        kind       = "AzureOpenAI",
        ResourceId = module.azure_openai[0].output.resource_id
      }
      target = module.azure_openai[0].output.endpoint
    }
  }
}
