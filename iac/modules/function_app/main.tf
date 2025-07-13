# App Service Plan
module "app_service_plan" {
  source  = "Azure/avm-res-web-serverfarm/azurerm"
  version = "0.5.0"

  enable_telemetry = var.enable_telemetry

  name                = "${var.app_name}asp"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = var.os_type

  zone_balancing_enabled = var.app_plan_zone_balancing_enabled
  worker_count           = var.app_plan_worker_count
  sku_name               = var.app_plan_sku_name
  tags                   = var.tags
}

# User Assigned Identity for the App Service
module "app_service_identity" {
  source              = "Azure/avm-res-managedidentity-userassignedidentity/azurerm"
  version             = "0.3.4"
  resource_group_name = var.resource_group_name
  location            = var.location
  enable_telemetry    = var.enable_telemetry
  name                = "${var.app_name}-${var.env}-identity"
  tags                = var.tags
}

# Define the App Service for the application
module "app_service" {
  source  = "Azure/avm-res-web-site/azurerm"
  version = "0.17.0"

  enable_telemetry = var.enable_telemetry

  name                = var.app_name
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "functionapp"
  os_type             = "Linux"

  # Uses an existing app service plan
  service_plan_resource_id = module.app_service_plan.resource_id

  # Required function app settings
  storage_account_name = data.azurerm_storage_account.storage_data.name

  # Disable public network access
  public_network_access_enabled = true

  # Use system-assigned managed identity
  managed_identities = {
    user_assigned_resource_ids = [module.app_service_identity.resource_id]
    system_assigned            = true
  }

  storage_uses_managed_identity = true

  site_config = var.function_app_site_config

  # Application settings for function app
  app_settings = merge(
    {
      "WEBSITE_RUN_FROM_PACKAGE" = "1" # Run App from package
      "FUNCTIONS_WORKER_RUNTIME" = var.runtime_name
      "RUNNING_ON_AZURE"         = "1"
      "AZURE_CLIENT_ID"          = module.app_service_identity.client_id
      "APP_CLIENT_ID"            = module.app_service_identity.client_id
      "APP_TENANT_ID"            = module.app_service_identity.tenant_id
    }
  )


  enable_application_insights = var.enable_application_insights

  application_insights = var.application_insights

  diagnostic_settings = var.diagnostic_settings

  auto_heal_setting = var.auto_heal_setting

  tags = var.tags
}

# Reference the existing Storage Account using its name
data "azurerm_storage_account" "storage_data" {
  resource_group_name = var.resource_group_name
  name                = var.storage_account_name
}

# Assign the 'Storage Blob Data Owner' role to the Function App's Managed Identity
resource "azurerm_role_assignment" "storage_role" {
  principal_id         = module.app_service_identity.principal_id
  role_definition_name = "Storage Blob Data Owner"
  scope                = data.azurerm_storage_account.storage_data.id

  lifecycle {
    ignore_changes = [
      principal_id,
      role_definition_name,
      scope
    ]
  }
}
