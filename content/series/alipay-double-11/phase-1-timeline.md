---
title: "Phase 1: Timeline and Scale Evolution"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Timeline of Alipay Double 11 scaling evolution from 2009 to 2020+."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/executive-summary/) • [Next →](/series/alipay-double-11/phase-2-architecture/)
## Tổng Quan

Sự kiện **Double 11 (Singles' Day)** bắt đầu từ năm 2009 và đã trở thành sự kiện mua sắm trực tuyến lớn nhất thế giới, vượt xa Black Friday và Cyber Monday cộng lại.

---

## Timeline Chi Tiết

### 2009: Khởi đầu khiêm tốn
- **Sự kiện**: Taobao Mall (nay là Tmall) tổ chức chương trình khuyến mãi đầu tiên
- **Quy mô**: 27 thương hiệu tham gia
- **Doanh thu**: 50 triệu CNY (khoảng 7 triệu USD)
- **Thách thức kỹ thuật**: 
  - Giao dịch cao gấp **5 lần** bình thường
  - Hệ thống Alipay gần như chạm giới hạn tải
  - Kỹ sư phải scale up thủ công khi thấy traffic tăng

### 2010: Chuẩn bị có chủ đích
- Alipay chủ động liên hệ Taobao Mall để hỏi về kế hoạch khuyến mãi
- Bắt đầu đưa Double 11 vào agenda cuộc họp ổn định hàng tuần
- Ước tính capacity: "Lấy giá trị ước tính rồi nhân 3"
- Li Junkui và team bắt đầu làm stress testing thủ công

### 2012: Khủng hoảng Scale - "Bước ngoặt sinh tử"

**Ba vấn đề nghiêm trọng đồng thời xảy ra:**

1. **Database Expansion Exhausted**
   - DBA cảnh báo: "Hệ thống chỉ có thể chịu đựng thêm vài tháng"
   - Không thể scale theo kiểu vertical nữa

2. **Oracle Database Limits**
   - Số lượng kết nối tối đa đến Oracle database trở thành bottleneck
   - Không thể mở rộng thêm

3. **Power Supply Crisis ở Hangzhou**
   - Nguồn điện Hangzhou **không đủ** để mở rộng data center
   - Phải **cắt điện văn phòng** để giữ điện cho data center
   - Dùng **đá lạnh để giải nhiệt** giữa mùa hè nóng bức
   - Gong Jie chia sẻ: "Chỉ ai từng sống qua mùa hè ở Hangzhou mới hiểu khắc nghiệt đến mức nào"

**Kết quả**: Bắt buộc phải có "cuộc cách mạng" kiến trúc - không còn cách nào khác.

---

## 2013: LDC Architecture Debut - "The Impossible Goal"

### Mục tiêu "Không thể": 20,000 Payments Per Second
- Tất cả kỹ sư đều hô "Impossible!"
- Chen Liang (architect) phải dành rất nhiều thời gian thuyết phục mọi người đồng ý giải pháp

### Logical Data Center (LDC) Architecture
- **Đề xuất**: Chia hệ thống thành các "units" độc lập (modularization)
- **Challenge**: Không có kinh nghiệm thành công nào để tham khảo
- **Timeline cực gấp**: 
  - Phê duyệt cuối năm 2012
  - Chỉ có < 1 năm trước Double 11/2013
  - Release updates hầu như **mỗi tháng** (tần suất gấp nhiều lần bình thường)
  - Hệ thống chỉ deploy xong **nửa tháng** trước Double 11

### Lần đầu tiên có "Đại diện" ở Guangming Peak
- Li Junkui là người đại diện đầu tiên của Alipay tại command center
- Tổng chỉ huy Li Jin chỉ vào màn hình lớn và nói: "Xiangxiu! Bạn chịu trách nhiệm dữ liệu Alipay!"
- Jiang Tao kết luận: **"We survived"** - Kiến trúc mới đã có bước đi đầu tiên đầy kịch tính

---

## 2014: Stress Testing System - Từ "Uncertain" đến "Deterministic"

### Vấn đề trước 2014
- Chen Liang đánh giá: Độ tin cậy hệ thống trước giờ G chỉ khoảng **60%**
- "Sự không chắc chắn là nguồn lo lắng lớn nhất"

### Giải pháp: Automated Stress Testing
- Xây dựng môi trường simulation để chạy thử hệ thống
- **Full-link testing** thay vì test từng máy riêng lẻ
- Kết quả:
  - Phát hiện **100+ vấn đề nghiêm trọng** trong tháng trước Double 11
  - Chen Liang: "Nếu không fix, Double 11/2014 chắc chắn thất bại"
  - Độ tin cậy tăng từ **60% → 95%**

Zheng Yangfei được vinh danh là **"Prince of Stress Testing"**

---

## 2019: Đỉnh cao 544K TPS

### Con số kỷ lục
- **544,000 TPS** (transactions per second) - Peak của Alipay
- **61 triệu QPS** (queries per second)
- **87 triệu TPS** - POLARDB database

### So sánh
- Visa network peak: 64,000 TPS
- Alipay peak 2019: **544,000 TPS** (gấp ~8.5 lần Visa)

---

## 2020+: Cloud-Native Era

### Chiến lược Cloud-Native
- CTO Cheng Li: "Cloud-native là cách nhanh nhất để tiếp cận lợi ích cloud computing"
- Ding Yu: "Cloud-native là cuộc cách mạng thực sự của công nghệ cloud"

### Thành tựu 2020
- **STO Express**: Chuyển core system lên cloud, giảm 30% IT costs
- **Century Mart**: 
  - QPS cao hơn 230% so với 2019
  - R&D và delivery efficiency tăng >30%
  - Elastic resource cost giảm >40%

### Công nghệ sử dụng
- Alibaba Cloud Container Service for Kubernetes (ACK)
- PouchContainer
- ApsaraDB for PolarDB
- RocketMQ
- Function Compute (FC)

---

## Bảng Tổng Hợp TPS Evolution

| Năm | TPS Peak | Cột Mốc Kỹ Thuật |
|-----|----------|------------------|
| 2009 | ~100 | Sự kiện đầu tiên, 5x normal traffic |
| 2010 | ~500 | Bắt đầu stress testing thủ công |
| 2012 | ~2,000 | Chạm giới hạn Oracle & power supply |
| 2013 | **20,000** | LDC Architecture debut |
| 2014 | ~50,000 | Automated stress testing system |
| 2019 | **544,000** | Peak kỷ lục |
| 2020 | 583,000 | Cloud-native full deployment |

---

## Cultural Aspects

### Truyền thống "Worshiping Guan Gong"
- Được mang vào phòng chuẩn bị 2013 bởi Zheng Yangfei
- Truyền thống từ thuở Alipay mới thành lập
- Mỗi lần release quan trọng, kỹ sư gửi emoji Guan Gong cầu "no bugs"
- Nâng cấp qua các năm: Painting → Shadow puppet → Wooden statue → Bronze statue

### "Lingyin Temple Faction" vs "Faxi Temple faction"
- Chia phe đi chùa cầu may trước Double 11
- CTO Cheng Li và Deputy CTO Hu Xi dẫn team đi lễ chùa Faxi sau mỗi Double 11
- Đi bộ từ Alipay Building đến chùa và nhặt rác trên đường về

### Cách giải tỏa stress
- **Chen Liang**: Chạy bộ, chơi bóng
- **Others**: Kiểm tra code đi kiểm tra code lại
- **Foodies**: Ăn lẩu Haidilao trước Double 11

---

## Key Takeaways Phase 1

1. **2009-2012**: Growth đột biến buộc phải tìm giải pháp mới
2. **2013**: LDC Architecture - cuộc cách mạng kiến trúc
3. **2014**: Stress testing - biến uncertainty thành determinism
4. **2019**: 544K TPS - đỉnh cao scale
5. **2020+**: Cloud-native - efficiency và cost optimization

**Tiến bộ quan trọng nhất**: Từ "cắt điện văn phòng dùng đá lạnh" đến "544K TPS tự động scale"

---

*Next: Phase 2 - Kiến Trúc Kỹ Thuật Sâu (LDC, OceanBase, Distributed Systems)*

