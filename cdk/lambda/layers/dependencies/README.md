# Lambda Layer Dependencies

This directory contains the dependencies for the reasoning Lambda function.

## Dependencies

- `google-generativeai==0.3.2` - Google Gemini AI SDK
- `boto3==1.34.0` - AWS SDK for Python
- `botocore==1.34.0` - Low-level AWS SDK core

## Building the Layer

### Option 1: Using Docker (Recommended)

If you have Docker installed, CDK will automatically bundle the layer when you run:

```bash
cd cdk
cdk synth
```

The bundling process will:
1. Use Python 3.11 Docker image
2. Install dependencies from requirements.txt
3. Package them in the correct structure for Lambda layers

### Option 2: Manual Build (Without Docker)

If Docker is not available, you can build the layer manually:

```bash
# Navigate to this directory
cd cdk/lambda/layers/dependencies

# Create the python directory if it doesn't exist
mkdir -p python

# Install dependencies
pip install -r requirements.txt -t python/ --platform manylinux2014_x86_64 --only-binary=:all:

# If the above fails, try without platform-specific builds
pip install -r requirements.txt -t python/
```

**Important:** When building manually on Windows, the packages may not be compatible with Lambda's Linux runtime. Use Docker or build on a Linux machine for production deployments.

### Option 3: Pre-built Layer ARN

For production deployments, you can also use a pre-built Lambda layer ARN if available:

1. Comment out the `dependenciesLayer` creation in `compute-stack.ts`
2. Use `lambda.LayerVersion.fromLayerVersionArn()` to reference a pre-built layer

## Layer Structure

After building, the layer should have this structure:

```
dependencies/
├── python/
│   ├── google/
│   ├── boto3/
│   ├── botocore/
│   └── ... (other dependencies)
├── requirements.txt
└── README.md
```

## Verification

To verify the layer was built correctly:

```bash
# Check that python directory exists and has content
ls -la python/

# Check for google-generativeai package
ls -la python/ | grep google

# Check size (should be several MB)
du -sh python/
```

## Troubleshooting

### Error: "spawnSync docker ENOENT"

This means Docker is not installed or not in your PATH. Either:
1. Install Docker Desktop
2. Use manual build (Option 2)
3. Build on a different machine with Docker

### Error: "No such file or directory"

Make sure you're in the correct directory:
```bash
pwd  # Should end with: cdk/lambda/layers/dependencies
```

### Error: Package installation fails

Try installing with `--no-deps` and manually add missing dependencies:
```bash
pip install google-generativeai==0.3.2 -t python/ --no-deps
pip install boto3==1.34.0 -t python/ --no-deps
```
