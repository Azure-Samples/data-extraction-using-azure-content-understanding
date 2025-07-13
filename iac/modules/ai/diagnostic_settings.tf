# Diagnostic Settings
#
# Some modules implement diagnostic settings to send logs and metrics to Log Analytics.
# If the modules are invoked directly from this pattern AVM, the diagnostic settings are implemented in the reference to that module.
# However, if the module is invoked from another resource module that the pattern uses, it will not be possible to implement the diagnostic settings,
# without changing the implementation of the module used by the pattern.

# For this reason, this module creates diagnostic settings for any resource that is not directly invoked from this pattern module and
# does not implement diagnostic settings.

# If diagnostic settings for the resource use category groups (allLogs, allMetrics), add the id of the corresponding
# resource in the diag_settings_resources local variable.
# Otherwise, add its specific resource with the customized attributes for it (storage account, for example)

locals {
  diag_setting_resources = {
    aml = { resource_id = module.aml.output.resource_id },
  }
  diag_settings_storage_resources = {
    storage-blob  = { resource_id = format("%s%s", module.storage_account.output.resource_id, "/blobServices/default/") },
    storage-table = { resource_id = format("%s%s", module.storage_account.output.resource_id, "/tableServices/default/") },
    storage-file  = { resource_id = format("%s%s", module.storage_account.output.resource_id, "/fileServices/default/") },
    storage-queue = { resource_id = format("%s%s", module.storage_account.output.resource_id, "/queueServices/default/") }
  }
}

resource "azurerm_monitor_diagnostic_setting" "diag_setting_resources" {
  for_each = local.diag_setting_resources

  name                       = var.diagnostic_settings.defaultDiagnosticSettings.name
  target_resource_id         = each.value.resource_id
  log_analytics_workspace_id = var.log_analytics_workspace_resource_id

  enabled_log {
    category_group = "allLogs"
  }
  enabled_metric {
    category = "AllMetrics"
  }
}

# Storage diagnostic settings that use "AllMetrics" affect the idempotency of the resource, so they are implemented separately
# until the issue is solved in the provider.

resource "azurerm_monitor_diagnostic_setting" "diag_setting_storage_resources" {
  for_each = local.diag_settings_storage_resources

  name                       = var.diagnostic_settings.defaultDiagnosticSettings.name
  target_resource_id         = each.value.resource_id
  log_analytics_workspace_id = var.log_analytics_workspace_resource_id

  enabled_log {
    category_group = "allLogs"
  }

  enabled_metric {
    category = "Transaction"
  }
}

resource "azurerm_monitor_diagnostic_setting" "diag_setting_storage" {

  name                       = var.diagnostic_settings.defaultDiagnosticSettings.name
  target_resource_id         = module.storage_account.output.resource_id
  log_analytics_workspace_id = var.log_analytics_workspace_resource_id

  enabled_metric {
    category = "Transaction"
  }
}
