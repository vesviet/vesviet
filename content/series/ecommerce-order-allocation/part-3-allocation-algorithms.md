---
title: "Phần 3 — Thuật toán phân bổ: Assignment Problem, Bin Packing & VRP"
slug: "part-3-allocation-algorithms"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "Ba họ thuật toán cốt lõi cho bài toán phân bổ đơn hàng: Assignment Problem (phân công tối ưu), Bin Packing (xếp đơn vào tài xế) và Vehicle Routing Problem (VRP)."
weight: 4
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-3-allocation-algorithms/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "Algorithms"
  - "VRP"
  - "Bin Packing"
  - "Optimization"
  - "OR-Tools"
cover:
  image: "/images/posts/default-post.png"
  alt: "Thuật toán phân bổ: Assignment Problem, Bin Packing & VRP"
  relative: false
---

[← Chương trước: Phần 2 — Inventory Management](/series/ecommerce-order-allocation/part-2-inventory-realtime/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 4 — Amazon CONDOR & Anticipatory Shipping →](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/)

---

> **Answer-first:** Thuật toán phân bổ đơn hàng kết hợp 3 bài toán tối ưu tổ hợp: Assignment Problem (phân công đơn-tài xế qua Hungarian O(n³)), Bin Packing (xếp đơn tối ưu capacity sàn/trần min-max) và Capacitated Vehicle Routing Problem (CVRP định tuyến lộ trình giao hàng), được giải đồng thời qua Google OR-Tools.

---

## Ba bài toán con

Phân bổ đơn hàng cho tài xế thực chất là tổng hợp của 3 bài toán kinh điển:

```
Bước 1: ASSIGNMENT — Đơn nào cho tài xế nào?
Bước 2: BIN PACKING — Mỗi tài xế nhận bao nhiêu đơn? (capacity constraint)
Bước 3: VRP — Tài xế đi giao theo lộ trình nào? (routing)

Trong thực tế, cả 3 bước thường được giải đồng thời.
```

---

## Bài toán 1: Assignment Problem (Bài toán phân công)

### Định nghĩa
Cho **N đơn hàng** và **M tài xế**, mỗi cặp (đơn, tài xế) có một **chi phí** (khoảng cách, thời gian, hoặc tiền). Tìm cách phân công sao cho **tổng chi phí nhỏ nhất**.

### Cost Matrix

```
            Driver 1   Driver 2   Driver 3   Driver 4
Order A  [    5          8          3          7     ]
Order B  [    9          4          6          2     ]
Order C  [    3          7          8          5     ]
Order D  [    6          2          4          9     ]

Mục tiêu: Gán mỗi Order cho 1 Driver sao cho tổng cost nhỏ nhất.
```

### Hungarian Algorithm — O(n³)

```
Bước 1: Trừ mỗi hàng cho giá trị nhỏ nhất của hàng đó
            D1   D2   D3   D4
  A  [   2    5    0    4  ]   (trừ 3)
  B  [   7    2    4    0  ]   (trừ 2)
  C  [   0    4    5    2  ]   (trừ 3)
  D  [   4    0    2    7  ]   (trừ 2)

Bước 2: Trừ mỗi cột cho giá trị nhỏ nhất của cột đó
            D1   D2   D3   D4
  A  [   2    5    0    4  ]
  B  [   7    2    4    0  ]
  C  [   0    4    5    2  ]
  D  [   4    0    2    7  ]
  (Cột 1 đã có 0, cột 2 đã có 0, cột 3 đã có 0, cột 4 đã có 0)

Bước 3: Tìm phân công sao cho mỗi hàng và cột chỉ chọn 1 ô có giá trị 0
  A → D3 (cost 3)
  B → D4 (cost 2)
  C → D1 (cost 3)
  D → D2 (cost 2)

  Tổng cost: 3 + 2 + 3 + 2 = 10 (tối ưu)
```

### Hạn chế trong thực tế
Hungarian Algorithm giả sử mỗi tài xế chỉ nhận **đúng 1 đơn**. Trong thực tế, 1 tài xế có thể nhận **nhiều đơn** (bounded by capacity) → cần Bin Packing.

---

## Bài toán 2: Bin Packing (Xếp thùng)

### Định nghĩa
Cho **N đơn hàng** (mỗi đơn có capacity cost khác nhau) và **M tài xế** (mỗi tài xế có max capacity). Xếp tất cả đơn vào các tài xế sao cho:
- Không tài xế nào vượt max capacity.
- Số tài xế sử dụng là **ít nhất** (hoặc tổng "lãng phí capacity" là nhỏ nhất).

### Ví dụ trực quan

```
Đơn hàng (capacity cost):
  Order A: 3  (3 thùng nước)
  Order B: 1  (1 điện thoại)
  Order C: 4  (4 thùng sữa)
  Order D: 2  (2 hộp mỹ phẩm)
  Order E: 5  (5 thùng bia)
  Order F: 2  (2 hộp giày)

Tài xế (min=2, max=8):

  Driver 1 [████████] max=8
  Driver 2 [████████] max=8
  Driver 3 [████████] max=8

Giải pháp First Fit Decreasing:
  Sắp xếp đơn giảm dần: E(5), C(4), A(3), D(2), F(2), B(1)

  Driver 1: E(5) + A(3) = 8/8 ████████ (đầy)
  Driver 2: C(4) + D(2) + F(2) = 8/8 ████████ (đầy)
  Driver 3: B(1) = 1/8 █        ← Chỉ có 1, < min_capacity(2)!

  Vấn đề: Driver 3 chỉ có 1 đơn, dưới min capacity!
```

### Bin Packing với Min-Max Capacity

Đây là biến thể đặc biệt của bài toán mà bạn cần:

```
Ràng buộc:
  ∀ driver d:  min_capacity(d) ≤ Σ order_capacity ≤ max_capacity(d)

Nếu không gán đủ min_capacity cho 1 tài xế → không dùng tài xế đó.
(Chuyến đi phải đủ đơn để có lời)
```

### Thuật toán Greedy cải tiến

```
Algorithm: MinMax-BinPacking

Input: orders[] (sorted by capacity DESC), drivers[] (sorted by max_capacity DESC)

1. Sắp xếp đơn hàng theo capacity giảm dần
2. Với mỗi đơn hàng:
   a. Tìm tài xế có remaining_capacity đủ chứa đơn
   b. Ưu tiên: tài xế nào gần min_capacity nhất nhưng chưa đạt → xếp vào
   c. Nếu không tài xế nào phù hợp → mở tài xế mới (nếu còn)

3. Post-processing:
   a. Tài xế nào có tổng capacity < min → cố gắng chuyển đơn sang tài xế khác
   b. Nếu không chuyển được → đánh dấu đơn cần chờ batch tiếp theo
```

---

## Bài toán 3: Vehicle Routing Problem (VRP)

### Định nghĩa
Sau khi biết tài xế nào nhận đơn nào, phải tìm **lộ trình giao hàng tối ưu** cho mỗi tài xế (đi qua tất cả điểm giao, quay về kho, với tổng quãng đường nhỏ nhất).

```
Driver 1 nhận 4 đơn: A (Q1), B (Q3), C (Q7), D (Q5)

Lộ trình thô:  Kho → A → B → C → D → Kho   (20km)
Tối ưu:        Kho → A → D → C → B → Kho   (14km)

VRP = Travelling Salesman Problem (TSP) × M tài xế + capacity constraints
```

### Capacitated VRP (CVRP) và Xu hướng 2026

Đến năm 2026, bài toán VRP đã mở rộng sang các mô hình **Dynamic và Stochastic VRP**. Hệ thống không chỉ lập kế hoạch tĩnh mà còn tính đến sự bất định về thời gian giao hàng, rủi ro giao thông, tích hợp cùng mạng lưới Parcel Lockers, logistics tuần hoàn (giao kết hợp nhận hàng hoàn trả). Việc áp dụng Machine Learning kết hợp cùng thuật toán tối ưu truyền thống giúp dự báo tốt hơn năng lực tài xế theo thời gian thực.

CVRP thêm ràng buộc capacity cho mỗi xe:

```
CVRP:
  Minimize: Tổng quãng đường tất cả tài xế
  Subject to:
    - Mỗi đơn được giao đúng 1 lần
    - Mỗi tài xế bắt đầu và kết thúc tại kho
    - Tổng capacity trên xe không vượt max tại bất kỳ thời điểm nào
    - (Tùy chọn) Thời gian giao hàng ≤ SLA
```

### Thuật toán giải VRP

| Thuật toán | Loại | Tốc độ | Chất lượng |
|---|---|---|---|
| **Brute Force** | Exact | O(n!) | Optimal, nhưng chỉ chạy được cho n < 15 |
| **Branch & Bound** | Exact | O(2^n) | Optimal, chạy được cho n < 30 |
| **Clarke-Wright Savings** | Heuristic | O(n²) | Tốt, nhanh |
| **Google OR-Tools** | Meta-heuristic | O(n² log n) | Rất tốt, thực tế |
| **Genetic Algorithm** | Meta-heuristic | Tùy chỉnh | Tốt cho bài toán lớn |

---

## Kết hợp: Order-Driver Assignment with Capacity & Routing

Trong thực tế, cả 3 bài toán được giải **đồng thời** hoặc **lặp lại (iterative)**:

```
Combined Algorithm:

Vòng 1: Assignment
  - Tính cost matrix (khoảng cách từ mỗi đơn đến vị trí giao)
  - Gom đơn theo vùng (clustering) bằng K-Means hoặc DBSCAN

Vòng 2: Bin Packing
  - Mỗi cluster → gán cho 1 tài xế
  - Kiểm tra: min_capacity ≤ cluster_total ≤ max_capacity
  - Nếu cluster quá lớn → chia nhỏ
  - Nếu cluster quá nhỏ → gom với cluster lân cận

Vòng 3: VRP
  - Mỗi tài xế → tối ưu lộ trình giao (TSP cho từng xe)

Vòng 4: Re-optimize
  - Thử swap đơn giữa các tài xế
  - Nếu swap cải thiện tổng cost → accept
  - Lặp lại cho đến khi không cải thiện nữa
```

---

## Công cụ thực tế

| Công cụ | Mô tả | Ngôn ngữ |
|---|---|---|
| **Google OR-Tools** | Thư viện tối ưu hóa mạnh nhất, hỗ trợ VRP, Bin Packing, Assignment | C++, Python, Java, Go |
| **OptaPlanner** | Framework planning AI cho Java, hỗ trợ VRP với time windows | Java |
| **VROOM** | Routing optimization engine, nhanh | C++ |
| **OSRM** | Open Source Routing Machine (tính khoảng cách đường bộ) | C++ |

### Google OR-Tools: VRP Example (Python)

```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_vrp(distance_matrix, demands, vehicle_capacities, depot=0):
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), len(vehicle_capacities), depot)
    routing = pywrapcp.RoutingModel(manager)

    # Distance callback
    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return distance_matrix[from_node][to_node]

    transit_id = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_id)

    # Capacity constraint
    def demand_callback(idx):
        node = manager.IndexToNode(idx)
        return demands[node]

    demand_id = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_id, 0, vehicle_capacities, True, 'Capacity')

    # Solve
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    solution = routing.SolveWithParameters(search_params)
    return solution
```

---

[← Chương trước: Phần 2 — Inventory Management](/series/ecommerce-order-allocation/part-2-inventory-realtime/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 4 — Amazon CONDOR & Anticipatory Shipping →](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 3 — Thuật toán phân bổ: Assignment Problem, Bin Packing & VRP giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Ba họ thuật toán cốt lõi cho bài toán phân bổ đơn hàng: Assignment Problem (phân công tối ưu), Bin Packing (xếp đơn vào tài xế) và Vehicle Routing Problem (VRP).

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
