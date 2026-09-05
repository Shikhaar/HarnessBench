package com.example.payment;

public class PaymentRequest {
    private final String orderId;
    private final double amount;
    private final String token;

    public PaymentRequest(String orderId, double amount, String token) {
        this.orderId = orderId;
        this.amount = amount;
        this.token = token;
    }

    public String getOrderId() { return orderId; }
    public double getAmount() { return amount; }
    public String getToken() { return token; }
}
