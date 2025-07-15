

module "cosmosdb" {
  source  = "Azure/avm-res-documentdb-databaseaccount/azurerm"
  version = "0.8.0"

  resource_group_name                     = var.resource_group_name
  location                                = var.location
  name                                    = var.name
  analytical_storage_enabled              = var.analytical_storage_enabled
  public_network_access_enabled           = var.public_network_access_enabled
  private_endpoints_manage_dns_zone_group = var.private_endpoints_manage_dns_zone_group
  mongo_server_version                    = var.mongo_server_version

  geo_locations = var.geo_locations

  managed_identities = var.managed_identities

  # MongoDB capabilities (only if MongoDB is enabled)
  capabilities = var.capabilities

  # MongoDB databases
  mongo_databases = var.mongo_databases

  # SQL API databases
  sql_databases = var.sql_databases

  enable_telemetry    = var.enable_telemetry
  diagnostic_settings = var.diagnostic_settings
  tags                = var.tags
}
