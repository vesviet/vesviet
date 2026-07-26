---
title: "Temporal Workflow & Golang: Kiến trúc & Production Guide"
description: "Hướng dẫn kiến trúc Temporal Workflow cho Go Developer: giải thích Determinism, Event Sourcing, Temporal Nexus và cách scale Temporal Worker trên Production."
slug: temporal-workflow-go-architecture
author: "Lê Tuấn Anh (Senior Go Engineer)"
series: "Cornerstone Technologies"
date: "2026-07-25"
---

# Temporal Workflow & Golang: Kiến trúc & Production Guide

> **Answer-first:** Temporal là nền tảng durable execution cho microservices, phục hồi sự cố nhờ Event Sourcing. Trong Golang, Temporal Workflow đòi hỏi tính determinism tuyệt đối để replay event history. Để vận hành production ổn định, engineer cần phân tách Workflow/Activity, dùng ContinueAsNew nén history và tối ưu worker concurrency.

Khi xây dựng các hệ thống microservices quy mô lớn, việc quản lý trạng thái của các giao dịch phân tán và orchestration là một bài toán cực kỳ phức tạp. [Cornerstone Technologies](/series/cornerstone-technologies/) thường đưa ra những nền tảng làm thay đổi cách chúng ta thiết kế hệ thống, và Temporal chính là một trong số đó. Bài viết phân tích chi tiết kiến trúc cốt lõi của Temporal Workflow dành cho Go Developer, từ nguyên lý Determinism, Event Sourcing, kiến trúc Temporal Nexus cho đến chiến lược triển khai và scale Temporal Worker trên môi trường Production.

## Temporal Architecture: Event Sourcing & Replay Engine

Temporal là một nền tảng orchestration cho microservices sử dụng mô hình Event Sourcing để đảm bảo workflow của bạn có thể phục hồi trạng thái sau khi crash. Trong Go, Temporal Workflow yêu cầu tính Determinism tuyệt đối để engine có thể replay lại chính xác trạng thái thực thi dựa trên lịch sử event được lưu trữ.

Temporal hoạt động như thế nào? Thay vì duy trì trạng thái của workflow trong bộ nhớ (RAM) và chịu rủi ro mất dữ liệu khi hệ thống gặp sự cố, Temporal áp dụng kiến trúc Event Sourcing. Mỗi bước thực thi (như bắt đầu một activity, nhận tín hiệu, bộ đếm thời gian) đều được lưu lại dưới dạng các sự kiện không thể thay đổi (immutable events) vào cơ sở dữ liệu backend của Temporal Cluster. 

Khi một Worker (tiến trình chạy mã Go của bạn) bị sập và được khởi động lại, Temporal sẽ không chạy lại workflow từ đầu một cách mù quáng. Thay vào đó, nó tạo ra một Replay Engine, đọc toàn bộ lịch sử các sự kiện từ Temporal Cluster và "phát lại" (replay) các dòng mã của bạn. Engine đảm bảo rằng mã sẽ đi đến đúng trạng thái cuối cùng trước khi bị crash. Điều này mang lại sự tin cậy tuyệt đối: mã của bạn dường như không bao giờ bị gián đoạn. Nếu bạn đang thiết kế [Event-Driven Architecture](/series/system-design/12-communication-protocols-microservices/), tư duy stateful, fault-tolerant này của Temporal là cực kỳ đắt giá.

## Temporal Nexus: Orchestration Xuyên Namespace & Enterprise Boundary (2026)

Temporal Nexus là chuẩn kiến trúc hiện đại ra mắt nhằm giải quyết bài toán điều phối workflow liên namespace (cross-namespace) và liên cụm cluster trong doanh nghiệp. Nexus thay thế các giao thức REST/gRPC tuỳ biến bằng các hợp đồng dịch vụ bền vững (`nexus.Operation`), giúp các team chia sẻ khả năng vận hành mà không cần công khai Task Queue hay trạng thái cụm cluster nội bộ.

Trong các kiến trúc microservices lớn tại doanh nghiệp, việc chia sẻ workflow giữa các đội ngũ khác nhau thường gặp rào cản về ranh giới bảo mật và hạ tầng. Trước đây, các nhóm phải tự bọc Workflow trong REST API hoặc gRPC endpoints, làm mất đi tính năng durable execution xuyên suốt. Temporal Nexus giải quyết bài toán này bằng cách giới thiệu khái niệm Endpoint và Operation:

- **Nexus Endpoint:** Định nghĩa cổng giao tiếp bền vững giữa hai namespace hoặc hai cụm Temporal độc lập.
- **Nexus Operation:** Định nghĩa contract thực thi có trạng thái, cho phép Workflow ở Namespace A gọi một Operation dài hạn ở Namespace B như một bước native trong workflow mà không lo đứt gãy lịch sử replay.
- **Tách biệt Task Queue:** Nexus đảm bảo Namespace A không cần biết tên Task Queue hay thông tin worker nội bộ của Namespace B, duy trì nguyên tắc đóng gói (encapsulation) trong phần mềm.

## Quy tắc sống còn: Workflow Determinism trong Golang

Determinism trong Temporal là gì và tại sao lại quan trọng? Determinism có nghĩa là một hàm, khi được cung cấp cùng một đầu vào và lịch sử, luôn luôn sinh ra cùng một kết quả và đi theo cùng một nhánh logic. Trong Temporal Workflow viết bằng Go SDK, bạn tuyệt đối không được sử dụng goroutine gốc, rand, hoặc các hàm time native, để đảm bảo quá trình replay diễn ra hoàn hảo.

Việc không tuân thủ các quy tắc này sẽ dẫn đến lỗi *Non-Deterministic Error*, khiến workflow của bạn bị kẹt mãi mãi (blocked/stuck). Dưới đây là những quy tắc cốt lõi khi viết mã Go cho Workflow:

*   **Không sử dụng goroutines (`go func()`) hoặc channels gốc:** Temporal SDK cung cấp các API thay thế như `workflow.Go()` và `workflow.Channel`. Engine cần theo dõi và quản lý vòng đời của mọi tiến trình đồng thời bên trong workflow.
*   **Không sử dụng `time.Now()` hoặc `time.Sleep()`:** Luôn sử dụng `workflow.Now()` và `workflow.Sleep()`. Việc gọi `time.Now()` sẽ trả về các giá trị khác nhau giữa lần chạy ban đầu và lần replay, phá vỡ tính determinism.
*   **Không gọi API mạng, I/O trực tiếp (HTTP, Database):** Mọi tương tác với thế giới bên ngoài, có thể thành công hoặc thất bại tuỳ thời điểm, đều phải được đóng gói vào trong **Activity**. Workflow chỉ điều phối, không thực thi I/O.
*   **Không tạo Random (Số ngẫu nhiên, UUID):** Sử dụng các API do Temporal cung cấp, ví dụ như `workflow.SideEffect()` nếu cần gọi các hàm không deterministic, hoặc dùng các context API tương đương.
*   **Cẩn trọng khi duyệt `map`:** Trong Go, thứ tự lặp qua một `map` bằng `range` là ngẫu nhiên. Nếu logic workflow phụ thuộc vào thứ tự này, nó sẽ không deterministic. Hãy chuyển dữ liệu sang slice hoặc mảng rồi sort trước khi duyệt.

*Kinh nghiệm firsthand:* Trong một dự án xử lý thanh toán, team tôi từng vi phạm quy tắc này khi lỡ thêm một dòng `time.Now()` để log thời gian xử lý vào trong Workflow code thay vì Activity. Ngay ngày hôm sau, khi worker restart, hàng ngàn workflow báo lỗi Non-Deterministic và bị đình trệ. Việc gỡ rối những lỗi này yêu cầu phải hiểu sâu về versioning (`workflow.GetVersion()`) để vá lỗi code mà không phá vỡ history cũ.

## Phân biệt Workflow vs Activity & Triển khai Saga Pattern

Sự khác biệt giữa Temporal Workflow và Activity nằm ở vai trò, tính an toàn và giới hạn thiết kế. Workflow là nhạc trưởng (đòi hỏi determinism tuyệt đối, stateful), trong khi Activity là các nhạc công thực thi nhiệm vụ thực tế (stateless, có thể chứa I/O, retry tự động). Đối với các giao dịch phân tán, Workflow kết hợp Activity để quản lý Saga Pattern với danh sách compensation stack chạy theo thứ tự LIFO.

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

Đoạn mã Go dưới đây minh họa mô hình Saga Pattern trong Temporal Workflow. Bằng cách lưu trữ danh sách các hàm bồi hoàn (compensation functions) và thực thi theo thứ tự LIFO trong khối defer, workflow đảm bảo rollback an toàn toàn bộ các bước giao dịch trước đó khi gặp sự cố:

```go
package workflows

import (
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

type OrderRequest struct {
	UserID   string
	ItemID   string
	Amount   float64
	Quantity int
}

// OrderSagaWorkflow điều phối giao dịch phân tán mua hàng với cơ chế compensation LIFO
func OrderSagaWorkflow(ctx workflow.Context, req OrderRequest) (err error) {
	options := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute,
		RetryPolicy: &temporal.RetryPolicy{
			MaximumAttempts: 3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, options)

	// Khởi tạo stack lưu trữ các hàm bồi hoàn (compensation stack)
	var compensations []func(workflow.Context) error
	defer func() {
		if err != nil {
			// Thực thi các hàm bồi hoàn theo thứ tự ngược lại (LIFO)
			disconnectedCtx, _ := workflow.NewDisconnectedContext(ctx)
			for i := len(compensations) - 1; i >= 0; i-- {
				_ = compensations[i](disconnectedCtx)
			}
		}
	}()

	// Bước 1: Trừ tiền tài khoản
	var paymentID string
	err = workflow.ExecuteActivity(ctx, "ReservePaymentActivity", req.UserID, req.Amount).Get(ctx, &paymentID)
	if err != nil {
		return err
	}
	// Đăng ký bước bồi hoàn cho thanh toán
	compensations = append(compensations, func(c workflow.Context) error {
		return workflow.ExecuteActivity(c, "CancelPaymentActivity", paymentID).Get(c, nil)
	})

	// Bước 2: Giữ hàng trong kho
	var inventoryID string
	err = workflow.ExecuteActivity(ctx, "ReserveInventoryActivity", req.ItemID, req.Quantity).Get(ctx, &inventoryID)
	if err != nil {
		return err // Defer sẽ tự động kích hoạt CancelPaymentActivity
	}

	return nil
}
```

## Triển khai Temporal Worker & Scale out trong Production

Triển khai Temporal Worker yêu cầu cấu hình Task Queues và cân bằng tải hiệu quả. Để scale out, bạn cần deploy nhiều Worker container lắng nghe cùng một Task Queue, đồng thời tối ưu hoá các cấu hình bộ nhớ và số lượng goroutine hoạt động đồng thời (concurrent executions).

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

## Benchmark Thực tế & Compaction với ContinueAsNew

Khi vận hành Temporal trên production, bạn cần đo lường hiệu năng của hệ thống và chủ động kiểm soát kích thước event history. Kỹ thuật `workflow.ContinueAsNew` là giải pháp nén history bắt buộc khi số lượng sự kiện chạm mốc 10.000 events, ngăn ngừa lỗi tràn giới hạn 50.000 events của Temporal Cluster.

*Case study & Benchmark:*
Là một Senior Go Engineer, tôi từng tham gia scale cụm Temporal xử lý 50.000 workflow đồng thời. Dưới đây là những con số và bài học đắt giá:

*   **Benchmark Timeouts:**
    *   Đối với API gọi nội bộ: `StartToCloseTimeout` là 2s.
    *   Đối với Webhooks ra bên ngoài: `StartToCloseTimeout` là 30s.
    *   Luôn luôn sử dụng `ScheduleToCloseTimeout` (đã bao gồm thời gian nằm queue + số lần retry) như một SLA cứng, ví dụ: Không quá 5 phút cho một luồng đăng ký tài khoản.
*   **Lỗi History Limit Exceeded (Giới hạn 50K events / 50MB):**
    *   Temporal có giới hạn cứng về độ dài lịch sử của một workflow (thường là 50,000 events hoặc 50MB). Nếu workflow lặp vô tận hoặc xử lý event dài hạn, nó sẽ crash hoàn toàn.
    *   *Cách khắc phục:* Sử dụng `workflow.ContinueAsNew()` để khởi động lại workflow từ trạng thái sạch khi số lượng event chạm ngưỡng 10,000. Điều này giải phóng bộ nhớ DB backend và ngăn lỗi xảy ra.

Mẫu mã Golang bên dưới thể hiện cơ chế chủ động kiểm tra độ dài event history và thực thi hàm ContinueAsNew. Kỹ thuật này nén lịch sử sự kiện, ngăn chặn việc chạm mốc giới hạn 50.000 events của cụm Temporal Cluster:

```go
package workflows

import (
	"go.temporal.io/sdk/workflow"
)

type StreamState struct {
	ProcessedCount  int
	LastProcessedID string
}

// ProcessOrderStreamWorkflow xử lý dòng sự kiện liên tục và tự nén history khi chạm 10,000 events
func ProcessOrderStreamWorkflow(ctx workflow.Context, state StreamState) error {
	logger := workflow.GetLogger(ctx)

	for {
		var eventData string
		// Chờ nhận Signal từ hệ thống bên ngoài
		signalChan := workflow.GetSignalChannel(ctx, "OrderSignalChannel")

		var more bool
		signalChan.Receive(ctx, &eventData)
		state.ProcessedCount++
		state.LastProcessedID = eventData
		logger.Info("Đã xử lý signal", "count", state.ProcessedCount, "lastID", state.LastProcessedID)

		// Kiểm tra độ dài Lịch sử sự kiện (Event History) hiện tại của Workflow
		info := workflow.GetInfo(ctx)
		if info.GetCurrentHistoryLength() >= 10000 {
			logger.Info("History chạm ngưỡng 10,000 events. Kích hoạt ContinueAsNew để nén history.")
			// Tự tái tạo workflow mới với state đã nén, xóa sạch event history cũ
			return workflow.NewContinueAsNewError(ctx, ProcessOrderStreamWorkflow, state)
		}
	}
}
```

*   **Lỗi Không Handle Signals Kịp Thời:**
    *   Go channel trong workflow để nhận signals có thể bị block nếu không có cơ chế buffer hoặc timeout (`workflow.Selector`). Hàng ngàn signal ập đến mà workflow xử lý chậm sẽ gây phình database.

## FAQ: Câu hỏi thường gặp về Temporal

*   **Tôi có thể gọi API trực tiếp bên trong Temporal Workflow không?**
    Tuyệt đối không! Mọi I/O (gọi HTTP API, gõ DB) phải được đưa vào Activity. Việc gọi API trong Workflow phá vỡ nguyên tắc Determinism vì kết quả API có thể thay đổi trong quá trình replay.
*   **Làm sao để handle versioning khi update code của Temporal Workflow?**
    Trong Go SDK, bạn phải sử dụng hàm `workflow.GetVersion()`. Nó cho phép code của bạn phân nhánh an toàn giữa logic cũ và logic mới khi xử lý các workflow đang chạy dang dở (in-flight workflows) dựa trên lịch sử đã ghi.
*   **Temporal có thay thế Kafka được không?**
    Không. Kafka là hệ thống pub/sub (event streaming) thuần túy với throughput cực lớn (hàng triệu msg/s). Temporal là Workflow Orchestration Engine (quản lý trạng thái, timeouts, retries, saga). Chúng bổ trợ cho nhau: Kafka để luân chuyển event tốc độ cao, Temporal để quản lý vòng đời logic nghiệp vụ phức tạp.
