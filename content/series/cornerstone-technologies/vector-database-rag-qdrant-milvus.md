---
title: "Vector Database là gì? Kiến trúc HNSW & RAG Pipeline (Qdrant)"
meta: "Vector Database là gì? Hướng dẫn chuyên sâu về kiến trúc Vector DB, giải phẫu thuật toán HNSW, so sánh Qdrant vs Milvus và cách tối ưu RAM cho RAG Pipeline."
slug: vector-database-rag-qdrant-milvus
author: "Lê Tuấn Anh (Senior Go Engineer)"
author_profile: "/about/"
credentials: "Kinh nghiệm thiết kế hệ thống AI Engineering & High-Concurrency"
---

# Vector Database là gì? Kiến trúc HNSW & RAG Pipeline (Qdrant)

Trong kỷ nguyên của AI sinh tạo (Generative AI) và Large Language Models (LLMs), khả năng hiểu và truy xuất dữ liệu phi cấu trúc một cách linh hoạt là yếu tố quyết định sự thành bại của các ứng dụng thông minh. Nếu bạn đang thiết kế một kiến trúc nền tảng cho [Cornerstone Technologies](/series/cornerstone-technologies/), bạn sẽ không thể bỏ qua vai trò của Vector Database. Khác với các hệ quản trị cơ sở dữ liệu truyền thống, Vector Database là thành phần hạt nhân trong một [AI Data Engineering Pipeline](/series/ai-data-engineering-pipeline/executive-summary/) thực thụ, đảm nhiệm trọng trách biến ngôn ngữ tự nhiên thành tri thức có thể tính toán được.

Bài viết này sẽ đi sâu vào kiến trúc nội tại của Vector Database, mổ xẻ cách thuật toán HNSW vận hành dưới nắp capo, so sánh hai thế lực đáng gờm (Qdrant và Milvus), và quan trọng nhất: những bài học xương máu (firsthand account) về tối ưu Memory Profiling trên môi trường production từ góc nhìn của một Kỹ sư Hệ thống.

## Vector Database là gì? Trái tim của hệ thống AI

**Answer-first:** Vector Database (Cơ sở dữ liệu Vector) là loại database chuyên dụng để lưu trữ và truy vấn dữ liệu dưới dạng các mảng số (vector embeddings) nhiều chiều. Chúng sử dụng các thuật toán Approximate Nearest Neighbor (như HNSW) để tìm kiếm dữ liệu có ngữ nghĩa tương đồng (semantic search) siêu tốc, làm nền tảng cốt lõi cho các hệ thống RAG và AI Agents.

Để hiểu sâu sắc lý do Vector Database trở nên không thể thiếu, chúng ta cần xem xét sự khác biệt căn bản của nó so với Relational Database (Cơ sở dữ liệu quan hệ) và cách nó biểu diễn dữ liệu.

Relational Database (như MySQL, PostgreSQL) lưu trữ dữ liệu trong các bảng có cấu trúc nghiêm ngặt (hàng và cột). Khi tìm kiếm, chúng ta dùng ngôn ngữ SQL để thực thi các lệnh so khớp chính xác (exact match - ví dụ: `WHERE name = 'John'`) hoặc so khớp chuỗi một cách cơ bản. Điều này cực kỳ hiệu quả đối với dữ liệu giao dịch, tài chính hay thông tin người dùng. Tuy nhiên, khi đối mặt với dữ liệu phi cấu trúc như văn bản (một đoạn văn, một bài báo), hình ảnh, hoặc âm thanh, cách tiếp cận này hoàn toàn vô vọng trong việc nắm bắt "ý nghĩa" hay "ngữ cảnh".

Đó là lúc **Vector Embeddings** xuất hiện. Embedding là quá trình sử dụng các mô hình Machine Learning (như mô hình text-embedding-ada-002 của OpenAI với 1536 chiều, hay các mô hình BERT với 768 chiều) để biến một đoạn text, một hình ảnh thành một mảng số thực dài. Mảng số này mã hóa ý nghĩa ngữ nghĩa của đối tượng đó. Hai câu có cấu trúc từ vựng hoàn toàn khác nhau nhưng cùng mang một ý nghĩa (ví dụ: "Chiếc xe hơi màu đỏ" và "Phương tiện giao thông bốn bánh sắc đỏ") sẽ có hai vector nằm rất gần nhau trong không gian nhiều chiều.

Vector Database sinh ra để lưu trữ hàng triệu, thậm chí hàng tỷ vector này và cung cấp khả năng tìm kiếm các vector lân cận gần nhất (Nearest Neighbors) so với một query vector đầu vào. Thay vì tìm kiếm sự trùng khớp ký tự, nó đo lường khoảng cách hình học (ví dụ: Cosine Similarity, L2 Euclidean Distance) giữa các vector. Điều này đặc biệt thiết yếu đối với các hệ thống Retrieval-Augmented Generation (RAG) và có [ứng dụng trong Agentic Search](/series/agentic-ecommerce-search/part-3-qdrant-hybrid-search/).

## Giải phẫu thuật toán HNSW (Hierarchical Navigable Small World)

**Answer-first:** HNSW (Hierarchical Navigable Small World) là thuật toán tìm kiếm lân cận gần đúng (ANN) hoạt động bằng cách xây dựng một đồ thị nhiều tầng. Các tầng trên cùng thưa thớt giúp duyệt nhanh các khoảng cách xa, trong khi các tầng dưới cùng dày đặc giúp tìm chính xác các điểm lân cận gần nhất, mang lại độ trễ mili-giây.

Trong thế giới của Vector Database, việc tìm kiếm chính xác (K-Nearest Neighbors - KNN) bằng cách duyệt qua tất cả các vector là bất khả thi về mặt thời gian khi tập dữ liệu lên tới hàng chục triệu điểm. Thuật toán HNSW ra đời để giải bài toán đánh đổi: chúng ta chấp nhận giảm một tỷ lệ nhỏ độ chính xác tuyệt đối (Approximate Nearest Neighbor - ANN) để đạt tốc độ tìm kiếm siêu việt.

HNSW hoạt động dựa trên các nguyên lý sau đây:

- **Cấu trúc Đồ thị nhiều tầng (Hierarchical Graph):** Tương tự như cách cấu trúc dữ liệu Skip List hoạt động, HNSW tổ chức các vector thành một tập hợp các tầng (layers). Tầng cao nhất (Tầng $L$) chỉ chứa rất ít các node phân tán rộng rãi. Tầng dưới cùng (Tầng $0$) chứa tất cả các node.
- **Quá trình tìm kiếm (Routing / Search):** Khi có một truy vấn (query vector), quá trình tìm kiếm luôn bắt đầu từ tầng trên cùng. Thuật toán tìm node gần query nhất ở tầng này, sau đó nhảy xuống tầng dưới, dùng node vừa tìm được làm điểm bắt đầu, tiếp tục tìm node lân cận gần hơn. Nhờ cấu trúc thưa thớt ở tầng trên, thuật toán nhanh chóng vượt qua các khoảng không gian lớn (như đi máy bay), và ở các tầng dưới, nó tinh chỉnh kết quả cục bộ (như đi xe đạp vào ngõ nhỏ).
- **Small World Network:** Đặc tính "Small World" đảm bảo rằng luôn có các đường nối ngắn gọn (short paths) giữa bất kỳ hai điểm nào trong đồ thị, dù chúng có xa nhau tới đâu trong không gian nhiều chiều. Điều này làm cho chi phí tìm kiếm chỉ theo độ phức tạp logarit $O(\log n)$.
- **Quá trình Xây dựng Đồ thị (Graph Construction & Insertions):** Khi một vector mới được chèn vào, nó được thêm vào các tầng từ dưới lên trên. Xác suất một vector được thăng cấp lên tầng trên giảm theo hàm mũ, điều này giúp duy trì tính phân cấp hợp lý. Quá trình tạo liên kết (edges) giữa các node đòi hỏi thuật toán đánh giá và loại bỏ bớt liên kết theo heuristic để tối ưu độ phức tạp duyệt.
- **Ưu và nhược điểm:** Ưu điểm lớn nhất của HNSW là sự cân bằng tuyệt vời giữa độ trễ (latency) cực thấp và độ chính xác (recall) rất cao (thường > 95%). Tuy nhiên, nhược điểm chí mạng của HNSW là **tiêu tốn bộ nhớ rất lớn (High Memory Footprint)** do phải duy trì toàn bộ cấu trúc đồ thị (edges và nodes) trên RAM để duy trì tốc độ truy xuất cực nhanh.

## So sánh Qdrant vs Milvus vs pgvector

**Answer-first:** Qdrant là Vector DB viết bằng Rust, tối ưu cho single-node và scale vừa phải; Milvus viết bằng Go/C++, kiến trúc phân tán cloud-native phù hợp với dữ liệu tỷ scale; pgvector là extension của PostgreSQL, lý tưởng khi hệ thống đã dùng Postgres và dữ liệu dưới vài triệu vectors.

Việc chọn hệ quản trị Vector DB phụ thuộc hoàn toàn vào bài toán kiến trúc, quy mô dữ liệu và hệ sinh thái kỹ thuật hiện hữu của team. Dưới đây là bảng so sánh chi tiết:

| Tiêu chí | Qdrant | Milvus | pgvector (PostgreSQL) |
| --- | --- | --- | --- |
| **Kiến trúc lõi** | Standalone / Phân tán (Rust) | Distributed Cloud-native Microservices (Go/C++) | Extension trên SQL DB (C) |
| **Thuật toán chính** | HNSW (Tối ưu riêng bằng Rust) | HNSW, IVFFlat, DiskANN, SCANN | HNSW, IVFFlat |
| **Quy mô (Scalability)** | Tối ưu cho hàng chục đến hàng trăm triệu vectors. Chạy tốt trên single-node. | Thiết kế cho hàng tỷ (Billion-scale) vectors. Phân tách rạch ròi Storage/Compute. | Phù hợp với Scale nhỏ và vừa (dưới vài triệu vectors). |
| **Tiêu thụ RAM** | Cao (do lưu HNSW trên RAM), nhưng hỗ trợ tốt Scalar Quantization và Memmap. | Rất cao, đòi hỏi cụm máy chủ lớn và cấu hình phức tạp. | Thấp đến trung bình, tận dụng được shared_buffers của Postgres. |
| **Use-case lý tưởng** | RAG pipelines cần tốc độ cao, triển khai dễ, cần payload JSON lọc (Filtering) phức tạp. | Dự án Enterprise AI, multi-tenancy, stream data mạnh, khối lượng dữ liệu khổng lồ. | Tích hợp Vector search ngay cạnh dữ liệu quan hệ (relational data), không muốn thêm DB mới. |

## Triển khai RAG Pipeline với Qdrant và Go

**Answer-first:** Triển khai RAG Pipeline với Qdrant và Go bao gồm các bước: chuẩn bị dữ liệu văn bản, gọi API embedding (như OpenAI) để biến text thành mảng số, lưu trữ vào Qdrant collection, và cuối cùng truy vấn vector để tìm kiếm ngữ nghĩa khi có request từ người dùng.

Để minh chứng cho sức mạnh của Qdrant trong vai trò lõi của hệ thống, sau đây là quy trình 5 bước cơ bản để xây dựng một pipeline RAG (Retrieval-Augmented Generation) bằng ngôn ngữ Go:

1.  **Khởi tạo Qdrant Client bằng Go:** Sử dụng gRPC client chính thức để kết nối đến Qdrant Server. gRPC cung cấp hiệu năng tốt hơn đáng kể so với REST API.
2.  **Tạo Collection với cấu hình Dimension:** Khởi tạo một "Collection" (tương đương Table trong SQL). Cần khai báo chính xác số chiều của vector. Ví dụ, nếu sử dụng mô hình OpenAI `text-embedding-ada-002`, `size` phải thiết lập bằng `1536`. Kèm theo là thông số cấu hình khoảng cách (Distance), thường dùng là `Cosine`.
3.  **Tạo Embeddings từ Raw Text:** Dữ liệu nguồn (văn bản) cần được phân mảnh (chunking) hợp lý (ví dụ: 500 tokens mỗi đoạn). Sau đó, gọi API của LLM Provider (như OpenAI, Cohere) hoặc chạy mô hình local để chuyển đổi text thành dạng slice số thực (`[]float32` trong Go).
4.  **Upsert Vectors vào Qdrant kèm Payload:** Chèn (Upsert) các vector này vào Qdrant. Đặc điểm xuất sắc của Qdrant là cho phép lưu kèm theo metadata dưới dạng JSON (gọi là Payload). Payload này rất quan trọng để lưu ID tài liệu, nội dung văn bản thô, tác giả, v.v., phục vụ cho việc lọc (Filtering) sau này.
5.  **Truy vấn ngữ nghĩa (Semantic Search) và RAG:** Khi người dùng đặt câu hỏi, ta chuyển câu hỏi đó thành vector, rồi truy vấn Qdrant để lấy Top-K vectors gần nhất. Lấy các văn bản (nằm trong payload) từ kết quả đó và đính kèm vào prompt gửi cho LLM để tạo ra câu trả lời dựa trên context.

## Memory Profiling: Tối ưu RAM cho hàng triệu Vectors

**Answer-first:** Tối ưu RAM cho hàng triệu vectors đòi hỏi phải tính toán trước memory footprint (công thức: Vectors * Dimensions * 4 bytes + HNSW overhead). Việc áp dụng Scalar Quantization (ép kiểu f32 xuống int8) có thể giảm 4x lượng RAM tiêu thụ mà độ chính xác (accuracy) chỉ giảm chưa tới 1-2%.

Quản trị RAM là ác mộng lớn nhất khi vận hành Vector Database trên production. Thuật toán HNSW đem lại tốc độ xé gió, nhưng cái giá phải trả là nó cần toàn bộ dữ liệu (hoặc phần lớn cấu trúc đồ thị) phải thường trực trên RAM.

Với vai trò Senior Go Engineer, tôi từng đối mặt với sự cố **OOM (Out of Memory) thảm họa trên production** khi nhồi hơn 5 triệu vectors 1536-dims (kèm metadata) vào Qdrant trên một máy chủ 32GB RAM. Trong trạng thái bình thường, máy chủ ngốn khoảng 25GB, tưởng chừng như vẫn an toàn. Nhưng khi có biến động dữ liệu và HNSW graph bắt đầu quá trình re-indexing ở chế độ nền, lượng RAM đột ngột vọt lên đỉnh điểm, vượt quá giới hạn và khiến hệ điều hành kill process Qdrant ngay lập tức. Hệ thống sập cục bộ. Bài học rút ra là: **Tuyệt đối không được đoán mò kích thước RAM.**

Dưới đây là công thức tính toán Memory Footprint và những con số thực tế bạn cần nằm lòng:

-   **Mức tiêu thụ gốc (Raw Vector Size):** Công thức tính RAM cơ bản cho bản thân vector (sử dụng chuẩn float32 – 4 bytes): `Số lượng Vectors * Số chiều (Dimensions) * 4 bytes`.
    -   *Metric 1:* RAM cho 1 triệu vectors 1536-dims = $1,000,000 \times 1536 \times 4 \text{ bytes} \approx 6.14 \text{ GB}$.
-   **Chi phí HNSW Overhead:** Đồ thị HNSW không miễn phí. Mỗi node trong đồ thị cần lưu trữ các liên kết (edges) tới các node khác ở nhiều tầng khác nhau.
    -   *Metric 2:* Cấu trúc HNSW thường tiêu thụ thêm khoảng 1.5x - 2x kích thước của raw vectors. Nghĩa là tổng cộng, bạn sẽ tiêu tốn khoảng **~10-12 GB RAM cho 1 triệu vectors 1536-dims** nếu load toàn bộ lên RAM.
-   **Kỹ thuật Scalar Quantization (SQ):** Đây là cứu cánh cho bài toán bộ nhớ. SQ thực hiện việc nén (compress) các giá trị số thực dạng `float32` (4 bytes) xuống số nguyên `int8` (1 byte), hoặc thấp hơn là Binary Quantization (1 bit).
    -   *Metric 3:* Áp dụng Scalar Quantization int8 giúp tiết kiệm tới ~75% lượng RAM. Kích thước raw vector cho 1M vectors chỉ còn $\approx 1.5 \text{ GB}$, đưa tổng yêu cầu RAM về mức rất an toàn.
-   **Tác động đến Latency Benchmark:** Kích thước dữ liệu nhỏ hơn đồng nghĩa với việc CPU cache (L1/L2) làm việc hiệu quả hơn (cache line fit tốt hơn).
    -   *Metric 4:* Một truy vấn HNSW với 1 triệu vectors chưa nén trên Qdrant mất khoảng **~5-15ms**. Tuy nhiên, khi dùng Scalar Quantization, thời gian xử lý khoảng cách có thể giảm xuống chỉ còn **~2-8ms**. Đánh đổi lại, độ chính xác (recall) thường chỉ sụt giảm chưa tới 1-2%, một tỷ lệ hoàn toàn có thể chấp nhận được với hầu hết các ứng dụng RAG.

Ngoài ra, Qdrant cung cấp tính năng **Memmap (Memory Mapping)**, cho phép lưu trữ vectors trên ổ đĩa SSD tốc độ cao (NVMe) và chỉ nạp (page in) vào RAM những trang nhớ cần thiết. Nếu kết hợp SQ và Memmap, bạn có thể chạy hàng trăm triệu vector trên một node với chi phí phần cứng rẻ hơn rất nhiều, dù độ trễ có thể tăng nhẹ.

## FAQ: Câu hỏi thường gặp về Vector DB

**Answer-first:** Dưới đây là các câu hỏi thường gặp khi triển khai Vector DB trên production, giải đáp về việc có nên dùng pgvector thay thế, khái niệm Quantization giúp giảm RAM, và khả năng hỗ trợ CRUD của các Vector DB hiện đại.

-   **Có nên dùng pgvector thay vì một Vector DB chuyên dụng không?**
    Nếu dự án của bạn đã có sẵn PostgreSQL, lượng dữ liệu vector tương đối nhỏ (dưới vài triệu vectors), và bạn muốn tận dụng các phép JOIN giữa dữ liệu quan hệ và vector trong cùng một câu query SQL, pgvector là sự lựa chọn tuyệt vời. Tuy nhiên, nếu bạn xây dựng hệ thống đòi hỏi scale lên hàng chục/trăm triệu vectors, yêu cầu tốc độ ms siêu thấp dưới tải nặng, và cần các tính năng chuyên sâu như Scalar Quantization, Payload Filtering riêng biệt, Qdrant hoặc Milvus chuyên dụng sẽ vượt trội hơn hẳn pgvector về hiệu năng.

-   **Quantization trong Vector DB là gì?**
    Quantization là kỹ thuật nén dữ liệu vector nhằm giảm dung lượng bộ nhớ. Scalar Quantization (SQ) thu hẹp khoảng biểu diễn số liệu (ví dụ từ float32 xuống int8). Product Quantization (PQ) chia vector thành nhiều đoạn nhỏ và nén chúng bằng cụm (clustering), giúp tiết kiệm mạnh bộ nhớ. Đổi lại, quá trình tìm kiếm sẽ tính toán khoảng cách "xấp xỉ", làm giảm nhẹ mức độ chính xác của kết quả.

-   **Vector DB có hỗ trợ CRUD như database truyền thống không?**
    Có. Các Vector DB hiện đại (như Qdrant, Milvus, Weaviate) không chỉ tìm kiếm mà còn hỗ trợ đầy đủ các thao tác CRUD (Create, Read, Update, Delete). Bạn có thể Upsert vector mới, Update metadata (payload), Xóa vector bằng ID, hoặc thậm chí xóa vector dựa trên các bộ lọc (filter) trên payload. Tuy nhiên, do cấu trúc đồ thị HNSW khá phức tạp, việc Update hay Delete liên tục (high-frequency) có thể gây phân mảnh đồ thị, buộc database phải thực hiện các tiến trình dọn dẹp và re-indexing ngầm tốn tài nguyên. Do đó, Vector DB tối ưu nhất cho các trường hợp "Write-Once, Read-Many".
