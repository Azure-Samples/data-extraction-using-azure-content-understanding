<!-- BEGIN_TF_DOCS -->
# aiservices Module

---

## Requirements

| Name      | Version            |
|-----------|--------------------|
| terraform | >= 1.9             |
| azapi     | >= 1.14.0, < 3.0.0 |
| azurerm   | >= 4.0.0, < 5.0.0  |

## Providers

No providers.

## Modules

| Name         | Source                                          | Version |
|--------------|-------------------------------------------------|---------|
| ai\_services | Azure/avm-res-cognitiveservices-account/azurerm | 0.7.1   |
| naming       | Azure/naming/azurerm                            | 0.4.2   |

## Resources

No resources.

## Inputs

| Name                                  | Description                                                                                                                                                                                                 | Type                                                                          | Default    | Required |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|------------|:--------:|
| name                                  | The name of the this resource.                                                                                                                                                                              | `string`                                                                      | n/a        |   yes    |
| pe\_subnet\_resource\_id              | The resource\_id of the Private Endpoint subnet.                                                                                                                                                            | `string`                                                                      | n/a        |   yes    |
| private\_dns\_zones                   | Map of DNS zone names to their details                                                                                                                                                                      | <pre>map(object({<br/>    name = string<br/>    id   = string<br/>  }))</pre> | n/a        |   yes    |
| enable\_telemetry                     | This variable controls whether or not telemetry is enabled for the module.<br/>For more information see <https://aka.ms/avm/telemetryinfo>.<br/>If it is set to false, then no telemetry will be collected. | `bool`                                                                        | `true`     |    no    |
| local\_auth\_enabled                  | Whether or not local authentication is enabled.                                                                                                                                                             | `bool`                                                                        | `true`     |    no    |
| location                              | The location for the resources.                                                                                                                                                                             | `string`                                                                      | `"westUS"` |    no    |
| outbound\_network\_access\_restricted | Whether or not outbound network access is restricted.                                                                                                                                                       | `bool`                                                                        | `false`    |    no    |
| public\_network\_access\_enabled      | Whether or not public network access is enabled.                                                                                                                                                            | `bool`                                                                        | `false`    |    no    |
| resource\_group\_name                 | The name of the resource group to create the resources in.                                                                                                                                                  | `string`                                                                      | `null`     |    no    |
| sku                                   | The SKU of the resource.                                                                                                                                                                                    | `string`                                                                      | `"S0"`     |    no    |
| tags                                  | A map of tags to add to all resources                                                                                                                                                                       | `map(string)`                                                                 | `null`     |    no    |

## Outputs

| Name   | Description            |
|--------|------------------------|
| output | The AI Services module |
<!-- END_TF_DOCS -->
