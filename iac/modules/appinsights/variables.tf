variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "enable_telemetry" {
  type        = bool
  default     = true
  description = <<DESCRIPTION
This variable controls whether or not telemetry is enabled for the module.
For more information see <https://aka.ms/avm/telemetryinfo>.
If it is set to false, then no telemetry will be collected.
As explained in the [AVM documentation](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/),
Microsoft relies on telemetry to identify the deployments of the AVM Modules.
Deployments are identified through a specific GUID (Globally Unique ID), indicating that the code originated from AVM.
The data is collected and governed by Microsoft’s privacy policies, found in the [Trust Center](https://www.microsoft.com/trust-center).
Telemetry collected does not provide Microsoft with insights into the resources deployed,
their configuration or any customer data stored in or processed by Azure resources deployed by using code from AVM.
Microsoft does not track the usage/consumption of individual resources using telemetry.
Telemetry collection is strictly optional, and it can easily be opted out of by following
[these procedures](https://azure.github.io/Azure-Verified-Modules/help-support/telemetry/#opting-out).
DESCRIPTION
}

variable "tags" {
  type        = map(string)
  default     = null
  description = "A map of tags to add to all resources"
}

variable "log_analytics_workspace_resource_id" {
  type        = string
  default     = ""
  description = "The resource_id of the Log Analytics Workspace."
}

variable "local_authentication_disabled" {
  type        = bool
  default     = false
  description = "(Optional) Disable Non-Azure AD based Auth"
}

variable "internet_ingestion_enabled" {
  type        = bool
  default     = false
  description = "(Optional) Should the Application Insights component support ingestion over the Public Internet?"
}

variable "internet_query_enabled" {
  type        = bool
  default     = false
  description = "(Optional) Should the Application Insights component support querying over the Public Internet?"
}
