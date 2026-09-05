# Java Multi-Module Contract: Synchronize PaymentRequest Call

### Context
In this multi-module repository, module `payment-api` updated `PaymentRequest` constructor to `(String orderId, double amount, String token)` with getter `getToken()`. Module `order-service` in `order-service/src/OrderService.java` still uses obsolete arguments and deprecated getter `getPaymentToken()`.

### Objective
1. Update `processOrder()` in `order-service/src/OrderService.java` to invoke `new PaymentRequest(orderId, amount, token)`.
2. Update `process()` to call `req.getToken()` instead of `req.getPaymentToken()`.
3. Do not modify `payment-api`.

### Style
Idiomatic Java cross-module communication adhering to published interface contracts.

### Tone
Contract-driven, multi-module dependency alignment.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `order-service/src/OrderService.java` to restore compilation and compatibility.
