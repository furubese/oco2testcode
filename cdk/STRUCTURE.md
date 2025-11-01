# CDK Project Structure

This document provides a visual overview of the CDK project structure.

## Directory Tree

```
cdk/
├── bin/
│   └── co2-analysis-app.ts          # CDK app entry point (142 lines)
│
├── lib/                              # Stack definitions
│   ├── base-stack.ts                 # Layer 1: Foundation (IAM, Secrets, SSM)
│   ├── network-stack.ts              # Layer 2: Network (VPC - optional)
│   ├── storage-stack.ts              # Layer 3: Data (DynamoDB, S3)
│   ├── compute-stack.ts              # Layer 4: Compute (Lambda)
│   ├── frontend-stack.ts             # Layer 5: Frontend (CloudFront, S3)
│   └── monitoring-stack.ts           # Layer 6: Observability (CloudWatch)
│
├── config/
│   └── environment.ts                # Environment configuration utilities
│
├── lambda/
│   ├── reasoning-handler/
│   │   ├── index.py                  # Lambda function handler (285 lines)
│   │   └── requirements.txt          # Python dependencies
│   └── layers/
│       └── dependencies/
│           └── requirements.txt      # Lambda layer dependencies
│
├── test/                             # CDK tests (to be implemented)
│   └── (test files go here)
│
├── cdk.json                          # CDK configuration & context
├── package.json                      # Node.js dependencies
├── tsconfig.json                     # TypeScript configuration
├── .gitignore                        # Git ignore patterns
│
├── README.md                         # Complete CDK documentation
├── DEPLOYMENT_GUIDE.md               # Deployment instructions
└── STRUCTURE.md                      # This file
```

## File Summary

**Total Files Created**: 16
**Total Lines of Code**: ~2,900 lines

---

**Last Updated**: 2025-11-01
