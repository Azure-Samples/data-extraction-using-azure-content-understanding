variable "location" {
  type        = string
  description = "The location/region where the resources will be deployed."
  nullable    = false
}

variable "name" {
  type        = string
  description = "The name of the this resource."

  validation {
    condition     = can(regex("^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$", var.name))
    error_message = "The name can only include alphanumeric characters and hyphens, and can't start or end with a hyphen."
  }
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

variable "diagnostic_settings" {
  type = map(object({
    name                  = optional(string, null)
    workspace_resource_id = optional(string, null)
  }))
}

variable "local_authentication_enabled" {
  type        = bool
  default     = true
  description = "Controls whether or not local authentication is enabled for the Azure OpenAI Cognitive Services account."
}

variable "sku" {
  type        = string
  default     = "S0"
  description = "The SKU of the Azure OpenAI Cognitive Services account."
}

variable "cognitive_deployments" {
  type = map(object({
    name = string
    model = object({
      format  = string
      name    = string
      version = string
    })
    scale = object({
      type = string
    })
    rai_policy_name = string
  }))
  default     = {}
  description = <<DESCRIPTION
  A map of cognitive model deployments to create on the Azure OpenAI Cognitive Services account. The map key is deliberately arbitrary to avoid issues where map keys maybe unknown at plan time.
  - `name` - (Required) The name of the deployment.
  - `model` - (Required) The model to deploy.
    - `format` - "OpenAI"
    - `name` - The name of the model to deploy.
    - `version` - The version of the model to deploy.
  - `scale` - (Required) The scale of the model.
    - `type` - The type of scale to use. Possible values are `Standard`.
  - `rai_policy_name` - (Required) The name of the RAI policy to use for the deployment.
  example:
  ```
  {
    "gpt-4" = {
      name = "gpt-4"
      model = {
        format  = "OpenAI"
        name    = "gpt-4"
        version = "0125-Preview"
      }
      scale = {
        type = "Standard"
      }
      rai_policy_name = "Microsoft.DefaultV2"
    }
    "text-embedding-ada-002" = {
      name = "text-embedding-ada-002"
      model = {
        format  = "OpenAI"
        name    = "text-embedding-ada-002"
        version = "2"
      }
      scale = {
        type = "Standard"
      }
      rai_policy_name = "Microsoft.DefaultV2"
    }
  }
  ```
  DESCRIPTION
}

