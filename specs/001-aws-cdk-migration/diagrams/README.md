# Architecture Diagrams

This directory contains detailed architecture diagrams for the AWS CDK migration project.

## Diagram Files

### 📊 [phase1-architecture.md](./phase1-architecture.md)
**Current State Architecture**
- Local Flask server architecture
- Component details and request flows
- Technology stack and limitations
- Performance characteristics

### 📊 [phase2-architecture.md](./phase2-architecture.md)
**Target State Architecture**
- AWS serverless architecture with all services
- Detailed component descriptions
- Cost estimates and performance metrics
- Migration advantages

### 📊 [cdk-stack-structure.md](./cdk-stack-structure.md)
**Infrastructure as Code Organization**
- CDK stack dependencies
- Deployment order and strategy
- Stack details (BaseStack, StorageStack, etc.)
- Cross-stack references

### 📊 [data-flow.md](./data-flow.md)
**Request/Response Flow Diagrams**
- Cache hit scenarios (Phase 1 & 2)
- Cache miss scenarios (Phase 1 & 2)
- Cache key generation
- Error handling flows
- Performance comparisons

### 📊 [component-interactions.md](./component-interactions.md)
**Component Communication Patterns**
- High-level component diagrams
- Module dependencies
- AWS service interactions
- Communication matrices
- Component lifecycle

## Viewing Diagrams

All diagrams are written in **Mermaid** format, which is natively supported by:

### GitHub
Simply view the `.md` files on GitHub - diagrams will render automatically.

### VS Code
Install the "Markdown Preview Mermaid Support" extension:
```bash
code --install-extension bierner.markdown-mermaid
```

### Command Line
Use the Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i phase1-architecture.md -o phase1-architecture.pdf
```

### Online
Use the [Mermaid Live Editor](https://mermaid.live/) to view and edit diagrams.

## Diagram Types Used

- **Flowcharts**: System architecture and component relationships
- **Sequence Diagrams**: Request/response flows and interactions
- **Graphs**: Dependencies and data flow

## Quick Reference

| Diagram | Best For |
|---------|----------|
| Phase 1 | Understanding current local architecture |
| Phase 2 | Understanding target AWS architecture |
| CDK Stacks | Planning deployment and IaC structure |
| Data Flow | Understanding cache behavior and performance |
| Component Interactions | Understanding how services communicate |

## Updates

When updating diagrams:
1. Edit the Mermaid code in the `.md` files
2. Test rendering on GitHub or Mermaid Live Editor
3. Update the parent [spec.md](../spec.md) if needed
4. Commit changes with descriptive message

## Related Documentation

- [Main Specification](../spec.md) - Complete migration specification
- [Project README](../../../README.md) - Project overview
