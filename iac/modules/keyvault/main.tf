
module "key_vault" {
  source  = "Azure/avm-res-keyvault-vault/azurerm"
  version = "0.10.0"

  name                          = var.name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = var.tenant_id
  public_network_access_enabled = var.public_network_access_enabled

  soft_delete_retention_days = 7 # shouldn't be hard coded

  role_assignments    = var.role_assignments
  diagnostic_settings = var.diagnostic_settings
  tags                = var.tags

  enable_telemetry = var.enable_telemetry
  keys             = var.keys
  wait_for_rbac_before_secret_operations = {
    create = "60s"
  }
  network_acls = {
    default_action = "Allow"
  }
}
