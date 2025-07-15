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

# Copy terraform variables template
if [ ! -f "terraform.tfvars" ]; then
    echo "📝 Creating terraform.tfvars file..."
    cp terraform.tfvars.sample terraform.tfvars
    
    # Get current subscription ID
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    
    # Replace placeholder values with defaults
    sed -i "s/<your-subscription-id>/${SUBSCRIPTION_ID}/g" terraform.tfvars
    sed -i "s/<your-resource-group-location>/East US/g" terraform.tfvars
    sed -i "s/<your-resource-group-location-abbr>/eus/g" terraform.tfvars
    sed -i "s/<your-environment-name>/dev/g" terraform.tfvars
    sed -i "s/<your-usecase-name>/data-extraction/g" terraform.tfvars
    
    echo "✅ terraform.tfvars created with default values"
    echo "📋 Please review and update the terraform.tfvars file if needed:"
    echo "   - Resource group location: East US"
    echo "   - Environment: dev"
    echo "   - Use case: data-extraction"
fi

# Initialize Terraform
echo "🏗️  Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan

# Ask for confirmation before applying
echo ""
read -p "🤔 Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying infrastructure..."
    terraform apply -auto-approve
    
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
