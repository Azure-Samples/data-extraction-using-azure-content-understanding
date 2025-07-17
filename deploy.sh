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
    echo ""
    echo "🔑 Please enter your Azure Subscription ID:"
    echo "   (Format: 12345678-1234-1234-1234-123456789012)"
    echo -n "Subscription ID: "
    read SUBSCRIPTION_ID
    
    # Remove any whitespace
    SUBSCRIPTION_ID=$(echo "$SUBSCRIPTION_ID" | tr -d '[:space:]')
    
    if [[ -z "$SUBSCRIPTION_ID" ]]; then
        echo "❌ Subscription ID cannot be empty. Please try again."
    elif [[ ${#SUBSCRIPTION_ID} -ne 36 ]]; then
        echo "❌ Subscription ID must be exactly 36 characters. You entered ${#SUBSCRIPTION_ID} characters."
    elif [[ "$SUBSCRIPTION_ID" != *"-"* ]]; then
        echo "❌ Subscription ID must contain dashes. Please enter a valid GUID format."
    else
        echo "✅ Subscription ID accepted: $SUBSCRIPTION_ID"
        break
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
    echo ""
    echo -n "🌍 Select resource group location (1-3): "
    read LOCATION_CHOICE
    
    # Remove any whitespace
    LOCATION_CHOICE=$(echo "$LOCATION_CHOICE" | tr -d '[:space:]')
    
    case $LOCATION_CHOICE in
        1)
            RESOURCE_GROUP_LOCATION="westus"
            RESOURCE_GROUP_LOCATION_ABBR="wu"
            echo "✅ Selected: West US"
            break
            ;;
        2)
            RESOURCE_GROUP_LOCATION="swedencentral"
            RESOURCE_GROUP_LOCATION_ABBR="sc"
            echo "✅ Selected: Sweden Central"
            break
            ;;
        3)
            RESOURCE_GROUP_LOCATION="australiaeast"
            RESOURCE_GROUP_LOCATION_ABBR="ae"
            echo "✅ Selected: Australia East"
            break
            ;;
        *)
            echo "❌ Invalid choice '$LOCATION_CHOICE'. Please select 1, 2, or 3."
            ;;
    esac
done

# Get environment name
echo ""
while true; do
    echo -n "🏷️  Enter environment name [default: dev]: "
    read ENVIRONMENT_NAME
    
    # Use default if empty
    if [[ -z "$ENVIRONMENT_NAME" ]]; then
        ENVIRONMENT_NAME="dev"
    fi
    
    # Remove whitespace
    ENVIRONMENT_NAME=$(echo "$ENVIRONMENT_NAME" | tr -d '[:space:]')
    
    # Simple validation - check if it contains only alphanumeric characters
    if [[ "$ENVIRONMENT_NAME" =~ ^[a-zA-Z0-9]+$ ]]; then
        echo "✅ Environment: $ENVIRONMENT_NAME"
        break
    else
        echo "❌ Environment name must contain only letters and numbers."
    fi
done

# Get use case name
echo ""
while true; do
    echo -n "📋 Enter use case name [default: dataext]: "
    read USECASE_NAME
    
    # Use default if empty
    if [[ -z "$USECASE_NAME" ]]; then
        USECASE_NAME="dataext"
    fi
    
    # Remove whitespace
    USECASE_NAME=$(echo "$USECASE_NAME" | tr -d '[:space:]')
    
    # Simple validation - check if it contains only alphanumeric characters and hyphens
    if [[ "$USECASE_NAME" =~ ^[a-zA-Z0-9-]+$ ]]; then
        echo "✅ Use case: $USECASE_NAME"
        break
    else
        echo "❌ Use case name must contain only letters, numbers, and hyphens."
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
echo "🤔 Do you want to proceed with the deployment? (y/N)"
echo -n "Enter your choice: "
read REPLY
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
