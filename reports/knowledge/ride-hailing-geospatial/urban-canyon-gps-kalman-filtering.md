# Urban Canyon GPS Multipath Mitigation: Extended Kalman Filtering & Map Matching

> **Domain:** Ride-Hailing & Geospatial | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `GPS Multipath Reflection`, `Extended Kalman Filter (EKF)`, `Hidden Markov Model (HMM)`

---

## 1. Problem Statement & Operational Context
In dense urban skyscraper corridors (e.g. Hong Kong, Singapore, Ho Chi Minh City District 1), satellite signals bounce off glass facades. Raw smartphone GPS points scatter erratically by up to 50 meters, causing inaccurate fares and erroneous turns.

## 2. Core Architectural Invariants
1. **Sensor Fusion via EKF:** Combine raw GPS measurements with smartphone IMU accelerometer and gyroscope readings to smooth physical trajectories.
2. **Hidden Markov Model (HMM) Map Matching:** Project noisy spatial coordinates onto the underlying road network graph (OSRM / OpenStreetMap), calculating highest-probability paths.

## 3. Agent Retrieval Guidance
- **Apply When:** Processing vehicle telematics, fleet tracking, or map navigation routing.
- **Related Articles:** `/posts/osrm-vs-graphhopper-architecture-comparison/`.
