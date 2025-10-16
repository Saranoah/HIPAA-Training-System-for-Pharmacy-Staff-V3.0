#!/bin/bash

PythonAnywhere Deployment Script
echo "🚀 Deploying to PythonAnywhere"

echo "==============================="

Configuration
PA_USERNAME="your_username" # Change this!

PA_DOMAIN="$PA_USERNAME.pythonanywhere.com"

echo ""

echo "📦 Step 1: Preparing deployment package..."

Create deployment directory
mkdir -p deploy_package

cd deploy_package

Copy necessary files
cp -r ../hipaa_training .

cp ../main.py .

cp ../requirements.txt .

cp -r ../content .

cp -r ../scripts .

Create .env template
cat > .env << EOF

HIPAA_ENCRYPTION_KEY=CHANGE_ME_TO_SECURE_KEY

HIPAA_SALT=CHANGE_ME_TO_SECURE_SALT

DB_URL=/home/$PA_USERNAME/hipaa_training.db

EOF

Create README for deployment
cat > DEPLOY_README.txt << EOF

PYTHONANYWHERE DEPLOYMENT INSTRUCTIONS

======================================

Upload this entire folder to PythonAnywhere

Open a Bash console on PythonAnywhere

Run these commands:

cd ~

unzip deploy_package.zip

cd deploy_package

Install dependencies
pip3.9 install --user -r requirements.txt

Set environment variables
nano .env # Edit and save secure keys

Initialize database
python3.9 main.py --setup-only

Test
python3.9 main.py --check-env

To run the application:

python3.9 main.py

For web console access, create a web app:

Go to Web tab

Add new web app

Choose Flask

Point to this directory

EOF

Create ZIP
cd ..

zip -r deploy_package.zip deploy_package/

echo "✓ Deployment package created: deploy_package.zip"

echo ""

echo "📤 Next steps:"

echo "1. Upload deploy_package.zip to PythonAnywhere"

echo "2. Follow instructions in DEPLOY_README.txt"

echo "3. Test the application"
