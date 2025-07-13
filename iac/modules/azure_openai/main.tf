

module "azureopenai" {
  source                = "Azure/avm-res-cognitiveservices-account/azurerm"
  version               = "0.7.1"
  kind                  = "OpenAI"
  location              = var.location
  name                  = var.name
  resource_group_name   = var.resource_group_name
  enable_telemetry      = var.enable_telemetry
  sku_name              = var.sku
  local_auth_enabled    = var.local_authentication_enabled
  cognitive_deployments = var.cognitive_deployments
  network_acls = {
    default_action = "Allow"
  }
  managed_identities = {
    system_assigned = true
  }
  diagnostic_settings = var.diagnostic_settings
  tags                = var.tags
}

