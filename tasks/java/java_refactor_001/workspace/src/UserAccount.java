package com.example;

public class UserAccount {
    private String username;
    private String email;
    private String role;
    private boolean enabled;

    // BUG: Telescoping constructor anti-pattern, no Builder
    public UserAccount(String username, String email, String role, boolean enabled) {
        this.username = username;
        this.email = email;
        this.role = role;
        this.enabled = enabled;
    }

    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getRole() { return role; }
    public boolean isEnabled() { return enabled; }
}
