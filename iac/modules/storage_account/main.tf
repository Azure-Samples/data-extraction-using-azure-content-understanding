
module "storage_account" {

  source  = "Azure/avm-res-storage-storageaccount/azurerm"
  version = "0.6.3"

  account_replication_type      = var.account_replication_type
  account_tier                  = "Standard"
  account_kind                  = "StorageV2"
  location                      = var.location
  name                          = var.name
  resource_group_name           = var.resource_group_name
  min_tls_version               = "TLS1_2"
  shared_access_key_enabled     = false
  public_network_access_enabled = true

  managed_identities = {
    system_assigned            = true
    user_assigned_resource_ids = var.user_assigned_identity_id
  }

  infrastructure_encryption_enabled = var.infrastructure_encryption_enabled
  tags                              = var.tags

  enable_telemetry = var.enable_telemetry

  network_rules = {
    bypass                     = ["AzureServices"]
    default_action             = "Deny"
  }

  customer_managed_key = var.customer_managed_key
}
