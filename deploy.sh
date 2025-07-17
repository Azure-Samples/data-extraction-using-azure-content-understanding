#!/bin/bash

# Data Extraction using Azure Content Understanding - One-Click Deployment Script
# This script deploys the infrastructure using Terraform in Azure Cloud Shell

set -e

echo "🚀 Starting deployment of Data Extraction using Azure Content Understanding..."

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Installing Terraform..."
    curl -O https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
    unzip terraform_1.5.0_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
    rm terraform_1.5.0_linux_amd64.zip
fi

# Clone the repository if not already cloned
if [ ! -d "data-extraction-using-azure-content-understanding" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/Azure-Samples/data-extraction-using-azure-content-understanding.git
fi

cd data-extraction-using-azure-content-understanding/iac

# Prompt user for required parameters
echo ""
echo "📝 Please provide the required deployment parameters:"
echo ""

# Get subscription ID with validation
while true; do
    echo -n "🔑 Enter your Azure Subscription ID: "
    read SUBSCRIPTION_ID
    if [[ -z "$SUBSCRIPTION_ID" ]]; then
        echo "❌ Subscription ID cannot be empty. Please try again."
    elif [[ ${#SUBSCRIPTION_ID} -ne 36 ]]; then
        echo "❌ Subscription ID must be 36 characters long (GUID format). Please try again."
    elif [[ ! "$SUBSCRIPTION_ID" == *-*-*-*-* ]]; then
        echo "❌ Invalid subscription ID format. Please enter a valid GUID (e.g., 12345678-1234-1234-1234-123456789012)."
    else
        # Additional validation - check if it's a valid GUID pattern
        if [[ "$SUBSCRIPTION_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
            break
        else
            echo "❌ Invalid subscription ID format. Please enter a valid GUID with hexadecimal characters only."
        fi
    fi
done

# Get resource group location
echo ""
echo "Available regions (Azure Content Understanding supported - Preview):"
echo "  1) westus (West US)"
echo "  2) swedencentral (Sweden Central)"
echo "  3) australiaeast (Australia East)"
echo ""
echo "⚠️  Note: Azure Content Understanding is in preview and only available in these 3 regions."
echo ""
while true; do
    echo -n "🌍 Select resource group location (1-3): "
    read LOCATION_CHOICE
    case $LOCATION_CHOICE in
        1)
            RESOURCE_GROUP_LOCATION="westus"
            RESOURCE_GROUP_LOCATION_ABBR="wu"
            break
            ;;
        2)
            RESOURCE_GROUP_LOCATION="swedencentral"
            RESOURCE_GROUP_LOCATION_ABBR="sc"
            break
            ;;
        3)
            RESOURCE_GROUP_LOCATION="australiaeast"
            RESOURCE_GROUP_LOCATION_ABBR="ae"
            break
            ;;
        *)
            echo "❌ Invalid choice. Please select 1-3."
            echo "💡 Note: Only regions where Azure Content Understanding is available are listed."
            ;;
    esac
done

# Get environment name
echo ""
while true; do
    echo -n "🏷️  Enter environment name (dev, test, prod, etc.) [default: dev]: "
    read ENVIRONMENT_NAME
    ENVIRONMENT_NAME=${ENVIRONMENT_NAME:-dev}
    if [[ "$ENVIRONMENT_NAME" =~ ^[a-zA-Z0-9]+$ ]]; then
        break
    else
        echo "❌ Environment name must contain only alphanumeric characters."
    fi
done

# Get use case name
echo ""
while true; do
    echo -n "📋 Enter use case name [default: dataext]: "
    read USECASE_NAME
    USECASE_NAME=${USECASE_NAME:-dataext}
    if [[ "$USECASE_NAME" =~ ^[a-zA-Z0-9-]+$ ]]; then
        break
    else
        echo "❌ Use case name must contain only alphanumeric characters and hyphens."
    fi
done

echo ""
echo "✅ Configuration summary:"
echo "   - Subscription ID: ${SUBSCRIPTION_ID}"
echo "   - Location: ${RESOURCE_GROUP_LOCATION}"
echo "   - Location abbreviation: ${RESOURCE_GROUP_LOCATION_ABBR}"
echo "   - Environment: ${ENVIRONMENT_NAME}"
echo "   - Use case: ${USECASE_NAME}"
echo ""

# Initialize Terraform
echo "🏗️  Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan \
  -var="subscription_id=${SUBSCRIPTION_ID}" \
  -var="resource_group_location=${RESOURCE_GROUP_LOCATION}" \
  -var="resource_group_location_abbr=${RESOURCE_GROUP_LOCATION_ABBR}" \
  -var="environment_name=${ENVIRONMENT_NAME}" \
  -var="usecase_name=${USECASE_NAME}"

# Ask for confirmation before applying
echo ""
echo -n "🤔 Do you want to proceed with the deployment? (y/N): "
read -n 1 -r REPLY
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying infrastructure..."
    terraform apply -auto-approve \
      -var="subscription_id=${SUBSCRIPTION_ID}" \
      -var="resource_group_location=${RESOURCE_GROUP_LOCATION}" \
      -var="resource_group_location_abbr=${RESOURCE_GROUP_LOCATION_ABBR}" \
      -var="environment_name=${ENVIRONMENT_NAME}" \
      -var="usecase_name=${USECASE_NAME}"
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Configure your Function App settings"
    echo "   2. Deploy your application code"
    echo "   3. Upload your document extraction configurations"
    echo ""
    echo "📖 For detailed instructions, see the README.md file"
else
    echo "❌ Deployment cancelled"
    exit 1
fi
