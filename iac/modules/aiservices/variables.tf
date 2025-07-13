variable "enable_telemetry" {
  type        = bool
  default     = true
  description = <<DESCRIPTION
This variable controls whether or not telemetry is enabled for the module.
For more information see <https://aka.ms/avm/telemetryinfo>.
If it is set to false, then no telemetry will be collected.
DESCRIPTION
}

variable "sku" {
  type        = string
  default     = "S0"
  description = "The SKU of the resource."
}

variable "location" {
  type        = string
  default     = "westUS"
  description = "The location for the resources."
}

variable "tags" {
  type        = map(string)
  default     = null
  description = "A map of tags to add to all resources"
}

variable "resource_group_name" {
  type        = string
  default     = null
  description = "The name of the resource group to create the resources in."
}

variable "name" {
  type        = string
  description = "The name of the this resource."

  validation {
    condition     = can(regex("^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$", var.name))
    error_message = "The name can only include alphanumeric characters and hyphens, and can't start or end with a hyphen."
  }
}

variable "local_auth_enabled" {
  type        = bool
  default     = true
  description = "Whether or not local authentication is enabled."
}

variable "outbound_network_access_restricted" {
  type        = bool
  default     = false
  description = "Whether or not outbound network access is restricted."
}

variable "public_network_access_enabled" {
  type        = bool
  default     = false
  description = "Whether or not public network access is enabled."
}
