---
title: "Part 5: Route Visualization UI with Mapbox & Deck.gl"
description: "Visualizing 100,000 vehicle paths without freezing the browser. Unlocking WebGL GPU rendering with Deck.gl and Mapbox."
date: "2026-06-14T23:05:00+07:00"
lastmod: "2026-06-14T23:05:00+07:00"
draft: false
tags: ["mapbox", "deck.gl", "webgl", "frontend", "geospatial", "ui"]
series: ["Routing & Geospatial Architecture"]
series_order: 5
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "Geospatial and Routing Engine Architecture series: Go and GraphHopper for production routing"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/routing-geospatial-architecture/part-5-visualization-ui/"
---

Rendering a single route on Google Maps is trivial. Rendering 100,000 historical vehicle routes, Origin-Destination matrices, and dynamic H3 geofences simultaneously? That requires offloading computation from the browser's CPU to the GPU using WebGL.

**Answer-first:** Do not use native Mapbox GL JS to render massive, dynamic datasets. Modifying the DOM or standard Mapbox sources with thousands of updates per second will freeze the browser. The industry standard is to use **deck.gl** paired with `MapboxOverlay`. This allows Deck.gl to render raw data directly onto the GPU while perfectly synchronizing with Mapbox's camera.

---

## 1. The GeoJSON and Polyline Traps

When your Golang API returns a route from Graphhopper, it usually comes as an "Encoded Polyline". Most frontend developers immediately grab `@mapbox/polyline` to decode it.

**The Performance Hack:** Decoding polylines in Javascript blocks the Main Thread. The smartest approach is to pass `points_encoded=false` in your backend Graphhopper request. It will return a raw GeoJSON `LineString`. You can feed this directly into Deck.gl or Mapbox without running a single line of decoding logic.

**The Coordinate Order Bug:** If you *do* decode the polyline manually, the array is returned as `[Latitude, Longitude]`. However, Mapbox and GeoJSON strictly require `[Longitude, Latitude]`. If you forget to reverse the array, your route will suddenly appear swimming in the middle of the Pacific Ocean.

---

## 2. Massive Rendering with Deck.gl

To render massive datasets, use the `MapboxOverlay` with `interleaved: true`. This injects Deck.gl directly into the Mapbox WebGL context, allowing your routes to render behind Mapbox text labels and 3D buildings.

### Time-lapse Animations (60 FPS)
To animate 100,000 vehicles over a 24-hour period, a junior developer might use a `setInterval` and `data.filter()` to update the array every frame. This will instantly kill the browser tab.

The Senior solution is the **DataFilterExtension**. You upload all 24 hours of data to the GPU memory exactly *once*. Inside your animation loop (using `requestAnimationFrame`), you update a single "Shader Uniform" (`filterRange`). The GPU instantly discards vertices outside the time window, achieving buttery smooth 60 FPS animations.

### Rendering H3 Hexagons without the Bloat
When visualizing H3 grids (like driver density zones), do not generate GeoJSON polygons on the backend. A city-wide grid in GeoJSON can easily weigh 50MB.

Instead, send only the 15-character H3 ID string (e.g., `8928308280fffff`). On the frontend, use Deck.gl's `H3HexagonLayer`. The library will use mathematical shaders to draw the perfect hexagon directly on the GPU, saving 99% of your network bandwidth.

*To handle millions of map and grid queries from the client without bottlenecking the backend, we need to implement Redis Semantic Caching. Explore this architecture in [Part 6: Location Clustering with Uber H3 & Redis Semantic Caching](/series/routing-geospatial-architecture/part-6-redis-semantic-caching/).*

---

## FAQ: WebGL & Mapbox Troubleshooting

{{< faq q="My Deck.gl routes are violently flickering against Mapbox terrain. How do I fix this?" >}}
This is a classic WebGL rendering glitch called **Z-Fighting**. Because your route and the map surface share the exact same Z-depth, the GPU doesn't know which one to draw first. Do not artificially raise the route's elevation. Instead, set `parameters: { polygonOffset: true, polygonOffsetFactor: -1 }` in your Deck.gl layer. This tricks the GPU depth buffer into prioritizing your layer without altering its physical height.
{{< /faq >}}

{{< faq q="My Mapbox map suddenly turned entirely white!" >}}
You hit a `WebGL Context Lost` error. This happens when the OS reclaims GPU memory (e.g., when the user plugs in a new 4K monitor or the GPU runs out of VRAM due to massive datasets). Your React/Vue application must listen for the `webglcontextlost` event and gracefully reload the Mapbox and Deck.gl instances to recover.
{{< /faq >}}
