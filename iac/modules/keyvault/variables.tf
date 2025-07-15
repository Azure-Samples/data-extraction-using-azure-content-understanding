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

variable "keys" {
  type = map(object({
    name     = string
    key_type = string
    key_opts = optional(list(string), ["sign", "verify"])

    key_size        = optional(number, null)
    curve           = optional(string, null)
    not_before_date = optional(string, null)
    expiration_date = optional(string, null)
    tags            = optional(map(any), null)

    role_assignments = optional(map(object({
      role_definition_id_or_name             = string
      principal_id                           = string
      description                            = optional(string, null)
      skip_service_principal_aad_check       = optional(bool, false)
      condition                              = optional(string, null)
      condition_version                      = optional(string, null)
      delegated_managed_identity_resource_id = optional(string, null)
      principal_type                         = optional(string, null)
    })), {})

    rotation_policy = optional(object({
      automatic = optional(object({
        time_after_creation = optional(string, null)
        time_before_expiry  = optional(string, null)
      }), null)
      expire_after         = optional(string, null)
      notify_before_expiry = optional(string, null)
    }), null)
  }))
  default = {}
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

variable "public_network_access_enabled" {
  type        = bool
  default     = false
  description = "Specifies whether the key vault is accessible from the public internet."
}

variable "tenant_id" {
  type        = string
  description = "The tenant id of the Azure AD tenant."
}

variable "diagnostic_settings" {
  type = map(object({
    name                  = optional(string, null)
    workspace_resource_id = optional(string, null)
  }))
}

variable "role_assignments" {
  type = map(object({
    role_definition_id_or_name             = string
    principal_id                           = string
    description                            = optional(string, null)
    skip_service_principal_aad_check       = optional(bool, false)
    condition                              = optional(string, null)
    condition_version                      = optional(string, null)
    delegated_managed_identity_resource_id = optional(string, null)
    principal_type                         = optional(string, null)
  }))
  default = {}
}
