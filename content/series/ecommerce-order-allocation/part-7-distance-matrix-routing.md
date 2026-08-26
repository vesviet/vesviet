---
title: "Phần 7 — Distance Matrix: Thuật toán tính toán quãng đường di chuyển"
slug: "part-7-distance-matrix-routing"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "So sánh GraphHopper vs OSRM. Hướng dẫn xây dựng Distance Matrix open-source thay thế API trả phí như distance.to hoặc Google Maps."
weight: 8
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-7-distance-matrix-routing/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "Distance Matrix"
  - "Routing"
  - "GraphHopper"
  - "OSRM"
  - "H3 Hexagon"
cover:
  image: "/images/posts/default-post.png"
  alt: "Graphhopper vs OSRM: Xây dựng Distance Matrix định tuyến"
  relative: false
---

[← Chương trước: Phần 6 — Xây dựng Mini Allocation Engine](/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 8 — AI Agentic cho Dynamic IOR →](/series/ecommerce-order-allocation/part-8-intelligent-order-release/)

---

> **Answer-first:** Để tối ưu hóa chi phí định tuyến VRP, tự host GraphHopper và OSRM thay thế hoàn hảo các API thương mại đắt đỏ như Google Maps. Kết hợp Haversine lọc sơ cấp và Uber H3 Hexagon Caching trên Redis giúp giảm 95% chi phí tính toán và đảm bảo độ trễ sub-second.

---

## Mảnh ghép vô hình nhưng tốn kém nhất trong E-commerce Routing

Để bất kỳ VRP (Vehicle Routing Problem) solver nào có thể tìm ra lộ trình giao hàng tối ưu, nó cần biết chính xác chi phí di chuyển giữa mọi cặp điểm dừng — đây chính là **distance matrix** (ma trận khoảng cách). Với 1 kho + 100 đơn hàng (101 điểm), cần tính `101 × 101 = 10,201` cặp khoảng cách. Chọn sai công cụ cho bước này có thể tốn kém **$510/ngày** phí API hoặc gây ra độ trễ hàng giây khi hệ thống quá tải.

---

## 1. Đường chim bay: Thuật toán Haversine

Đây là cách tính khoảng cách đường thẳng giữa 2 điểm trên mặt cầu (Trái Đất) dựa trên tọa độ vĩ độ (Latitude) và kinh độ (Longitude).

### Ưu điểm
- **Cực kỳ nhanh:** Tính 10,000 cặp khoảng cách chỉ mất vài mili-giây trên CPU.
- **Không cần dữ liệu ngoài:** Code thuần toán học, không phụ thuộc vào API hay dữ liệu bản đồ.

### Nhược điểm
- **Thiếu chính xác:** Không tính đến đường phố, sông ngòi, hầm vượt, hay đường một chiều. Trong thực tế đô thị, quãng đường di chuyển thật thường gấp 1.2 đến 1.5 lần khoảng cách Haversine.

### Code Python minh họa

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Bán kính Trái Đất (km)
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2)**2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c # Trả về km

# Áp dụng tạo Distance Matrix:
def build_haversine_matrix(locations):
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine(
                    locations[i].lat, locations[i].lng,
                    locations[j].lat, locations[j].lng
                )
    return matrix
```

**Thực tế áp dụng:** Amazon và Grab thường dùng Haversine làm bộ lọc sơ cấp (Candidate Filtering) để loại bỏ các điểm ở quá xa trước khi gọi các thuật toán đắt tiền hơn.

---

## 2. Chân ái cho bài toán Base: Routing Engine (OSRM / GraphHopper)

Nếu bài toán của bạn **chỉ cần giao hàng từ kho cố định tới khách**, **không quan tâm kẹt xe**, **không màng lịch sử giao thông**, mà chỉ cần tính khoảng cách dựa trên **mạng lưới đường bộ thực tế đang tồn tại** — thì đây chính là giải pháp hoàn hảo và tiết kiệm nhất.

Bạn cần một **Routing Engine** để nạp dữ liệu đồ thị mạng lưới đường bộ. Dữ liệu này thường được tải miễn phí từ **OpenStreetMap (OSM)** — nơi cộng đồng liên tục cập nhật mỗi khi có đường mới được xây, hẻm bị dỡ bỏ hoặc cấm tải. Khi đường sá thay đổi, bạn chỉ việc tải lại file bản đồ (`.osm.pbf`) và restart lại engine.

### Tại sao không dùng thuật toán Dijkstra/A* thông thường?

Nếu dùng thuật toán **Dijkstra** hoặc **A*** truyền thống để tìm đường giữa 10,000 cặp điểm trên bản đồ toàn thành phố (nơi có hàng triệu node), server sẽ bị quá tải vì phải duyệt đồ thị quá lớn cho mỗi query.

Vì thế, các Routing Engine hiện đại sử dụng các kỹ thuật "tiền xử lý" (pre-processing) bản đồ:

1. **Contraction Hierarchies (CH):** Mất vài giờ để phân tích trước bản đồ, tạo ra các "shortcut" (đường cao tốc ảo) giữa các khu vực. Khi truy vấn, thuật toán nhảy qua các shortcut này thay vì đi từng ngõ hẻm → Thời gian truy vấn giảm xuống mức **micro-giây**. Bù lại, nếu có một con đường bị kẹt xe hoặc đóng cửa, bạn phải build lại toàn bộ map (rất tốn thời gian).
2. **Multi-Level Dijkstra (MLD) / Customizable Route Planning (CRP):** Chia bản đồ thành nhiều ô nhỏ (cells). Thay đổi chi phí đi lại của một con đường (ví dụ: đang kẹt xe) chỉ yêu cầu cập nhật lại một ô nhỏ đó (mất vài giây) thay vì toàn bộ map. Phù hợp để nhúng dữ liệu Traffic Real-time.

### So sánh hai "ông lớn" Open-Source: OSRM và GraphHopper (Cập nhật 2026)

Trong giới logistics tự build hệ thống, hai engine open-source nổi tiếng nhất là **OSRM** (viết bằng C++) và **GraphHopper** (viết bằng Java). Bước sang 2026, cả hai đều có những cải tiến đáng chú ý để loại bỏ sự phụ thuộc vào các API thương mại đắt đỏ, bên cạnh sự xuất hiện của **Valhalla** nổi lên như một lựa chọn thay thế sáng giá cho routing đa phương thức.
- **OSRM:** Đang có những nỗ lực "hồi sinh" (revitalization) đáng kể, tập trung duy trì lợi thế tốc độ khủng khiếp (millisecond latency) cho các ma trận cực lớn và hỗ trợ chạy mượt mà trên đa nền tảng nhờ tối ưu bộ nhớ `mmap`.
- **GraphHopper:** Tiếp tục dẫn đầu về tính linh hoạt. Với Custom Models định nghĩa qua JSON, engine này cho phép cập nhật luật định tuyến (routing weights, turn penalties, cargo restrictions) ngay lúc runtime (on-the-fly) mà không cần phải build lại cấu trúc graph.

| Tính năng | OSRM (Open Source Routing Machine) | GraphHopper |
|---|---|---|
| **Ngôn ngữ** | C++ | Java |
| **Thuật toán chính** | MLD và CH | CH, A*, Landmark |
| **Routing Profiles** | Viết bằng Lua script (driving, cycling, walking) | Viết bằng Java / YAML |
| **Matrix API** | Nhanh khủng khiếp (C++ optimized) | Tốt, nhưng OSRM vẫn nhỉnh hơn một chút ở tính Matrix lớn |
| **Sự linh hoạt** | Khá cứng ngắc, khó thay đổi rules runtime | Rất linh hoạt (Custom Models) cho phép đổi rules khi đang chạy |
| **Cộng đồng/Sử dụng** | Mapbox đứng sau, dùng rộng rãi cho routing tĩnh | Dễ nhúng vào ứng dụng Java, linh hoạt cao |

**Routing Profiles (Hồ sơ định tuyến):** 
Khoảng cách từ A đến B của một chiếc xe máy đi luồn lách trong hẻm khác hoàn toàn với một chiếc xe tải 10 tấn (bị cấm vào đường nhỏ, đường cấm tải). Cả OSRM và GraphHopper đều cho phép bạn định nghĩa các **Profiles**. Ví dụ ở OSRM, bạn viết file Lua: `car.lua`, `truck.lua`, `bike.lua` để engine biết đường nào xe được phép đi.

### OSRM Table API: Cách tạo Distance Matrix siêu tốc

Giả sử bạn tự host một server OSRM (chạy bằng Docker rất dễ), OSRM cung cấp một API có tên là `table` để tạo Distance Matrix cực kỳ tối ưu:

```bash
# Request lên OSRM server local để tính ma trận 3x3 (khoảng cách giữa 3 tọa độ)
curl "http://localhost:5000/table/v1/driving/106.70,10.77;106.71,10.78;106.72,10.79?annotations=distance,duration"

# Response trả về cả ma trận thời gian (durations) và quãng đường (distances)
{
  "durations": [
    [0, 150, 320],
    [155, 0, 180],
    [330, 175, 0]
  ],
  "distances": [
    [0, 1200, 2400],
    [1250, 0, 1100],
    [2500, 1150, 0]
  ]
}
```
*Ghi chú: OSRM Table API có thể trả về một ma trận 100x100 (10.000 phần tử) chỉ trong vài chục mili-giây!*

**Ưu điểm tự host:** Miễn phí, cực nhanh, không lo bị giới hạn rate limit.
**Nhược điểm:** Tốn RAM (đặc biệt nếu load bản đồ cả một quốc gia lớn), và không có sẵn dữ liệu kẹt xe thời gian thực trừ khi bạn tự mua dữ liệu traffic và feed vào thuật toán MLD liên tục.

---

## 3. Sự thừa thãi đắt đỏ: Commercial APIs (Google Maps / Mapbox)

Nếu hệ thống của bạn là ứng dụng gọi xe (Ride-Hailing) cần ETA (thời gian đến dự kiến) chính xác từng phút để khách không hủy chuyến, bạn sẽ cần dữ liệu kẹt xe hiện tại, lịch sử giao thông giờ cao điểm... Khi đó bạn phải dùng các API thương mại (Google Maps).

**Tuy nhiên, với bài toán giao hàng tĩnh (Static Delivery) từ kho cố định, điều này là hoàn toàn thừa thãi và cực kỳ lãng phí.**

```python
# Gọi Google Maps Distance Matrix API (Rất đắt)
import requests

url = "https://maps.googleapis.com/maps/api/distancematrix/json"
params = {
    "origins": "10.77,106.70|10.78,106.71",
    "destinations": "10.77,106.70|10.78,106.71",
    "departure_time": "now",  # Tính kẹt xe ngay lúc này
    "key": "YOUR_API_KEY"
}
```

### Cái giá quá đắt

Google Maps tính phí khoảng **$0.005** cho mỗi CẶP điểm (Element).
Trở lại ví dụ 1 kho + 100 đơn hàng = 10,201 cặp.
Mỗi lần chạy thuật toán phân bổ, bạn tốn: `10,201 × $0.005 = $51`.
Nếu mỗi ngày kho chạy 10 lần, bạn mất **$510/ngày** chỉ để tính khoảng cách!

Đó là lý do các công ty giao hàng nội địa đều tự host **OSRM** hoặc **GraphHopper** thay vì dùng Google Maps để giải bài toán định tuyến từ kho. Mạng lưới đường OpenStreetMap là quá đủ tốt cho nhu cầu này.

---

## 4. Chiến lược System Design để tiết kiệm chi phí

Để vừa có độ chính xác cao vừa không phá sản vì tiền API, các hệ thống lớn dùng các thủ thuật sau:

### Kỹ thuật 1: Gom cụm (Clustering) trước khi tính
Nếu có 5 đơn hàng giao cho 1 tòa nhà chung cư, gom chúng thành 1 tọa độ duy nhất. Ma trận giảm từ 101x101 xuống còn 97x97.

### Kỹ thuật 2: Hybrid Matrix (Kết hợp Haversine + OSRM)
Bạn chỉ cần tính khoảng cách chính xác cho những điểm có tiềm năng đi nối tiếp nhau.
- Nếu điểm A và điểm B cách nhau > 15km (theo Haversine), gán luôn cost vô cùng lớn (infinity). Thuật toán VRP sẽ tự động không bao giờ ghép xe đi từ A đến B.
- Chỉ gọi OSRM cho các cặp điểm gần nhau (< 5km).

### Kỹ thuật 3: H3 Hexagon Caching (Cách Uber/Grab làm)

Tính toán lại khoảng cách giữa hai con hẻm gần nhau ngày qua ngày là một sự lãng phí tài nguyên. Các ông lớn logistics sử dụng **H3 (Hexagonal Hierarchical Spatial Index)** của Uber để cache kết quả khoảng cách.

#### Tại sao lại là lưới lục giác (Hexagon) mà không phải Geohash (Hình vuông)?
Trong hình vuông, khoảng cách từ tâm đến 4 cạnh thẳng và 4 góc chéo là khác nhau. Trong hình lục giác, khoảng cách từ tâm đến tất cả các ô hàng xóm xung quanh là **bằng nhau**. Điều này cực kỳ quan trọng trong định tuyến vì sai số khoảng cách được kiểm soát đồng đều về mọi hướng.

#### Cách hệ thống hoạt động:

**1. Chọn Resolution (Độ phân giải):**
Thường dùng **H3 Resolution 9** (Mỗi ô lục giác có đường kính khoảng 174 mét). Đây là độ lớn vừa đủ để đại diện cho 1 cụm dân cư nhỏ hoặc 1 đoạn phố.

**2. Chuyển đổi tọa độ (Lat/Lng) thành H3 Index:**
```python
import h3

# Chuyển đổi tọa độ của Điểm A và Điểm B
h3_A = h3.geo_to_h3(10.7712, 106.7011, 9) # Kết quả: '8965a6a0033ffff'
h3_B = h3.geo_to_h3(10.7780, 106.7100, 9) # Kết quả: '8965a6a0027ffff'
```

**3. Kiểm tra Cache (Redis) trước khi gọi API:**
```python
redis_key = f"route_cost:{h3_A}:{h3_B}"

cache_result = redis.get(redis_key)
if cache_result:
    return json.loads(cache_result) # Cache Hit! Không tốn tiền
else:
    # Cache Miss! Gọi Google Maps / OSRM
    result = call_routing_api(lat1, lon1, lat2, lon2)
    
    # Lưu vào Redis để lần sau dùng (TTL = 30 ngày)
    redis.set(redis_key, json.dumps({
        "distance_m": result.distance,
        "duration_s": result.duration
    }), ex=2592000)
    
    return result
```

#### Pre-warming Cache (Khởi động trước bộ đệm)
Thay vì đợi khách hàng đặt đơn mới bắt đầu tính, hệ thống có thể chạy batch job vào ban đêm:
1. Lấy tất cả các ô H3 có dân cư trong thành phố.
2. Dùng OSRM (miễn phí) tính toán trước khoảng cách giữa tất cả các cặp ô H3 (cách nhau dưới 10km).
3. Bơm sẵn vào Redis.

Khi ban ngày hệ thống OR-Tools chạy phân bổ, nó chỉ việc đọc RAM từ Redis với tốc độ ánh sáng mà không cần duyệt đồ thị nữa. Do mạng lưới đường sá ít khi thay đổi (chỉ khi có lô cốt hoặc đường 1 chiều mới), tỷ lệ Cache Hit của chiến lược này có thể lên tới **95%**, giúp bạn có tốc độ của Haversine nhưng độ chính xác của Routing Engine!

---

[← Chương trước: Phần 6 — Xây dựng Mini Allocation Engine](/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 8 — AI Agentic cho Dynamic IOR →](/series/ecommerce-order-allocation/part-8-intelligent-order-release/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 7 — Distance Matrix: Thuật toán tính toán quãng đường di chuyển giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
So sánh GraphHopper vs OSRM. Hướng dẫn xây dựng Distance Matrix open-source thay thế API trả phí như distance.to hoặc Google Maps.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
