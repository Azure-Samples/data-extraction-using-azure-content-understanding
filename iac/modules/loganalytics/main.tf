module "log_analytics_workspace" {
  source  = "Azure/avm-res-operationalinsights-workspace/azurerm"
  version = "0.4.2"

  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  enable_telemetry    = var.enable_telemetry

  log_analytics_workspace_cmk_for_query_forced = var.log_analytics_workspace_cmk_for_query_forced
}