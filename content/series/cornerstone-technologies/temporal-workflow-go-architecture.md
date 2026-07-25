---
title: "Temporal Workflow & Golang: Kiến trúc & Production Guide"
description: "Hướng dẫn chuyên sâu kiến trúc Temporal Workflow dành cho Go Developer. Giải thích Determinism, Event Sourcing, và cách scale Temporal Worker trên Production."
slug: temporal-workflow-go-architecture
author: "Lê Tuấn Anh (Senior Go Engineer)"
series: "Cornerstone Technologies"
date: "2026-07-25"
---

# Temporal Workflow & Golang: Kiến trúc & Production Guide

Khi xây dựng các hệ thống microservices quy mô lớn, việc quản lý trạng thái của các giao dịch phân tán và orchestration là một bài toán cực kỳ phức tạp. [Cornerstone Technologies](/series/cornerstone-technologies/) thường đưa ra những nền tảng làm thay đổi cách chúng ta thiết kế hệ thống, và Temporal chính là một trong số đó. Trong bài viết này, chúng ta sẽ đi sâu vào kiến trúc cốt lõi của Temporal Workflow dành cho Go Developer, từ việc hiểu rõ Determinism, Event Sourcing cho đến cách scale Temporal Worker trên môi trường Production.

## Temporal Architecture: Event Sourcing & Replay Engine

**Answer-first:** Temporal là một nền tảng orchestration cho microservices sử dụng mô hình Event Sourcing để đảm bảo workflow của bạn có thể phục hồi trạng thái sau khi crash. Trong Go, Temporal Workflow yêu cầu tính Determinism tuyệt đối để engine có thể replay lại chính xác trạng thái thực thi dựa trên lịch sử event được lưu trữ.

Temporal hoạt động như thế nào? Thay vì duy trì trạng thái của workflow trong bộ nhớ (RAM) và chịu rủi ro mất dữ liệu khi hệ thống gặp sự cố, Temporal áp dụng kiến trúc Event Sourcing. Mỗi bước thực thi (như bắt đầu một activity, nhận tín hiệu, bộ đếm thời gian) đều được lưu lại dưới dạng các sự kiện không thể thay đổi (immutable events) vào cơ sở dữ liệu backend của Temporal Cluster. 

Khi một Worker (tiến trình chạy mã Go của bạn) bị sập và được khởi động lại, Temporal sẽ không chạy lại workflow từ đầu một cách mù quáng. Thay vào đó, nó tạo ra một Replay Engine, đọc toàn bộ lịch sử các sự kiện từ Temporal Cluster và "phát lại" (replay) các dòng mã của bạn. Engine đảm bảo rằng mã sẽ đi đến đúng trạng thái cuối cùng trước khi bị crash. Điều này mang lại sự tin cậy tuyệt đối: mã của bạn dường như không bao giờ bị gián đoạn. Nếu bạn đang thiết kế [Event-Driven Architecture](/series/system-design/12-communication-protocols-microservices/), tư duy stateful, fault-tolerant này của Temporal là cực kỳ đắt giá.

## Quy tắc sống còn: Workflow Determinism trong Golang

**Answer-first:** Determinism trong Temporal là gì và tại sao lại quan trọng? Determinism có nghĩa là một hàm, khi được cung cấp cùng một đầu vào và lịch sử, luôn luôn sinh ra cùng một kết quả và đi theo cùng một nhánh logic. Trong Temporal Workflow viết bằng Go SDK, bạn tuyệt đối không được sử dụng goroutine gốc, rand, hoặc các hàm time native, để đảm bảo quá trình replay diễn ra hoàn hảo.

Việc không tuân thủ các quy tắc này sẽ dẫn đến lỗi *Non-Deterministic Error*, khiến workflow của bạn bị kẹt mãi mãi (blocked/stuck). Dưới đây là những quy tắc cốt lõi khi viết mã Go cho Workflow:

*   **Không sử dụng goroutines (`go func()`) hoặc channels gốc:** Temporal SDK cung cấp các API thay thế như `workflow.Go()` và `workflow.Channel`. Engine cần theo dõi và quản lý vòng đời của mọi tiến trình đồng thời bên trong workflow.
*   **Không sử dụng `time.Now()` hoặc `time.Sleep()`:** Luôn sử dụng `workflow.Now()` và `workflow.Sleep()`. Việc gọi `time.Now()` sẽ trả về các giá trị khác nhau giữa lần chạy ban đầu và lần replay, phá vỡ tính determinism.
*   **Không gọi API mạng, I/O trực tiếp (HTTP, Database):** Mọi tương tác với thế giới bên ngoài, có thể thành công hoặc thất bại tuỳ thời điểm, đều phải được đóng gói vào trong **Activity**. Workflow chỉ điều phối, không thực thi I/O.
*   **Không tạo Random (Số ngẫu nhiên, UUID):** Sử dụng các API do Temporal cung cấp, ví dụ như `workflow.SideEffect()` nếu cần gọi các hàm không deterministic, hoặc dùng các context API tương đương.
*   **Cẩn trọng khi duyệt `map`:** Trong Go, thứ tự lặp qua một `map` bằng `range` là ngẫu nhiên. Nếu logic workflow phụ thuộc vào thứ tự này, nó sẽ không deterministic. Hãy chuyển dữ liệu sang slice hoặc mảng rồi sort trước khi duyệt.

*Kinh nghiệm firsthand:* Trong một dự án xử lý thanh toán, team tôi từng vi phạm quy tắc này khi lỡ thêm một dòng `time.Now()` để log thời gian xử lý vào trong Workflow code thay vì Activity. Ngay ngày hôm sau, khi worker restart, hàng ngàn workflow báo lỗi Non-Deterministic và bị đình trệ. Việc gỡ rối những lỗi này yêu cầu phải hiểu sâu về versioning (`workflow.GetVersion()`) để vá lỗi code mà không phá vỡ history cũ.

## Phân biệt Workflow vs Activity

**Answer-first:** Sự khác biệt giữa Temporal Workflow và Activity nằm ở vai trò, tính an toàn và giới hạn thiết kế. Workflow là nhạc trưởng (đòi hỏi determinism tuyệt đối, stateful), trong khi Activity là các nhạc công thực thi nhiệm vụ thực tế (stateless, có thể chứa I/O, retry tự động).

Dưới đây là bảng so sánh chi tiết giữa hai khái niệm này:

| Tính năng | Workflow | Activity |
| :--- | :--- | :--- |
| **Vai trò chính** | Điều phối (Orchestration), kiểm soát luồng (if/else, vòng lặp, timeout). | Thực thi tác vụ cụ thể (gọi API, chèn DB, tải file). |
| **Determinism** | **Bắt buộc tuyệt đối.** Replay engine dựa vào mã này. | Không yêu cầu. Chứa bất cứ I/O, goroutines, DB calls nào. |
| **Retry tự động** | Không tự động retry code của workflow khi có lỗi (vì nó stateful). | **Tự động retry** với Exponential Backoff khi fail. |
| **State (Trạng thái)** | Stateful. Lưu vết trạng thái qua Event Sourcing. | Stateless. Nhận Input -> Trả Output. Không giữ state lâu dài. |
| **Thời gian chạy** | Có thể tồn tại vĩnh viễn (tháng, năm). | Thường ngắn hạn (giây, phút). Nếu lâu cần heartbeat. |
| **Thực thi song song** | Dùng `workflow.Go()` | Dùng WaitGroup hoặc promises (futures) trong Go. |

Nếu bạn đang phát triển các tính năng như [ứng dụng Saga Pattern bằng Temporal](/series/system-design/08-saga-pattern-distributed-transactions-go/), Workflow sẽ chứa logic điều phối các giao dịch Saga (bắt đầu, rollback), còn Activity chính là các lời gọi tới các service tham gia vào giao dịch.

## Triển khai Temporal Worker & Scale out trong Production

**Answer-first:** Triển khai Temporal Worker yêu cầu cấu hình Task Queues và cân bằng tải hiệu quả. Để scale out, bạn cần deploy nhiều Worker container lắng nghe cùng một Task Queue, đồng thời tối ưu hoá các cấu hình bộ nhớ và số lượng goroutine hoạt động đồng thời (concurrent executions).

Cách viết Temporal Workflow bằng Go SDK cho production không chỉ dừng ở code chạy được mà còn ở khả năng chịu tải. Dưới đây là các bước triển khai và scale out chuẩn xác:

1.  **Thiết kế Task Queues phân mảnh:** Đừng ném tất cả Workflows và Activities vào chung một Task Queue. Hãy phân tách theo domain (ví dụ: `PAYMENT_TASK_QUEUE`, `EMAIL_TASK_QUEUE`). Điều này giúp bạn scale worker độc lập tuỳ theo cường độ công việc của từng loại dịch vụ.
2.  **Cấu hình Worker Tuning Parameters:** Trên production, cấu hình mặc định hiếm khi đủ tốt. Bạn cần tinh chỉnh trong Go SDK:
    *   `MaxConcurrentActivityExecutionSize`: Số lượng Activity goroutines tối đa chạy trên một worker. (Benchmark khuyên dùng: 200 - 1000 tuỳ memory).
    *   `MaxConcurrentWorkflowTaskExecutionSize`: Số lượng Workflow executions đồng thời.
    *   `MaxConcurrentLocalActivityExecutionSize`: Dành cho các tác vụ rất nhỏ và cực nhanh gọn (như parse data).
3.  **Horizontal Pod Autoscaling (HPA) trên Kubernetes:** Không dùng CPU/Memory thuần tuý để scale worker. Hãy dùng Prometheus adapter để theo dõi metric `temporal_worker_task_slots_available` hoặc độ trễ `schedule_to_start_latency`. Khi hàng đợi quá tải, hệ thống sẽ tự sinh thêm pod worker.
4.  **Cấu hình Timeouts cẩn thận:** Bạn phải xác định đúng các loại timeout:
    *   `ScheduleToStartTimeout`: Thời gian tối đa worker có thể nán lại (đợi trong queue). Nếu quá lâu, nghĩa là worker đang thiếu.
    *   `StartToCloseTimeout`: Thời gian chạy thực tế của Activity. Nếu activity gọi API bên thứ ba mất 10s, hãy set 15s.

## Benchmark Thực tế & Các lỗi thường gặp

**Answer-first:** Khi vận hành Temporal trên production, bạn cần đo lường hiệu năng của hệ thống. Các benchmark thực tế cho thấy cấu hình ScheduleToClose là cực kỳ quan trọng để đảm bảo SLA của người dùng. Các lỗi thường gặp xoay quanh Non-Deterministic Errors và Memory Leaks do không tối ưu history size.

*Case study & Benchmark:*
Là một Senior Go Engineer, tôi từng tham gia scale cụm Temporal xử lý 50.000 workflow đồng thời. Dưới đây là những con số và bài học đắt giá:

*   **Benchmark Timeouts:**
    *   Đối với API gọi nội bộ: `StartToCloseTimeout` là 2s.
    *   Đối với Webhooks ra bên ngoài: `StartToCloseTimeout` là 30s.
    *   Luôn luôn sử dụng `ScheduleToCloseTimeout` (đã bao gồm thời gian nằm queue + số lần retry) như một SLA cứng, ví dụ: Không quá 5 phút cho một luồng đăng ký tài khoản.
*   **Lỗi History Limit Exceeded (Giới hạn 50K events):**
    *   Temporal có giới hạn cứng về độ dài lịch sử của một workflow (thường là 50,000 events hoặc 50MB). Nếu workflow lặp vô tận, nó sẽ crash hoàn toàn.
    *   *Cách khắc phục:* Sử dụng `workflow.ContinueAsNew()` để khởi động lại workflow từ trạng thái sạch khi số lượng event chạm ngưỡng 10,000. Điều này giải phóng bộ nhớ và ngăn lỗi xảy ra.
*   **Lỗi Không Handle Signals Kịp Thời:**
    *   Go channel trong workflow để nhận signals có thể bị block nếu không có cơ chế buffer hoặc timeout (`workflow.Selector`). Hàng ngàn signal ập đến mà workflow xử lý chậm sẽ gây phình database.

## FAQ: Câu hỏi thường gặp về Temporal

*   **Tôi có thể gọi API trực tiếp bên trong Temporal Workflow không?**
    Tuyệt đối không! Mọi I/O (gọi HTTP API, gõ DB) phải được đưa vào Activity. Việc gọi API trong Workflow phá vỡ nguyên tắc Determinism vì kết quả API có thể thay đổi trong quá trình replay.
*   **Làm sao để handle versioning khi update code của Temporal Workflow?**
    Trong Go SDK, bạn phải sử dụng hàm `workflow.GetVersion()`. Nó cho phép code của bạn phân nhánh an toàn giữa logic cũ và logic mới khi xử lý các workflow đang chạy dang dở (in-flight workflows) dựa trên lịch sử đã ghi.
*   **Temporal có thay thế Kafka được không?**
    Không. Kafka là hệ thống pub/sub (event streaming) thuần túy với throughput cực lớn (hàng triệu msg/s). Temporal là Workflow Orchestration Engine (quản lý trạng thái, timeouts, retries, saga). Chúng bổ trợ cho nhau: Kafka để luân chuyển event tốc độ cao, Temporal để quản lý vòng đời logic nghiệp vụ phức tạp.
