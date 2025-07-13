# This is required for most resource modules
variable "resource_group_name" {
  type        = string
  description = "The resource group where the resources are deployed."
}

variable "location" {
  type        = string
  default     = "UKsouth"
  description = "The location for the resources."
}

variable "env" {
  type        = string
  default     = "dev"
  description = "The environment where the resource is deployed."
}

variable "app_name" {
  type        = string
  description = "The name of the application."
}

variable "os_type" {
  type        = string
  default     = "Linux"
  description = "The operating system that should be the same type of the App Service Plan to deploy the App Service in."
}

variable "kind" {
  type        = string
  default     = "functionapp"
  description = "The type of App Service to deploy. Possible values are `functionapp` and `webapp`."
}

variable "app_service_subnet_address_spaces" {
  description = "Address prefixes for the App Service subnet."
  type        = list(string)
  nullable    = false
  default     = ["10.1.8.0/24"]
}

variable "enable_application_insights" {
  type    = bool
  default = false
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

variable "app_plan_sku_name" {
  description = "The SKU name of the App Service Plan"
  type        = string
  default     = "P1v2" #P1v3 as another default value
}

variable "app_plan_worker_count" {
  description = "The number of workers to allocate for the App Service Plan"
  type        = string
  default     = "3"
}

variable "app_plan_zone_balancing_enabled" {
  description = "Whether to enable zone balancing for the App Service Plan"
  type        = bool
  default     = false
}

variable "tags" {
  type = map(string)
  default = {
    environment = "dev - secure CAIRA infra"
    cicd        = "terraform"
    name        = "CAIRA"
  }
  description = "A map of tags to add to all resources"
}

variable "storage_account_name" {
  type        = string
  description = "The name of storage account"
}

variable "storage_uses_managed_identity" {
  description = "Whether to use managed identity for the storage account."
  type        = bool
  default     = true
}

variable "runtime_name" {
  description = "The runtime environment to be used (e.g., 'node', 'python')."
  type        = string
  default     = "python"
}

variable "deploy_flex_plan" {
  description = "The flex plan model for azure function to be deployed."
  type        = bool
  default     = false
}

variable "runtime_version" {
  description = "The version of the runtime environment to be used (e.g., '14', '20')."
  type        = string
  default     = "3.11"
}

variable "maximum_instance_count" {
  description = "The maximum number of instances allowed for scaling."
  type        = number
  default     = 100
}

variable "instance_memory_in_mb" {
  description = "The amount of memory (in MB) allocated to each instance."
  type        = number
  default     = 2048
}

variable "function_app_uses_fc1" {
  description = "Whether the function app uses flex config 1."
  type        = bool
  default     = false
}

variable "functions_extension_version" {
  description = "The version of the Azure Functions runtime to use."
  type        = string
  default     = "~4"
}

variable "function_app_site_config" {
  description = "Site configuration for the function app."
  type        = any
  default     = {}
}


variable "https_only" {
  description = "Whether to enforce HTTPS for the function app."
  type        = bool
  default     = true
}


variable "auto_heal_setting" {
  description = "Auto healing configuration for the function app."
  type        = any
  default     = {}
}

variable "application_insights" {
  description = "Auto healing configuration for the function app."
  type        = any
  default     = {}
}

variable "diagnostic_settings" {
  type = map(object({
    name                  = optional(string, null)
    workspace_resource_id = optional(string, null)
  }))
  description = "Map of diagnostic settings for the function app."
}

variable "subnets" {
  type        = any
  default     = {}
  description = "The ID of the subnet to use for the function app."
}
