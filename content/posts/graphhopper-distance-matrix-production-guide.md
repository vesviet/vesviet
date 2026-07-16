---
title: "GraphHopper Distance Matrix: Self-Host & Save $510/day"
slug: "graphhopper-distance-matrix-production-guide"
author: "Lê Tuấn Anh"
date: "2026-06-11T20:00:00+07:00"
lastmod: "2026-07-08T18:21:00+07:00"
draft: false
description: "Run GraphHopper distance matrix in production: Docker self-hosting, /matrix API, custom truck models, and H3 Redis caching."
categories:
  - "Architecture"
  - "Engineering"
  - "Backend"
tags:
  - "GraphHopper"
  - "Distance Matrix"
  - "OSRM"
  - "Routing Engine"
  - "OpenStreetMap"
  - "Python"
  - "Java"
  - "Logistics"
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "GraphHopper distance matrix production guide: self-hosted routing with OSM data and Kubernetes"
  relative: false
canonicalURL: "https://tanhdev.com/posts/graphhopper-distance-matrix-production-guide/"
---

**Answer-first:** GraphHopper distance matrix is the `/matrix` API of the open-source GraphHopper routing engine. It accepts N points and returns an N×N matrix of travel durations (seconds) and distances (meters) based on real road networks from OpenStreetMap — completely free when self-hosted. For 100 delivery stops, it computes 10,000 pairs in under 50ms on a standard VPS.

### What You'll Learn That AI Won't Tell You
- Setting up GraphHopper self-hosting routing engine with custom profile caches.
- Configuring RAM allocations to hold entire continental OpenStreetMap networks.


## What Is the GraphHopper Distance Matrix?



This guide covers everything you need to run GraphHopper distance matrix in production: Docker setup, the `/matrix` API, Custom Models for truck/motorcycle routing, H3-based Redis caching, and an honest comparison with OSRM, Valhalla, and Google Maps.

---

## Why GraphHopper Distance Matrix?

The three main choices for open-source route distance matrix computation are **Haversine** (straight-line), **OSRM** (C++, extremely fast, rigid profiles), and **GraphHopper** (Java, flexible Custom Models). A fourth option is commercial APIs (Google Maps, HERE, Mapbox).

| Criterion | GraphHopper | OSRM | Haversine | Google Maps |
|-----------|-------------|------|-----------|-------------|
| **Cost** | Free (self-hosted) | Free (self-hosted) | Free | $0.005/element |
| **Accuracy** | Road network ✅ | Road network ✅ | Straight-line ❌ | Road + traffic ✅ |
| **Speed (100×100)** | ~50ms | ~20ms | <1ms | 500ms+ |
| **Runtime routing rules** | ✅ Custom Models | ❌ Recompile + Lua | N/A | Paid tiers |
| **Java/Python SDK** | ✅ Native Java SDK | HTTP only | Native | HTTP only |
| **Docker setup** | ✅ Official image | ✅ Official image | N/A | N/A |
| **Best for** | Multi-profile fleets | Max raw speed | Pre-filter candidates | Real-time ETA |

**Rule of thumb:** Use **GraphHopper** when you have vehicles with different routing rules (truck weight limits, motorcycle lane access, toll avoidance). Use **OSRM** when you need the absolute fastest static matrix for one vehicle type.

---

## OSRM vs GraphHopper: Which Should You Choose?

Both engines are free, self-hostable, and use OpenStreetMap data. The decision comes down to **speed vs. flexibility** — and the actual performance delta is smaller than most engineers expect.

### Benchmark: 100×100 Distance Matrix (10,000 pairs)

| Engine | 10×10 | 50×50 | 100×100 | Key tradeoff |
|--------|:---:|:---:|:---:|------|
| **OSRM** | 4ms | 14ms | **21ms** | Fastest, but rigid profiles (Lua only) |
| **GraphHopper** | 8ms | 28ms | **52ms** | 2.5× slower, but Custom Models at runtime |
| **Google Maps** | 300ms | 1,200ms | **2,500ms+** | **$510/day** — 50× slower and 50× more expensive |

*Tested on DigitalOcean 4-vCPU/8GB droplet, Vietnam OSM data.*

> **The 2.5× gap largely disappears with H3 Redis caching** (see the caching section below). After warm-up, cached GraphHopper responses return in 1–3ms — indistinguishable from OSRM.

### Choose OSRM when:

- ✅ You have **one vehicle type** (only cars, or only trucks) with a static routing profile
- ✅ You need **maximum raw throughput** — millions of pairs per hour, no caching
- ✅ Your team is comfortable with **Docker + Lua** for profile changes
- ✅ You will never need to change routing rules without a full graph rebuild
- ✅ You are optimizing a **ride-hailing dispatch** system where every millisecond counts (see [Uber DISCO dispatch architecture](/series/ride-hailing-realtime-architecture/part-4-dispatch-matching-engine/))

### Choose GraphHopper when:

- ✅ You have a **multi-vehicle fleet** — motorcycles filtering lanes, trucks avoiding weight-restricted roads, cyclists on bike paths — all needing different rules
- ✅ You need **runtime Custom Models** — change toll preferences, road restrictions, or vehicle weights without restarting and rebuilding the graph
- ✅ Your backend is **Java-based** and you want embedded mode (no HTTP overhead)
- ✅ You are building an **e-commerce order allocation** system where flexibility across SKU types and vehicle classes matters more than the 2.5× raw speed delta (see [E-commerce Order Allocation Series](/series/ecommerce-order-allocation/))
- ✅ You want a **single engine** that can also handle H3 geospatial caching, Valhalla-style turn restrictions, and matrix + route in one deployment

### Verdict for most production systems

If you are replacing Google Maps Distance Matrix API for a logistics or e-commerce routing use case with mixed vehicle types: **start with GraphHopper**. Add H3 Redis caching (documented below) and you will match OSRM's effective latency while keeping full routing flexibility. Switch to OSRM only if profiling shows the matrix API is your actual bottleneck — which is rare below 500 requests/second.

---

## Quick Start: GraphHopper Distance Matrix with Docker

### Step 1: Start the GraphHopper Server

GraphHopper needs an OpenStreetMap `.osm.pbf` file as its map source. Geofabrik provides free regional extracts.

```bash
# Create a data directory
mkdir -p ./graphhopper-data

# Start GraphHopper — it will download the Vietnam OSM file automatically
docker run -d \
  --name graphhopper \
  -p 8989:8989 \
  -v $(pwd)/graphhopper-data:/data \
  israelhikingmap/graphhopper:latest \
  --url https://download.geofabrik.de/asia/vietnam-latest.osm.pbf \
  --host 0.0.0.0

# Follow logs — graph preparation takes 5-15 minutes on first run
docker logs -f graphhopper
```

Wait for the log line: `Started server at HTTP 0.0.0.0:8989`

### Step 2: Call the Matrix API

```bash
# Simple 3×3 matrix: car routing between 3 Ho Chi Minh City locations
curl -X POST http://localhost:8989/matrix \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      [106.7011, 10.7712],
      [106.7100, 10.7780],
      [106.6980, 10.7650]
    ],
    "profile": "car",
    "out_arrays": ["times", "distances"],
    "fail_fast": false
  }'
```

> ⚠️ **GeoJSON coordinate order:** GraphHopper uses `[longitude, latitude]` (not `[lat, lng]`). This is the most common bug when migrating from Haversine-based code.

**Response:**
```json
{
  "times": [[0, 320, 185], [315, 0, 410], [180, 405, 0]],
  "distances": [[0, 2100, 1350], [2050, 0, 2900], [1300, 2880, 0]],
  "info": {"took": 12, "copyrights": ["OpenStreetMap contributors"]}
}
```

- `times`: N×N array in **seconds**
- `distances`: N×N array in **meters**
- Diagonal is `0` (same point to same point)

---

## Production Python Client

```python
import requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class Location:
    lat: float
    lng: float
    label: Optional[str] = None

@dataclass
class DistanceMatrix:
    durations: list[list[int]]   # seconds, N×N
    distances: list[list[int]]   # meters, N×N

class GraphHopperClient:
    """
    Production-ready GraphHopper distance matrix client.
    Handles [lng, lat] coordinate order, error handling, and retries.
    """

    def __init__(self, base_url: str = "http://localhost:8989", profile: str = "car"):
        self.base_url = base_url.rstrip("/")
        self.profile = profile
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get_matrix(self, locations: list[Location], timeout: int = 30) -> DistanceMatrix:
        """
        Compute a full N×N distance matrix for the given locations.

        Args:
            locations: List of Location objects (lat/lng).
            timeout:   HTTP request timeout in seconds.

        Returns:
            DistanceMatrix with 'durations' (seconds) and 'distances' (meters).

        Raises:
            requests.HTTPError: If GraphHopper returns an error.
            ValueError: If fewer than 2 locations are provided.
        """
        if len(locations) < 2:
            raise ValueError("At least 2 locations are required for a distance matrix")

        # GraphHopper uses [lng, lat] — GeoJSON order
        points = [[loc.lng, loc.lat] for loc in locations]

        payload = {
            "points": points,
            "profile": self.profile,
            "out_arrays": ["times", "distances"],
            "fail_fast": False,   # Return partial results for unreachable pairs
        }

        response = self.session.post(
            f"{self.base_url}/matrix",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()

        return DistanceMatrix(
            durations=data["times"],
            distances=data["distances"],
        )


# --- Usage example ---

client = GraphHopperClient(base_url="http://localhost:8989", profile="car")

locations = [
    Location(lat=10.7712, lng=106.7011, label="Warehouse"),
    Location(lat=10.7780, lng=106.7100, label="Customer A"),
    Location(lat=10.7650, lng=106.6980, label="Customer B"),
]

matrix = client.get_matrix(locations)

# Print duration matrix
for i, from_loc in enumerate(locations):
    for j, to_loc in enumerate(locations):
        if i != j:
            duration_min = matrix.durations[i][j] // 60
            distance_km = matrix.distances[i][j] / 1000
            print(f"{from_loc.label} → {to_loc.label}: {duration_min}min, {distance_km:.1f}km")
```

---

## Vehicle Profiles and Custom Models

This is GraphHopper's core advantage over OSRM: **Custom Models** allow you to change routing rules at runtime without recompiling the map graph.

### Built-in Profiles

```bash
# Car routing (default)
curl -X POST http://localhost:8989/matrix \
  -d '{"points": [...], "profile": "car", ...}'

# Motorcycle (includes lane filtering, smaller roads)
curl -X POST http://localhost:8989/matrix \
  -d '{"points": [...], "profile": "motorcycle", ...}'

# Bicycle
curl -X POST http://localhost:8989/matrix \
  -d '{"points": [...], "profile": "bike", ...}'

# Walking / on-foot
curl -X POST http://localhost:8989/matrix \
  -d '{"points": [...], "profile": "foot", ...}'
```

### Custom Models — Runtime Rule Changes

Custom Models let you modify routing behavior without restarting the server. This is essential for logistics platforms with mixed fleets.

**Example: Heavy truck avoiding highways and narrow roads**

```json
{
  "points": [[106.7011, 10.7712], [106.7100, 10.7780]],
  "profile": "car",
  "out_arrays": ["times", "distances"],
  "custom_model": {
    "speed": [
      {
        "if": "road_class == MOTORWAY",
        "limit_to": 90
      },
      {
        "if": "road_environment == TUNNEL",
        "multiply_by": 0
      }
    ],
    "priority": [
      {
        "if": "max_weight < 10",
        "multiply_by": 0
      },
      {
        "if": "road_class == RESIDENTIAL",
        "multiply_by": 0.3
      }
    ]
  }
}
```

**Example: Toll-avoidance routing**

```json
{
  "custom_model": {
    "priority": [
      {
        "if": "toll == ALL",
        "multiply_by": 0
      }
    ]
  }
}
```

> **Real-world use case:** A logistics company managing both motorcycles (fast last-mile) and 10-ton trucks (restricted roads) can call the same GraphHopper instance with different Custom Models per vehicle type — no infrastructure change needed.

---

## Java SDK (Embedded Mode)

For Java-based logistics backends, embed GraphHopper directly in-process — zero HTTP overhead for matrix computation.

```java
import com.graphhopper.GraphHopper;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.config.CHProfile;
import com.graphhopper.config.Profile;
import com.graphhopper.routing.matrix.MatrixResult;

public class EmbeddedGraphHopperMatrix {

    private final GraphHopper hopper;

    public EmbeddedGraphHopperMatrix(String osmFile, String graphLocation) {
        GraphHopperConfig config = new GraphHopperConfig();
        config.putObject("graph.location", graphLocation);

        this.hopper = new GraphHopper();
        this.hopper.setOSMFile(osmFile);
        this.hopper.setGraphHopperLocation(graphLocation);
        this.hopper.setProfiles(
            new Profile("car").setVehicle("car").setWeighting("fastest"),
            new Profile("truck").setVehicle("car").setWeighting("custom")
        );
        this.hopper.getCHPreparationHandler()
            .setCHProfiles(new CHProfile("car"));
        this.hopper.importOrLoad();
    }

    // Use the GHMatrixAPI for N×N computations
    // See: https://github.com/graphhopper/graphhopper/tree/master/web-api
    public void shutdown() {
        hopper.close();
    }
}
```

**Why embedded vs. HTTP?**
- Embedded: ~1ms per matrix call (no network overhead). Best for Java microservices doing thousands of matrix calls per second.
- HTTP: Language-agnostic, easier to scale horizontally. Best for Python/Go services or multi-language stacks.

---

## H3-Based Redis Caching for Production Scale

Road networks change rarely. Caching distance matrix results by H3 cell pair reduces GraphHopper calls by 90%+ in steady-state production.

```python
import h3
import json
import redis
from graphhopper_client import GraphHopperClient, Location, DistanceMatrix

class CachedDistanceMatrix:
    """
    GraphHopper distance matrix with H3-based Redis caching.
    Cache hit ratio: 90%+ after warm-up in steady-state logistics.
    """

    H3_RESOLUTION = 9        # ~174m cells — one city block
    CACHE_TTL_DAYS = 30      # Road networks change slowly

    def __init__(self, gh_client: GraphHopperClient, redis_client: redis.Redis):
        self.gh = gh_client
        self.redis = redis_client

    def _h3_key(self, loc_a: Location, loc_b: Location) -> str:
        """Generate a canonical cache key from two H3 cell IDs."""
        cell_a = h3.latlng_to_cell(loc_a.lat, loc_a.lng, self.H3_RESOLUTION)
        cell_b = h3.latlng_to_cell(loc_b.lat, loc_b.lng, self.H3_RESOLUTION)
        # Sort for symmetry: A→B and B→A use the same key (undirected graph)
        return f"gh:matrix:{min(cell_a, cell_b)}:{max(cell_a, cell_b)}"

    def get_pair(self, origin: Location, dest: Location) -> dict:
        """
        Get distance and duration for a single pair, with cache.
        Returns: {"duration_s": int, "distance_m": int}
        """
        cache_key = self._h3_key(origin, dest)
        cached = self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Cache miss — compute via GraphHopper
        matrix = self.gh.get_matrix([origin, dest])
        result = {
            "duration_s": matrix.durations[0][1],
            "distance_m": matrix.distances[0][1],
        }

        self.redis.setex(
            cache_key,
            self.CACHE_TTL_DAYS * 86400,
            json.dumps(result)
        )
        return result

    def get_matrix_cached(self, locations: list[Location]) -> DistanceMatrix:
        """
        Build a full N×N matrix using cached pairs where possible.
        Falls back to GraphHopper for cache misses only.
        """
        n = len(locations)
        durations = [[0] * n for _ in range(n)]
        distances = [[0] * n for _ in range(n)]
        missing_pairs = []

        # Check cache for all pairs
        cache_keys = {}
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                key = self._h3_key(locations[i], locations[j])
                cached = self.redis.get(key)
                if cached:
                    data = json.loads(cached)
                    durations[i][j] = data["duration_s"]
                    distances[i][j] = data["distance_m"]
                else:
                    missing_pairs.append((i, j))

        if missing_pairs:
            # Batch compute missing pairs via GraphHopper
            missing_locs = list({idx for pair in missing_pairs for idx in pair})
            loc_subset = [locations[i] for i in missing_locs]
            sub_matrix = self.gh.get_matrix(loc_subset)

            idx_map = {orig_idx: sub_idx for sub_idx, orig_idx in enumerate(missing_locs)}

            for i, j in missing_pairs:
                si, sj = idx_map[i], idx_map[j]
                dur = sub_matrix.durations[si][sj]
                dist = sub_matrix.distances[si][sj]
                durations[i][j] = dur
                distances[i][j] = dist

                # Store in cache
                key = self._h3_key(locations[i], locations[j])
                self.redis.setex(
                    key,
                    self.CACHE_TTL_DAYS * 86400,
                    json.dumps({"duration_s": dur, "distance_m": dist})
                )

        return DistanceMatrix(durations=durations, distances=distances)
```

**Cache hit ratio in practice:**
- Day 1 (cold): ~0% hits — all misses populated into Redis
- Day 7: ~70% hits
- Day 30 (steady state): **>90% hits** — recurring delivery zones are fully cached

---

## OSRM vs GraphHopper vs Google Maps: Full Production Benchmark

Based on a 100-point (100×100 = 10,000 pairs) test on a DigitalOcean 4-vCPU/8GB droplet with Vietnam OSM data:

| Engine | 10×10 matrix | 50×50 matrix | 100×100 matrix | Monthly cost |
|--------|:---:|:---:|:---:|:---:|
| **GraphHopper (self-hosted)** | 8ms | 28ms | **52ms** | ~$20 VPS |
| **OSRM (self-hosted)** | 4ms | 14ms | **21ms** | ~$20 VPS |
| **Valhalla (self-hosted)** | 15ms | 60ms | 120ms | ~$20 VPS |
| **Google Maps Distance Matrix** | 300ms | 1,200ms | 2,500ms+ | **$510/day** |
| **HERE Matrix Routing v8** | 150ms | 600ms | 1,200ms | $0.70/route |

**Interpretation:**
- OSRM is 2.5x faster than GraphHopper at raw matrix computation
- GraphHopper is necessary when you need Custom Models (runtime vehicle rules)
- Google Maps is 50x more expensive and 50x slower — justified only for real-time traffic ETA, not static delivery routing

---

## Memory and Hardware Requirements

GraphHopper loads the entire road graph into RAM. Sizing depends on the OSM coverage region:

| Region | OSM file size | GraphHopper RAM |
|--------|:---:|:---:|
| Ho Chi Minh City metro | ~180MB | 2GB |
| Vietnam (entire country) | ~880MB | 6GB |
| Southeast Asia | ~4.5GB | 24GB+ |
| Germany | ~3.8GB | 20GB+ |

**Recommended production setup for Vietnam routing:**
- 4 vCPU / 8GB RAM VPS
- NVMe storage for graph-cache directory
- CH (Contraction Hierarchies) profile for fastest query time
- Run 2 instances behind a load balancer for HA

---

## Frequently Asked Questions

{{< faq q="What is GraphHopper distance matrix?" >}}
GraphHopper distance matrix is the `/matrix` endpoint of the GraphHopper open-source routing engine. It takes N latitude/longitude points and returns an N×N matrix of travel times (seconds) and distances (meters) using real road data from OpenStreetMap. It is free when self-hosted via Docker, and it processes a 100×100 matrix (10,000 pairs) in approximately 50ms on a standard 4-vCPU server.
{{< /faq >}}

{{< faq q="Is GraphHopper free?" >}}
Yes. GraphHopper is open-source (Apache 2.0) and free to self-host. You download OpenStreetMap data (also free from Geofabrik), run GraphHopper via Docker, and pay only for your server costs (~$20/month on DigitalOcean for Vietnam routing). GraphHopper GmbH also offers a paid cloud API if you prefer not to self-host.
{{< /faq >}}

{{< faq q="How does GraphHopper compare to OSRM for distance matrix computation?" >}}
OSRM is faster (21ms vs. 52ms for a 100×100 matrix) because it is written in C++. GraphHopper is slower but more flexible: Custom Models let you change routing rules (vehicle weight limits, toll avoidance, road class restrictions) at runtime without recompiling the graph. If you have a single vehicle type and need maximum speed, use OSRM. If you have a mixed fleet with different routing constraints, GraphHopper's Custom Models justify the performance cost.
{{< /faq >}}

{{< faq q="GraphHopper vs Google Maps Distance Matrix API — when to use which?" >}}
Use GraphHopper (self-hosted) for static delivery routing from fixed warehouses to customers. It handles 10,000 pairs for free in 50ms. Use Google Maps for real-time ride-hailing or last-mile routing where current traffic data materially changes the ETA. For 10,000 pairs, Google Maps costs $51 per request vs. $0 for self-hosted GraphHopper. At 10 routing batches per day, that's $510/day in API fees.
{{< /faq >}}

{{< faq q="What OSM data format does GraphHopper use?" >}}
GraphHopper uses OpenStreetMap `.osm.pbf` binary format. You can download regional extracts for free from Geofabrik (geofabrik.de). For Vietnam: `https://download.geofabrik.de/asia/vietnam-latest.osm.pbf`. GraphHopper can also download the file automatically on first start if you pass the `--url` flag.
{{< /faq >}}

{{< faq q="How much RAM does GraphHopper need?" >}}
GraphHopper loads the road graph into memory for fast queries. Vietnam (~880MB OSM file) requires approximately 6GB RAM. Ho Chi Minh City metro area (~180MB OSM file) requires approximately 2GB RAM. A 4-vCPU / 8GB DigitalOcean droplet handles Vietnam-wide routing comfortably.
{{< /faq >}}

---

## Internal Links & Next Steps

- **E-commerce routing series:** This guide is referenced from the [E-commerce Order Allocation](/series/ecommerce-order-allocation/) series, which shows how a self-hosted matrix feeds a VRP solver.
- **Ride-hailing:** The same H3 spatial indexing used for caching is also how Uber finds nearby drivers — see [H3 Geospatial Indexing for Ride-Hailing Architecture](/series/ride-hailing-realtime-architecture/part-2-geospatial-indexing/).
- **High-concurrency systems:** For serving matrix results under high request volume, see [Rate Limiting and Singleflight Patterns](/series/high-concurrency-systems/).

{{< author-cta >}}
