---
title: "Phần 6 — Thực hành: Xây dựng Mini Order Allocation Engine bằng Google OR-Tools"
slug: "part-6-build-mini-allocation-engine"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "Xây dựng delivery allocation engine bằng Google OR-Tools Python: giải VRP với ràng buộc tải trọng, ưu tiên EXPRESS, và đóng gói FastAPI."
weight: 7
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "OR-Tools"
  - "Python"
  - "FastAPI"
  - "VRP"
  - "Allocation Engine"
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 6: Xây dựng Allocation Engine bằng Google OR-Tools"
  relative: false
---

[← Chương trước: Phần 5 — Split Shipment & Last-Mile](/series/ecommerce-order-allocation/part-5-split-consolidation-lastmile/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 7 — Distance Matrix Routing →](/series/ecommerce-order-allocation/part-7-distance-matrix-routing/)

---

> **Answer-first:** Hướng dẫn xây dựng Allocation Engine hoàn chỉnh bằng Google OR-Tools trong Python đóng gói FastAPI. Hệ thống phân bổ đơn hàng cho đội ngũ tài xế tuân thủ ràng buộc tải trọng min/max capacity, ưu tiên bảo vệ đơn EXPRESS (disjunction penalty), và tối ưu hóa chi phí quãng đường kết hợp giá vốn đa kho (COGS).

---

## Mô tả bài toán

Bạn là kỹ sư tại một công ty giao hàng. Mỗi ngày, kho xuất ra hàng trăm đơn hàng. Bạn cần phân bổ các đơn hàng cho đội ngũ tài xế sao cho:

### Đầu vào
- **1 kho duy nhất** (Điểm xuất phát - Depot).
- **N tài xế**, mỗi tài xế có:
  - `min_capacity`: Số đơn vị tối thiểu phải nhận (để chuyến đi có lời).
  - `max_capacity`: Sức chứa tối đa (giới hạn vật lý: trọng lượng, thể tích).
- **M đơn hàng**, mỗi đơn hàng có:
  - `capacity_cost`: Số đơn vị capacity chiếm dụng (ví dụ: 1 thùng nước = 3, 1 điện thoại = 1).
  - `destination`: Vị trí giao hàng (để tính khoảng cách).
  - `priority`: Mức ưu tiên (EXPRESS, STANDARD).

### Ràng buộc thực tế
```
1. Capacity Constraint:
   ∀ driver d được sử dụng: min_capacity(d) ≤ tổng_capacity_đơn ≤ max_capacity(d)

2. Đảm bảo giao hàng:
   Phải cố gắng giao nhiều đơn nhất có thể. Nếu quá tải, ưu tiên rớt các đơn STANDARD lại,
   tuyệt đối không rớt đơn EXPRESS.

3. Objective (Mục tiêu):
   Minimize tổng quãng đường giao hàng của toàn bộ tài xế.
```

---

## Bước 1: Database Schema

Vẫn giữ nguyên schema chuẩn như thiết kế ban đầu để quản lý trạng thái:

```sql
-- DRIVERS
CREATE TABLE drivers (
    id              VARCHAR(20) PRIMARY KEY,
    min_capacity    INT NOT NULL,
    max_capacity    INT NOT NULL,
    status          VARCHAR(20) DEFAULT 'AVAILABLE'
);

-- ORDERS
CREATE TABLE orders (
    id              VARCHAR(20) PRIMARY KEY,
    capacity_cost   INT NOT NULL,
    priority        VARCHAR(20) DEFAULT 'STANDARD',
    status          VARCHAR(20) DEFAULT 'PENDING',
    dest_latitude   DECIMAL(10,7),
    dest_longitude  DECIMAL(10,7)
);

-- ALLOCATIONS
CREATE TABLE allocations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id        VARCHAR(50) NOT NULL,
    driver_id       VARCHAR(20) NOT NULL REFERENCES drivers(id),
    order_id        VARCHAR(20) NOT NULL REFERENCES orders(id),
    sequence_num    INT NOT NULL
);
```

---

## Bước 2: Thuật toán phân bổ với Google OR-Tools (Python)

Thay vì tự viết thuật toán Greedy dễ dính lỗi tối ưu cục bộ, chúng ta sẽ dùng thư viện đẳng cấp thế giới **Google OR-Tools**. 

Hệ thống được thiết kế thành một microservice bằng Python:

### 1. Khởi tạo dữ liệu (Data Model)

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model(orders, drivers, distance_matrix):
    data = {}
    data['distance_matrix'] = distance_matrix  # Ma trận khoảng cách
    
    # Nhu cầu của từng điểm (Kho = 0, sau đó là các orders)
    # Ví dụ: Kho=0, O1=3, O2=1, O3=4
    data['demands'] = [0] + [order['capacity_cost'] for order in orders]
    
    # Priority penalty (Chi phí phạt nếu không giao)
    # EXPRESS = 1,000,000 | STANDARD = 10,000
    data['penalties'] = [0] + [
        1000000 if order['priority'] == 'EXPRESS' else 10000 
        for order in orders
    ]
    
    # Xe (Tài xế)
    data['vehicle_capacities'] = [driver['max_capacity'] for driver in drivers]
    data['vehicle_min_capacities'] = [driver['min_capacity'] for driver in drivers]
    data['num_vehicles'] = len(drivers)
    data['depot'] = 0
    return data
```

### 2. Thiết lập Solver và Ràng buộc Max Capacity

```python
def solve_allocation(data):
    # Khởi tạo Routing Index Manager và Model
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    # Callback tính khoảng cách
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Callback tính Capacity
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    # Thêm Dimension quản lý Max Capacity cho từng xe
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # Max capacities array
        True,  # start cumul to zero
        'Capacity'
    )
```

### 3. Xử lý Disjunctions (Ưu tiên EXPRESS)

Để giải quyết bài toán xe không đủ chỗ chứa tất cả đơn hàng, ta cho phép hệ thống "bỏ qua" (drop) một số đơn, nhưng sẽ chịu phạt (penalty). OR-Tools sẽ tìm cách gán đơn sao cho tổng điểm phạt là thấp nhất → Nó sẽ ưu tiên bỏ đơn STANDARD và giữ đơn EXPRESS.

```python
    # Cho phép drop orders với penalties tương ứng
    for node in range(1, len(data['distance_matrix'])):
        routing.AddDisjunction([manager.NodeToIndex(node)], data['penalties'][node])
```

### 4. Giải quyết Min-Capacity Constraint (Phần khó nhất)

OR-Tools mặc định không hỗ trợ trực tiếp việc "nếu xe chạy thì phải đạt min capacity". Chúng ta phải tạo ràng buộc cấp độ Solver.

```python
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    solver = routing.solver()

    for vehicle_id in range(data['num_vehicles']):
        # Lấy biến chứa tổng load của xe tại điểm kết thúc lộ trình (quay về kho)
        end_index = routing.End(vehicle_id)
        load_var = capacity_dimension.CumulVar(end_index)
        
        # Tạo biến boolean is_used: =1 nếu load > 0, =0 nếu load == 0
        is_used = solver.IsGreaterCstVar(load_var, 0)
        
        # Thêm Ràng buộc: load_var >= is_used * min_capacity
        # Nếu xe không dùng (is_used=0) → load_var >= 0 (luôn đúng)
        # Nếu xe có dùng (is_used=1) → load_var >= min_capacity
        min_cap = data['vehicle_min_capacities'][vehicle_id]
        solver.Add(load_var >= is_used * min_cap)
```

### 5. Chạy thuật toán và in kết quả

```python
    # Thiết lập chiến lược tìm kiếm
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 5  # Dừng sau 5 giây tìm kiếm

    # Giải bài toán
    solution = routing.SolveWithParameters(search_parameters)

    # Parse kết quả
    if solution:
        return parse_solution(manager, routing, solution, data)
    return None
```

---

## Bước 3: Đóng gói thành FastAPI

Để tương tác với các service khác (ví dụ Order Service viết bằng Golang), ta gói Python OR-Tools thành một REST API bằng **FastAPI**:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class OrderReq(BaseModel):
    id: str
    capacity_cost: int
    priority: str
    lat: float
    lng: float

class DriverReq(BaseModel):
    id: str
    min_capacity: int
    max_capacity: int

class AllocationRequest(BaseModel):
    batch_id: str
    warehouse_lat: float
    warehouse_lng: float
    orders: list[OrderReq]
    drivers: list[DriverReq]

@app.post("/api/v1/allocate")
def allocate_batch(req: AllocationRequest):
    # 1. Tính toán ma trận khoảng cách (dùng công thức Haversine hoặc OSRM)
    distance_matrix = build_distance_matrix(req)
    
    # 2. Xây dựng Data Model
    data = create_data_model(req.orders, req.drivers, distance_matrix)
    
    # 3. Chạy OR-Tools Solver
    result = solve_allocation(data)
    
    return {"batch_id": req.batch_id, "allocations": result}
```

---

## Bước 4: Invariant Checks (Kiểm tra bất biến)

Sau khi Python API trả về kết quả và lưu vào Database, chạy các SQL sau để đảm bảo hệ thống không bị lỗi logic:

```sql
-- Check 1: Không đơn nào được gán cho 2 tài xế
SELECT order_id, COUNT(DISTINCT driver_id) AS driver_count
FROM allocations
WHERE batch_id = 'BATCH-001'
GROUP BY order_id
HAVING COUNT(DISTINCT driver_id) > 1;

-- Check 2: Không tài xế nào vượt MAX capacity
SELECT
    a.driver_id, d.max_capacity, SUM(o.capacity_cost) AS total_assigned
FROM allocations a
JOIN orders o ON a.order_id = o.id
JOIN drivers d ON a.driver_id = d.id
WHERE a.batch_id = 'BATCH-001'
GROUP BY a.driver_id, d.max_capacity
HAVING SUM(o.capacity_cost) > d.max_capacity;

-- Check 3: Không tài xế nào dưới MIN capacity (khi được dùng)
SELECT
    a.driver_id, d.min_capacity, SUM(o.capacity_cost) AS total_assigned
FROM allocations a
JOIN orders o ON a.order_id = o.id
JOIN drivers d ON a.driver_id = d.id
WHERE a.batch_id = 'BATCH-001'
GROUP BY a.driver_id, d.min_capacity
HAVING SUM(o.capacity_cost) < d.min_capacity;

-- Check 4: Xem có đơn EXPRESS nào bị bỏ lại không?
SELECT o.id
FROM orders o
LEFT JOIN allocations a ON o.id = a.order_id AND a.batch_id = 'BATCH-001'
WHERE o.priority = 'EXPRESS' AND a.id IS NULL;
-- Nếu có: Có thể do tổng Max Capacity của tất cả tài xế nhỏ hơn 
-- tổng sức chứa của riêng các đơn EXPRESS.
```

---

## Bước 5: Tối ưu hóa theo Giá Vốn (Multi-Store Cost-based Optimization)

Trong thực tế, bạn có thể phải xử lý mô hình **Đa kho (Multi-Depot)**. Khi đó, một món hàng (SKU) có thể có **giá vốn (COGS) khác nhau** tại các kho khác nhau. 

Nếu chỉ tối ưu theo Quãng đường, thuật toán luôn chọn kho gần nhất. Nhưng nếu Kho A gần khách hơn (tiền ship rẻ hơn 20k) nhưng giá nhập hàng tại Kho A lại đắt hơn Kho B đến 50k, thì việc lấy hàng từ Kho B mới mang lại lợi nhuận cao nhất cho công ty.

Để giải quyết, thay vì chỉ Minimize **Distance_Cost**, chúng ta sẽ Minimize **Total_Cost = (Distance_Cost * Rate) + Item_Cost**.

### Cách tích hợp vào OR-Tools

Bạn cần chuyển đổi bài toán thành Multi-Depot (nhiều điểm xuất phát). Mỗi xe (vehicle) sẽ được gán cứng vào một kho (Store) cụ thể. 

```python
    # Giả sử có 2 Store:
    # Xe 0 xuất phát từ Store 0. Xe 1 xuất phát từ Store 1.
    # data['starts'] = [Store_0_Index, Store_1_Index]
    
    # Ma trận giá vốn: data['item_costs'][store_index][order_node_index]
    DISTANCE_TO_VND = 5000  # Ví dụ: 1km = 5,000 VNĐ

    def total_cost_callback(from_index, to_index, vehicle_id):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        # 1. Chi phí vận chuyển (Tiền Ship)
        distance = data['distance_matrix'][from_node][to_node]
        shipping_cost = distance * DISTANCE_TO_VND
        
        # 2. Chi phí hàng hóa (Giá vốn)
        goods_cost = 0
        if to_node not in data['starts'] and to_node not in data['ends']:
            # to_node là một order, ta lấy giá vốn của order đó tại kho mà xe đang trực thuộc
            store_idx = data['starts'][vehicle_id]
            goods_cost = data['item_costs'][store_idx][to_node]
            
        return shipping_cost + goods_cost

    # Đăng ký callback MỚI (có nhận tham số vehicle_id)
    # Vì mỗi xe thuộc một kho khác nhau nên chi phí sẽ khác nhau
    transit_callback_index = routing.RegisterTransitCallback(
        lambda from_idx, to_idx: total_cost_callback(from_idx, to_idx, 0) # Xe 0
    )
    # Lưu ý: Trong OR-Tools thực tế, bạn sẽ dùng routing.SetArcCostEvaluatorOfVehicle()
    # để set hàm tính cost riêng cho từng chiếc xe (phụ thuộc vào kho của xe đó).
```

**Kết quả:** Hệ thống sẽ tự động cân nhắc: *Kho B xa hơn tốn thêm tiền ship, nhưng giá vốn rẻ hơn* → Thuật toán sẽ tự động gán đơn đó cho tài xế xuất phát từ Kho B để tối ưu hóa biên lợi nhuận cuối cùng.

---

## Tổng kết Lợi ích khi dùng OR-Tools

So với thuật toán tự viết (Greedy), việc chuyển sang OR-Tools đem lại giá trị khổng lồ:

1. **Routing cực chuẩn:** OR-Tools không chỉ nhét đơn vào xe (Bin Packing), nó còn sắp xếp lộ trình (Sequence) đi qua các điểm sao cho tổng số km di chuyển là ngắn nhất.
2. **Khả năng Global Search:** Nhờ `GUIDED_LOCAL_SEARCH`, nếu mắc kẹt ở giải pháp tồi, nó tự biết hoán đổi đơn hàng giữa các xe để tìm ra cấu hình tốt hơn nhiều.
3. **Mở rộng dễ dàng:** Mai mốt Business yêu cầu *"Đơn hàng kem lạnh phải giao trong 30 phút"*, bạn chỉ cần thêm `Time Window Dimension`. Không cần đập đi viết lại từ đầu.
4. **Nền tảng cho AI Orchestration (2026):** Trong xu thế hiện đại, các solver như OR-Tools vẫn không hề lỗi thời. Chúng trở thành lõi tính toán vững chắc. Một hệ thống AI (Orchestrator) phía trên sẽ đánh giá động các tham số thời tiết, tắc đường, và ưu tiên để tinh chỉnh mô hình, sau đó nạp vào OR-Tools để đưa ra phương án chính xác tuyệt đối.

---

[← Chương trước: Phần 5 — Split Shipment & Last-Mile](/series/ecommerce-order-allocation/part-5-split-consolidation-lastmile/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 7 — Distance Matrix Routing →](/series/ecommerce-order-allocation/part-7-distance-matrix-routing/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 6 — Thực hành: Xây dựng Mini Order Allocation Engine bằng Google OR-Tools giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Xây dựng delivery allocation engine bằng Google OR-Tools Python: giải VRP với ràng buộc tải trọng, ưu tiên EXPRESS, và đóng gói FastAPI.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
