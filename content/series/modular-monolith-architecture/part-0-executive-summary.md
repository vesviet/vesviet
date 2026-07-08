---
title: "Part 0: Executive Summary — How Amazon Prime Video Saved 90% on Infrastructure"
lastmod: "2026-07-03T15:41:55+07:00"
description: "Discover why Amazon Prime Video cut infrastructure costs by 90% after moving from Serverless/Microservices back to a Monolith, alongside case studies from"
slug: "executive-summary-amazon-prime-video-monolith"
aliases: ["/series/modular-monolith-architecture/part-0-executive-summary/"]
tags: ["Modular Monolith", "AWS", "Serverless", "FinOps", "Amazon Prime"]
cover:
  image: "images/posts/golang-microservices-cover.png"
  alt: "Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/executive-summary-amazon-prime-video-monolith/"
---

# Part 0: Executive Summary â€” How Amazon Prime Video Saved 90% on Infrastructure Costs

In the tech industry, Serverless architecture and Microservices are often hailed as the ultimate solutions for infinite scalability. However, this infinite scalability comes with massive hidden FinOps risks when traffic crosses a critical tipping point.

This article synthesizes a real-world report from the engineering team at **Amazon Prime Video**, along with restructuring stories from **Segment**, **Pinterest**, and **37signals**, to demonstrate the cost-optimizing power of the **Monolithic Architecture**.

## 1. The Classic Case Study: Amazon Prime Video's 90% Savings

**Answer-first:** Amazon Prime Video reduced infrastructure costs by 90% by migrating their audio/video monitoring service from a Serverless architecture (AWS Lambda and Step Functions) back to a Monolith. This consolidation eliminated massive state transition fees and S3 network egress bottlenecks caused by high-frequency inter-service data transfers.

In 2023, the team developing the audio/video monitoring service for Amazon Prime Video published an [engineering case study](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90) that sent shockwaves through the engineering community: They reduced their **infrastructure costs by 90%** by redesigning their system from Serverless Microservices back to a traditional Monolith.

### The Problem with the Old Architecture (Serverless)
The initial architecture was built by piecing together multiple Serverless components:
- Utilizing **AWS Step Functions** to orchestrate the workflow.
- Video processing functions were split into multiple independent **AWS Lambda** functions.
- Data communication between Lambdas went through **Amazon S3**.

When the system had to monitor thousands of high-frequency video streams simultaneously, two severe bottlenecks emerged:
1. **Orchestration Costs:** AWS Step Functions charge based on *state transitions*. At high transaction volumes, this fee increased exponentially, becoming the most expensive line item on the AWS bill.
2. **Network Egress and Storage Costs:** The fact that Lambda functions had to constantly read and write video frames to S3 created a network bottleneck and drastically inflated data retrieval costs.

### The Solution: Consolidation into a Monolith
Instead of trying to "optimize" a distributed architecture, the Prime Video team decided to **consolidate the entire logic of the Lambda functions and Step Functions into a single process**.

The new system (Monolith) was packaged and deployed directly on **Amazon EC2 / Amazon ECS**.
- Data between processing steps is now transferred directly in-memory, rather than requiring intermediate storage on S3.
- The orchestration costs of Step Functions were completely eliminated.

**The Result:** The system achieved lower latency, became easier to monitor, remained easy to scale (by copying EC2 instances), and most importantly: reduced cloud operational costs by 90%.

## 2. The Tipping Point of Serverless & Microservices

The lesson from Prime Video doesn't imply that Serverless or Microservices are ineffective. These technologies are incredibly cost-efficient during low-volume phases or for slow, asynchronous event processing systems.

However, for workloads involving **large data and high-frequency inter-service messaging**, Microservices will quickly reach a *Tipping Point*. At this point, the costs of Serialize/Deserialize (packing/unpacking data) and Network I/O will devour the actual Compute resources. Switching to a Monolith (direct in-RAM function calls) becomes cheaper by orders of magnitude.

## 3. The Million-Dollar Consolidation Wave

Amazon Prime Video is not alone; a massive wave of returning to centralized architecture is gaining momentum due to financial pressure (FinOps):

- **Segment:** Had to manage over 140 specialized microservices to push data to partners. This fragmentation led to enormous costs for maintaining CI/CD pipelines and Auto-scaling groups. Segment [consolidated them all into a single Monolithic Worker](https://segment.com/blog/goodbye-microservices/), saving over **$250,000** in cloud costs in the first year alone and reducing the on-call burden for engineers.
- **Pinterest:** Consolidated dozens of scattered microservices into large-scale domain services (Macroservices), eliminating redundant cross-service network hops, saving millions of dollars in AWS costs.
- **X/Twitter:** During recent infrastructure optimization efforts, Twitter decommissioned a slew of redundant microservices and integrated logic back into their core monoliths, reducing latency and costs.
- **37signals (HEY & Basecamp):** Took it a step further with a **Cloud Exit** strategy. Instead of optimizing the Monolith on the Cloud, they used **Kamal** to [deploy their Majestic Monolith applications directly onto Bare-metal servers](https://world.hey.com/dhh/the-big-cloud-exit-faq-20274010). In just the first year, they saved **$1.5 million** in server rental costs.

## Summary

Software optimization isn't about how many services you split your system into; it's about how you physically arrange the communication of the system. **In-memory execution is always cheaper and faster than network communication.**

In **[Part 1: Decision Framework]({{< ref "part-1-decision-framework.md" >}})**, we will dive deep into technical numbers (Latency Benchmarks) and Martin Fowler's "Microservice Premium" model, equipping you with precise quantitative criteria to choose the right architecture for your project.

## FAQ


{{< faq q="Why did Amazon Prime Video move away from serverless?" >}}
Amazon Prime Video abandoned their serverless architecture because AWS Step Functions orchestration fees and Amazon S3 read/write costs became too expensive when processing thousands of high-frequency video streams.
{{< /faq >}}

{{< faq q="What is the tipping point of microservices?" >}}
The tipping point occurs when a system handles large data and high-frequency inter-service messaging. At this scale, network I/O and data serialization/deserialization costs exceed the actual compute cost, making a Monolith (in-memory execution) significantly cheaper.
{{< /faq >}}

{{< faq q="How much did Segment save by migrating to a monolith?" >}}
By consolidating 140 microservices into a single Monolithic Worker, Segment saved over $250,000 in cloud infrastructure costs in just their first year while significantly reducing engineering operational overhead.
{{< /faq >}}
