---
title: "GitOps at Scale: Orchestrating 21 Microservices with Kubernetes & ArgoCD"
date: 2026-04-12T07:00:00+07:00
draft: false
mermaid: true
tags: ["GitOps", "Kubernetes", "ArgoCD", "DevOps", "Microservices"]
description: "Why running kubectl apply is a dangerous anti-pattern. How we automated the deployment lifecycle of a 21-service Go platform using strict GitOps principles and ArgoCD."
categories: ["DevOps", "Engineering"]
---

Building 21 incredibly optimized Go microservices is only 50% of the battle. If your deployment process relies on an engineer typing `kubectl apply` from their local laptop on a Friday afternoon, you haven't built an Enterprise platform—you've built a ticking time bomb.

When designing our Composable E-commerce ecosystem, we made a hard architectural rule early on: **No human touches the production cluster directly.** 

To enforce this, we fully embraced **GitOps** using **ArgoCD**. Here is how we orchestrated it.

### The GitOps Principle: Git is God
The core philosophy of GitOps is that a Git repository must represent the *descriptive desired state* of the entire infrastructure. 

Instead of traditional CI pipelines pushing Docker images *into* our cluster, we use a GitOps "Pull" mechanism.

```mermaid
graph LR
    subgraph "CI: Code Pipeline"
        DEV[Developer] -- "git push" --> GIT[App Repository]
        GIT -- "Github Actions" --> DOCKER[(Container Registry)]
    end

    subgraph "CD: GitOps Pipeline"
        DOCKER -- "Updates Tag inside" --> MAN[Manifest Repository]
        ARGO[ArgoCD Controller] -- "Polls every 3m" --> MAN
    end

    subgraph "Kubernetes Cluster"
        ARGO -- "Applies differences" --> K8S[K8s Cluster Nodes]
    end
```

1. **Continuous Integration (CI):** An engineer pushes Go code. Github Actions runs the unit tests, compiles the binary, creates a Docker image, pushes it to our Registry, and finally opens a Pull Request on a totally separate **Manifest Repository** updating the Docker Tag string.
2. **Continuous Deployment (CD):** ArgoCD constantly watches this Manifest Repository. As soon as the PR is merged, ArgoCD detects that the *Desired State* (Git) differs from the *Actual State* (Kubernetes). 
3. ArgoCD automatically self-corrects the cluster, doing rolling restarts of the pods to load the new image. 

### Taming YAML Chaos with Kustomize
Managing Kubernetes manifests for 21 services across 3 environments (`dev`, `staging`, `prod`) yields over 60 massive YAML files. Copy-pasting these files causes devastating configuration drifts. 

We utilize **Kustomize** natively within ArgoCD to solve this. 
Each microservice is assigned a `base` template containing standardized Deployments and Services. We then use Kustomize `overlays` to inject environment-specific variables.
The `Catalog` service uses 1 CPU core in `dev`, but the `prod` Kustomize overlay dynamically rewrites the resource requests to 4 CPU cores and changes the `DB_HOST` variables to point to the production RDS cluster. 

### The Ultimate Rollback Button
Before GitOps, rolling back a severely bugged deployment meant frantically digging through CI/CD logs to find the old Docker tag and running manual imperative rollback commands while customers stared at 500 error screens.

With ArgoCD, our disaster recovery is literally a `git revert`.
If the `Checkout` service crashes production, an engineer simply reverts the commit in the Manifest Repository. ArgoCD instantly sees the change, kills the broken Pods, and spins up the previous extremely stable Docker image in seconds. 

### Conclusion
By treating our Kubernetes configuration as code and letting ArgoCD act as the uncompromising bouncer to our cluster, we ripped out human error completely. Developers focus entirely on writing Go Business Logic, knowing that if the code makes it into the Git Main branch, ArgoCD will elegantly hand-deliver it to the servers without dropping a single packet.
