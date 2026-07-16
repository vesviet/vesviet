---
title: "Part 2: Zero to Hero Environment Setup (Docker, OSM, Golang)"
description: "A complete, production-ready guide to setting up a local Graphhopper routing engine with OpenStreetMap data and a high-performance Golang API client."
date: "2026-06-14T22:45:00+07:00"
lastmod: "2026-06-14T22:45:00+07:00"
draft: false
tags: ["golang", "docker", "graphhopper", "osm"]
series: ["Routing & Geospatial Architecture"]
series_order: 2
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "Geospatial and Routing Engine Architecture series: Go and GraphHopper for production routing"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/routing-geospatial-architecture/part-2-environment-setup/"
ShowToc: true
TocOpen: true
---

[← Series hub]({{< ref "/series/routing-geospatial-architecture/_index.md" >}})
[← Prev]({{< ref "/series/routing-geospatial-architecture/part-1-core-algorithms.md" >}}) • [Next →]({{< ref "/series/routing-geospatial-architecture/part-3-spatial-indexing.md" >}})

> **Prerequisite:** Before starting this part, ensure you have read [Part 1: Core Routing Algorithms — A* & Dijkstra Visualized]({{< ref "part-1-core-algorithms.md" >}}).

Setting up a local routing engine is notoriously difficult. Most generic tutorials offer a basic Docker command that crashes silently, leaving developers confused. 

In this guide, we bypass the basic "Hello World" setups. We will build a production-grade local environment integrating **OpenStreetMap (OSM)** data, a properly tuned **Graphhopper (Java)** Docker container, and a high-concurrency **Golang API Gateway**.

## 1. Downloading and Cropping Map Data

**Answer-first:** Download raw OpenStreetMap data in `.osm.pbf` format from the Geofabrik server. To save gigabytes of RAM during local development, use `osmium extract` to crop the massive country-level map down to a single city bounding box.

The industry standard source for raw map data is [download.geofabrik.de](https://download.geofabrik.de/). You must download the **Protocolbuffer Binary Format (.osm.pbf)**, as it is highly compressed and optimized for routing engines.

However, loading an entire country (e.g., `vietnam-latest.osm.pbf`) into memory requires upwards of 16GB of RAM. For local development on a standard laptop, this is a silent killer.

**Pro-tip: Osmium Cropping**
Install the `osmium-tool` and crop the map to a specific bounding box (e.g., Ho Chi Minh City):

```bash
# Crop map to bounding box: min_lon, min_lat, max_lon, max_lat
osmium extract -b 106.5,10.7,106.8,10.9 vietnam-latest.osm.pbf -o hcmc.osm.pbf
```
This reduces your map file from Gigabytes to Megabytes, ensuring lightning-fast startup times.

## 2. Running Graphhopper via Docker Compose

**Answer-first:** Run Graphhopper using the official `graphhopper/graphhopper:latest` image. You **must** allocate sufficient heap space using `JAVA_OPTS=-Xmx6g` to prevent Out-Of-Memory (OOM) crashes during the initial `.pbf` import phase.

Create a `docker-compose.yml` file to manage your routing engine. Notice the critical volume mappings and environment variables:

```yaml
version: '3'
services:
  graphhopper:
    image: graphhopper/graphhopper:latest
    ports:
      - "8989:8989"
    volumes:
      - ./data:/data         # Maps your PBF file
      - ./config:/config     # Maps your config.yml
      - ./srtm:/data/srtm    # Critical: Cache for Elevation Data
    environment:
      - JAVA_OPTS=-Xmx6g     # Prevent OOM crashes during import
    command: >
      --input /data/hcmc.osm.pbf
      --graph-location /data/graph-cache
      --config /config/config.yml
```

## 3. Configuring Custom Models (Toll Roads & Elevation)

**Answer-first:** Edit `config.yml` to define Custom Models (e.g., avoiding toll roads) under the `priority` section. To enable 3D uphill/downhill routing, activate the `srtm` elevation provider. **Crucial:** You must delete the `graph-cache` folder whenever you change these rules.

To instruct the engine to avoid toll roads, define a custom weighting profile:

```yaml
profiles:
  - name: my_car_no_tolls
    vehicle: car
    weighting: custom
    custom_model:
      priority:
        - if: "toll != NO"
          multiply_by: 0.0
```

To enable ETA calculations that account for steep hills, enable SRTM elevation data. Ensure your Docker compose maps the `cache_dir` so you don't re-download gigabytes of terrain data on every restart:

```yaml
graph:
  elevation:
    provider: srtm
    cache_dir: /data/srtm
```

## 4. The Golang API Gateway (Preventing Socket Exhaustion)

**Answer-first:** When writing a Golang client to call the Graphhopper Matrix API, you must configure a custom `http.Transport` with a high `MaxIdleConnsPerHost` (e.g., 100) and set an explicit `Timeout`. The default Go client will cause catastrophic socket exhaustion under high load.

By default, Go's `http.Client` only allows **2 idle connections per host**. If your microservice fires 50 concurrent Matrix requests to Graphhopper, Go opens and closes 48 new TCP connections every second. This leads to massive `TIME_WAIT` spikes and port exhaustion.

Here is the production-grade Golang setup:

```go
package main

import (
	"net/http"
	"time"
)

// Define a globally reused transport and client
var routingTransport = &http.Transport{
	MaxIdleConns:        100,
	MaxIdleConnsPerHost: 100, // CRITICAL: Overrides the default limit of 2
	IdleConnTimeout:     90 * time.Second,
}

var routingClient = &http.Client{
	Transport: routingTransport,
	Timeout:   15 * time.Second, // CRITICAL: Prevent goroutine leaks
}
```

When hitting the `POST /matrix` endpoint, Graphhopper strictly expects GeoJSON coordinate formatting: `[Longitude, Latitude]`.

## Docker Compose Network Boundaries & Topology

In a production-like environment, keeping services in a single default Docker network is a security and performance risk. We split our services into two network boundaries:

1. **`routing-edge` (Public network boundary):** Only the Golang API Gateway container has access to this network. It handles public traffic from client apps (port 8080/443).
2. **`routing-internal` (Private network boundary):** This network is strictly internal. The Graphhopper routing engine and Redis caching layers live here. The Golang API Gateway is the only bridge between the public-facing edge and the internal backend. Graphhopper (port 8989) and Redis (port 6379) are not exposed to the public internet, preventing unauthorized routing queries or cache tampering.

Here is the updated configuration illustrating this isolation:

```yaml
version: '3.8'

networks:
  routing-edge:
    driver: bridge
  routing-internal:
    internal: true

services:
  gateway:
    image: my-golang-gateway:latest
    ports:
      - "8080:8080"
    networks:
      - routing-edge
      - routing-internal
    depends_on:
      - graphhopper
      - redis

  graphhopper:
    image: graphhopper/graphhopper:latest
    volumes:
      - ./data:/data
    networks:
      - routing-internal
    environment:
      - JAVA_OPTS=-Xmx6g

  redis:
    image: redis:7-alpine
    networks:
      - routing-internal
```

## Hugo and OSM Data Import Workflows

Building this series locally also requires running the Hugo content site and integrating OpenStreetMap datasets.

- **Hugo Dependencies:** The website uses Hugo Extended version 0.120+ to compile the SCSS and process asset pipelines. Ensure your host has Dart Sass installed to compile layout overrides.
- **OSM Data Import Pipelines:** While the `osmium` tool extracts bounding boxes, automating this in a CI/CD environment or a local shell script is highly recommended. The import script should curl the `.pbf` data, check its MD5 checksum, run `osmium extract`, and finally delete the raw country-wide file to keep the disk footprint minimal.

## Deep Dive: Tuning GraphHopper config.yml

To move from a basic local playground to a high-throughput production routing engine, we must customize GraphHopper's `config.yml`. Below is an annotated breakdown of the crucial settings required for high-scale operations:

```yaml
graphhopper:
  # Enable Contraction Hierarchies (CH) for sub-millisecond query speed
  prepare.ch.weightings: [fastest]
  prepare.ch.profiles:
    - name: car_profile
  
  # Specify the active routing profiles (must match the profiles compiled in the graph cache)
  profiles:
    - name: car_profile
      vehicle: car
      weighting: fastest
      turn_costs: true # Enable edge-based routing for realistic turn restrictions
  
  # Cache settings to accelerate lookups
  graph.dataaccess: RAM_STORE # Keep routing graph completely in memory for peak performance
  
  # Limit the size of coordinate lists to prevent malicious denial-of-service memory exhaustion
  routing.max_visited_nodes: 1000000
```

### Explaining the Parameters:
- `prepare.ch.profiles`: By pre-calculating CH profiles, we bake in the optimal shortcuts. This increases the import time and RAM usage slightly but reduces the runtime query latency by 100x.
- `turn_costs: true`: By default, routing engines treat intersections as zero-cost nodes. In reality, making a left turn across a four-lane highway takes significantly longer than a right turn. Setting `turn_costs` to true forces GraphHopper to build an edge-based graph rather than a node-based graph. This doubles the memory footprint of the graph but yields highly realistic ETA routing paths.
- `graph.dataaccess: RAM_STORE`: GraphHopper offers multiple data access storage methods: `MMAP` (memory-mapped files) and `RAM_STORE` (direct heap allocation). For developer environments, `MMAP` is fine, but in production, `RAM_STORE` provides direct heap-allocated access, avoiding disk I/O bottlenecks and ensuring the lowest possible latency variance.

## Automated OSM Data Pipeline Script

Manually downloading and extracting map files is prone to human error. Below is a complete Bash script (`import_osm.sh`) that automates this workflow:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configurations
REGIONAL_URL="https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf"
RAW_FILE="./data/berlin-latest.osm.pbf"
EXTRACTED_FILE="./data/berlin-central.osm.pbf"
BBOX="13.3,52.45,13.5,52.55" # Berlin center bounding box

echo "Step 1: Creating data directory..."
mkdir -p ./data

echo "Step 2: Downloading regional PBF from Geofabrik..."
curl -L -o "${RAW_FILE}" "${REGIONAL_URL}"

echo "Step 3: Extracting bounding box using Osmium..."
osmium extract \
  --bbox "${BBOX}" \
  --output "${EXTRACTED_FILE}" \
  "${RAW_FILE}" --overwrite

echo "Step 4: Cleaning up raw large PBF file..."
rm "${RAW_FILE}"

echo "OSM pipeline finished successfully. Target file: ${EXTRACTED_FILE}"
```

This script can be easily scheduled as a CronJob in Kubernetes or as part of a Jenkins/GitHub Actions pipeline, guaranteeing that your routing engine is always running on recent geographical data.

---

## FAQ: Production Troubleshooting

{{< faq q="Why does my Graphhopper Docker container crash immediately after starting?" >}}
This is almost always an OOM (Out of Memory) error during the initial `.osm.pbf` graph import. You must set the `JAVA_OPTS=-Xmx4g` (or higher) environment variable in your docker-compose file.
{{< /faq >}}

{{< faq q="I changed my config.yml to avoid toll roads, but it still routes through them. Why?" >}}
This is the 'Graph-Cache Trap'. Graphhopper does not hot-reload topology rules. You must manually delete the `graph-cache` directory to force the engine to re-import the OSM data and bake in your new custom model.
{{< /faq >}}

{{< faq q="My laptop doesn't have 16GB of RAM to process the entire country. What should I do?" >}}
Use the `osmium extract` command-line tool. You can crop a massive 2GB national PBF file down to a tiny 50MB city bounding box before feeding it into Graphhopper, saving vast amounts of RAM.
{{< /faq >}}

{{< faq q="What if the OpenStreetMap data is missing my company's private warehouse roads?" >}}
OSM data is entirely extensible. You can use desktop tools like JOSM to draw your private roads, export them as a `.osm` XML file, and merge them with the Geofabrik PBF file before processing.
{{< /faq >}}

{{< faq q="Why is the Matrix API returning errors about 'invalid coordinate format'?" >}}
Unlike Google Maps which expects `[Latitude, Longitude]`, the Graphhopper Matrix POST API strictly requires GeoJSON array formatting: `[Longitude, Latitude]`.
{{< /faq >}}

{{< faq q="Why does my Golang API Gateway hang forever when requesting a massive 1000x1000 Matrix?" >}}
Graphhopper can take several seconds to compute massive matrices. If your Golang `http.Client` lacks an explicit `Timeout`, the calling goroutine will block indefinitely, leading to memory leaks and a frozen API.
{{< /faq >}}

{{< faq q="Does self-hosting Graphhopper mean I have unlimited Matrix API calls?" >}}
Yes, you bypass external API subscription limits. However, you are strictly bound by your server's RAM. Requesting a 10,000x10,000 matrix will instantly cause a Java Out-Of-Memory crash if you haven't allocated enough heap space.
{{< /faq >}}

Need help building high-scale routing engines or spatial indexing pipelines? [Contact me](/contact/) to discuss your project.

🔗 **Next Step:** Learn about spatial indexing in [Part 3: Spatial Indexing (Uber H3, PostGIS & Redis GEO)]({{< ref "/series/routing-geospatial-architecture/part-3-spatial-indexing.md" >}}).

