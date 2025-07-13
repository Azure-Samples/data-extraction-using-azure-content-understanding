<!-- BEGIN_TF_DOCS -->
# aiproject Module

---

## Requirements

| Name      | Version            |
|-----------|--------------------|
| terraform | >= 1.9             |
| azapi     | >= 1.14.0, < 3.0.0 |
| azurerm   | >= 4.0.0, < 5.0.0  |
| random    | >= 3.0.0, < 4.0.0  |

## Providers

| Name    | Version           |
|---------|-------------------|
| azurerm | >= 4.0.0, < 5.0.0 |
| random  | >= 3.0.0, < 4.0.0 |

## Modules

| Name    | Source                                                  | Version |
|---------|---------------------------------------------------------|---------|
| project | Azure/avm-res-machinelearningservices-workspace/azurerm | 0.7.0   |

## Resources

| Name                                                                                                                                                       | Type        |
|------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| [random_string.project_name_suffix](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/string)                                 | resource    |
| [azurerm_machine_learning_workspace.ai_hub](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/machine_learning_workspace) | data source |

## Inputs

| Name                    | Description                                              | Type     | Default | Required |
|-------------------------|----------------------------------------------------------|----------|---------|:--------:|
| hub\_name               | The name of the AI Foundry to deploy projects into.      | `string` | n/a     |   yes    |
| location                | The location where the AI project will be deployed       | `string` | n/a     |   yes    |
| project\_description    | The description of the AI project                        | `string` | n/a     |   yes    |
| project\_friendly\_name | The friendly name of the AI project                      | `string` | n/a     |   yes    |
| project\_name           | The name of the AI project                               | `string` | n/a     |   yes    |
| resource\_group\_name   | The resource group where the resources will be deployed. | `string` | n/a     |   yes    |

## Outputs

| Name   | Description                   |
|--------|-------------------------------|
| output | The ID of the created project |
<!-- END_TF_DOCS -->
