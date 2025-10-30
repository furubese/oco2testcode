# Vibe Kanban - AWS CDK Infrastructure

This directory contains the AWS CDK infrastructure code for the Vibe Kanban application.

## Project Structure

```
cdk/
├── bin/
│   └── cdk.ts                 # CDK app entry point
├── lib/
│   └── cdk-stack.ts          # Main stack definition
├── test/
│   └── cdk.test.ts           # Stack tests
├── cdk.json                   # CDK configuration
├── package.json               # Dependencies
└── tsconfig.json             # TypeScript configuration
```

## Prerequisites

- Node.js 14.x or later
- AWS CLI configured with appropriate credentials
- AWS CDK CLI (`npm install -g aws-cdk`)

## Installation

Install project dependencies:

```bash
npm install
```

## Available Commands

- `npm run build` - Compile TypeScript to JavaScript
- `npm run watch` - Watch for changes and compile automatically
- `npm run test` - Run Jest unit tests
- `npm run synth` - Synthesize CloudFormation template
- `npm run deploy` - Deploy stack to AWS
- `npm run cdk` - Run CDK CLI commands

## CDK Commands

- `cdk synth` - Synthesize CloudFormation template
- `cdk deploy` - Deploy stack to AWS account/region
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy` - Remove stack from AWS

## Dependencies

### Core Dependencies
- **aws-cdk-lib** (^2.221.1) - AWS CDK core library
- **constructs** (^10.4.2) - CDK constructs base library

### Development Dependencies
- **aws-cdk** (2.1031.0) - CDK CLI toolkit
- **cdk-nag** (^2.37.55) - Security validation rules
- **typescript** (~5.6.3) - TypeScript compiler
- **jest** (^29.7.0) - Testing framework
- **ts-jest** (^29.2.5) - TypeScript Jest transformer

## Security Validation with CDK Nag

This project uses CDK Nag for security best practices validation. CDK Nag will check your infrastructure code against AWS security best practices and Well-Architected Framework guidelines.

To enable CDK Nag in your stack, add the following to your `bin/cdk.ts`:

```typescript
import { AwsSolutionsChecks } from 'cdk-nag';
import { Aspects } from 'aws-cdk-lib';

const app = new cdk.App();
const stack = new CdkStack(app, 'CdkStack');

// Apply CDK Nag checks
Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

## Configuration

The CDK configuration is managed through:

- **cdk.json** - CDK toolkit configuration
- **tsconfig.json** - TypeScript compiler options
- **package.json** - Project metadata and dependencies

### TypeScript Configuration

The project uses strict TypeScript configuration with:
- Target: ES2022
- Module: NodeNext
- Strict mode enabled
- Declaration files generated

## Development Workflow

1. **Make changes** to your infrastructure code in `lib/cdk-stack.ts`
2. **Build** the project: `npm run build`
3. **Synthesize** to verify: `npm run synth`
4. **Test** your changes: `npm run test`
5. **Deploy** to AWS: `npm run deploy`

## Best Practices

- Always run `cdk synth` before deploying to verify the generated template
- Use CDK Nag to validate security best practices
- Write unit tests for your infrastructure code
- Use environment-specific configurations for different deployment stages
- Review generated CloudFormation templates in `cdk.out/` directory

## Environment Configuration

To deploy to a specific AWS account/region, modify `bin/cdk.ts`:

```typescript
new CdkStack(app, 'CdkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  }
});
```

## Troubleshooting

### Bootstrap Required

If you encounter bootstrap errors, run:

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### TypeScript Compilation Errors

Run TypeScript compiler directly to see detailed errors:

```bash
npx tsc --noEmit
```

### CDK Synth Failures

Check the error messages and verify:
- All required dependencies are installed
- TypeScript compilation succeeds
- No circular dependencies exist

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [CDK TypeScript Reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html)
- [CDK Nag Rules](https://github.com/cdklabs/cdk-nag)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## License

This project is part of the Vibe Kanban application.
