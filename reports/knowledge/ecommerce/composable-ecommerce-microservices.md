# Composable E-Commerce: 21-Service Decomposition with Golang, DDD & Dapr Event Mesh

> **Domain:** E-Commerce Architecture | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Bounded Contexts`, `Kratos Clean Architecture`, `Saga Choreography`, `Database-per-Service`

---

## 1. Problem Statement & Operational Context
Monolithic commerce frameworks (Magento, WooCommerce) couple product catalog, checkout, order state, and warehouse inventory into monolithic relational schemas. High-volume checkouts lock tables across business boundaries, causing sitewide downtime.

## 2. Core Architectural Invariants
1. **Database-per-Service Isolation:** Services never join or read foreign databases; all cross-boundary interactions occur via gRPC Protobuf APIs or Dapr CloudEvents.
2. **Single-Aggregate Transaction Boundary:** Business invariants are strictly maintained within individual aggregate roots; multi-service coordination uses compensating Sagas.
3. **Compile-Time Layer Decoupling:** `internal/biz` logic has zero dependencies on transport (HTTP/gRPC) or database libraries (Google Wire DI).

## 3. Domain Decomposition Matrix (5 Core Domains, 21 Services)
- **Core Commerce (7):** API Gateway, Catalog, Cart, Checkout Orchestrator, Order, Payment, Pricing/Promotion.
- **Logistics & Supply (5):** Inventory Reservation, Warehouse WMS, 3PL Shipping, Reverse Logistics (RMA), Supplier PO.
- **Identity & Engagement (5):** Customer Auth, Customer Profile, Loyalty Ledger, Notification Hub, Review/Moderation.
- **Data & Platform (4):** Search/Vector Re-rank, Clickstream Ingest, Audit Compliance, Feature Flag Engine.

## 4. Key Implementation Patterns

### Kratos Aggregate Root Definition (Go 1.25)
```go
type OrderAggregate struct {
    ID          string
    CustomerID  string
    Status      OrderStatus
    Items       []OrderLineItem
    TotalAmount int64
    Version     int64
    events      []DomainEvent
}

func (o *OrderAggregate) MarkAsPaid(paymentID string) error {
    if o.Status != OrderStatusPendingPayment {
        return errors.New("invalid status transition")
    }
    o.Status = OrderStatusPaid
    o.Version++
    o.events = append(o.events, DomainEvent{EventType: "order.paid", Payload: paymentID})
    return nil
}
```

## 5. Agent Retrieval Guidance
- **Apply When:** Migrating monoliths to microservices, architecting multi-warehouse retail systems, or implementing DDD in Go.
- **Related Articles:** `/posts/architecting-21-service-ecommerce-golang-ddd/`, `/posts/go-microservices/`.
