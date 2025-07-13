variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.name))
    error_message = "The name must be between 3 and 24 chars long and can only contain lowercase letters and numbers."
  }
}

# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources will be deployed."
}

variable "customer_managed_key" {
  type = object({
    key_vault_resource_id = string
    key_name              = string
    key_version           = optional(string, null)
    user_assigned_identity = optional(object({
      resource_id = string
    }), null)
  })
  default     = null
  description = "Specifies whether to use a customer-managed key for the ACR."
}

variable "infrastructure_encryption_enabled" {
  type        = bool
  default     = false
  description = "Specifies whether to enable infrastructure encryption for the storage account."
}

variable "account_replication_type" {
  type        = string
  default     = "LRS"
  description = "The replication type for the storage account."
}

variable "user_assigned_identity_id" {
  type        = list(string)
  default     = null
  description = "The ID of the user assigned identity."
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

variable "enabled_endpoints" {
  type        = set(string)
  description = "A set of enabled endpoint types for the storage account. Options are 'blob', 'queue', 'table', 'file'."
  default     = ["blob", "queue", "table", "file"] # this can be overridden
}
