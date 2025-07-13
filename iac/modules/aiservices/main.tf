module "naming" {
  source  = "Azure/naming/azurerm"
  version = "0.4.2"
}

module "ai_services" {
  source                        = "Azure/avm-res-cognitiveservices-account/azurerm"
  version                       = "0.7.1"
  resource_group_name           = var.resource_group_name
  kind                          = "AIServices"
  name                          = var.name
  custom_subdomain_name         = "${var.name}-${module.naming.cognitive_account.name_unique}"
  location                      = var.location
  enable_telemetry              = var.enable_telemetry
  sku_name                      = var.sku
  public_network_access_enabled = var.public_network_access_enabled

  # Enable managed identity - required for AI projects
  managed_identities = {
    system_assigned = true
  }

  local_auth_enabled                 = var.local_auth_enabled
  outbound_network_access_restricted = var.outbound_network_access_restricted
  tags                               = var.tags
}

