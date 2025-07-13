module "application_insights" {
  source                        = "Azure/avm-res-insights-component/azurerm"
  version                       = "0.1.5"
  resource_group_name           = var.resource_group_name
  workspace_id                  = var.log_analytics_workspace_resource_id
  name                          = var.name
  location                      = var.location
  local_authentication_disabled = var.local_authentication_disabled
  internet_ingestion_enabled    = var.internet_ingestion_enabled
  internet_query_enabled        = var.internet_query_enabled
  tags                          = var.tags
  enable_telemetry              = var.enable_telemetry
}