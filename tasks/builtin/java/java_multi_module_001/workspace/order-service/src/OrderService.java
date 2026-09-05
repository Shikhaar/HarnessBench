package com.example.order;

import com.example.payment.PaymentRequest;

public class OrderService {
    public boolean processOrder(String orderId, double amount, String token) {
        PaymentRequest req = new PaymentRequest(orderId, amount, token);
        // BUG: Calling obsolete method getPaymentToken()
        String t = req.getPaymentToken();
        return t != null && !t.isEmpty();
    }
}
