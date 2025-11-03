#!/usr/bin/env python3
"""
Script to update Lambda function code without Docker
"""
import zipfile
import os
import subprocess
import sys

def create_lambda_zip():
    """Create a zip file with the Lambda function code"""
    handler_dir = "cdk/lambda/reasoning-handler"
    zip_path = "function.zip"

    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        index_path = os.path.join(handler_dir, "index.py")
        zipf.write(index_path, "index.py")

    print(f"[OK] Created {zip_path}")
    return zip_path

def update_lambda_function(zip_path):
    """Update Lambda function code using AWS CLI"""
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

    print(f"[INFO] Updating Lambda function: {function_name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Lambda function updated successfully")
        return True
    else:
        print(f"[ERROR] Failed to update Lambda function")
        print(result.stderr)
        return False

def cleanup(zip_path):
    """Clean up temporary files"""
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"[INFO] Cleaned up {zip_path}")

def main():
    try:
        zip_path = create_lambda_zip()
        success = update_lambda_function(zip_path)
        cleanup(zip_path)

        if success:
            print("\n[OK] Lambda function code updated successfully!")
            print("[INFO] Wait a few seconds for the update to propagate...")
            return 0
        else:
            print("\n[ERROR] Failed to update Lambda function")
            return 1
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
