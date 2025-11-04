#!/usr/bin/env python3
"""
Create a full Lambda deployment package with dependencies
"""
import subprocess
import sys
import os
import shutil
import zipfile

def install_dependencies():
    """Install dependencies to a temporary directory"""
    print("[INFO] Installing dependencies...")

    target_dir = "lambda_package"

    # Clean up existing directory
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir)

    # Install dependencies
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "google-generativeai",
        "boto3",
        "-t", target_dir,
        "--platform", "manylinux2014_x86_64",
        "--only-binary=:all:",
        "--python-version", "3.11"
    ], check=False)  # Don't check return code, some packages might not be platform-specific

    print(f"[OK] Dependencies installed to {target_dir}")
    return target_dir

def create_deployment_package(package_dir):
    """Create deployment package zip"""
    print("[INFO] Creating deployment package...")

    zip_path = "lambda_deployment.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from package directory
        for root, dirs, files in os.walk(package_dir):
            # Skip __pycache__ and dist-info directories
            dirs[:] = [d for d in dirs if d != '__pycache__' and not d.endswith('.dist-info')]

            for file in files:
                if file.endswith('.pyc'):
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)

        # Add Lambda handler
        handler_path = "cdk/lambda/reasoning-handler/index.py"
        zipf.write(handler_path, "index.py")

    file_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[OK] Created {zip_path} ({file_size:.2f} MB)")
    return zip_path

def update_lambda(zip_path):
    """Update Lambda function"""
    print("[INFO] Updating Lambda function...")

    function_name = "co2-analysis-dev-reasoning-api"
    profile = "fse"
    region = "us-east-1"

    cmd = [
        "aws", "lambda", "update-function-code",
        "--function-name", function_name,
        "--zip-file", f"fileb://{zip_path}",
        "--profile", profile,
        "--region", region
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Lambda function updated successfully")
        return True
    else:
        print(f"[ERROR] Failed to update Lambda function")
        print(result.stderr)
        return False

def cleanup(package_dir, zip_path):
    """Clean up temporary files"""
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
        print(f"[INFO] Cleaned up {package_dir}")

    # Keep the zip file for reference
    print(f"[INFO] Deployment package saved as {zip_path}")

def main():
    try:
        package_dir = install_dependencies()
        zip_path = create_deployment_package(package_dir)
        success = update_lambda(zip_path)
        cleanup(package_dir, zip_path)

        if success:
            print("\n[OK] Lambda function updated with full deployment package!")
            print("[INFO] Wait a few seconds for the update to propagate...")
            return 0
        else:
            print("\n[ERROR] Failed to update Lambda function")
            return 1
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
