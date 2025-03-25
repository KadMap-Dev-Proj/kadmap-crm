# Auto Auth Guide

## Overview

Auto Auth is a seamless authentication mechanism specifically designed to make Frappe CRM compatible with KadMap Workspace. This integration feature enables automatic user login or account creation via URL parameters or JavaScript API calls, providing frictionless access between KadMap Workspace and the CRM system.

Key Features:
- One-click authentication between KadMap Workspace and Frappe CRM
- Automatic user creation if an account doesn't exist
- JavaScript API for programmatic authentication
- Immediate redirection to the CRM after successful authentication
- Robust error handling and user feedback

## How It Works

The Auto Auth system consists of three main components:

1. **URL Handler (`/auto_auth`)**: A web page that processes authentication parameters from the URL
2. **JavaScript API (`crm.auto_auth`)**: A client-side library for programmatic authentication
3. **Backend Controller**: Python code that handles authentication requests and manages user accounts

When a KadMap Workspace user accesses the `/auto_auth` endpoint with the required parameters, the system:
1. Extracts the credentials from the URL or form submission
2. Checks if the user exists in Frappe CRM, creating them if necessary (and if allowed)
3. Authenticates the user with Frappe's authentication system
4. Redirects to the CRM application upon success

## Usage

### Authentication via URL

The simplest way to use Auto Auth is by creating a URL with the necessary authentication parameters:

```
/auto_auth?email=user@example.com&password=YourPassword123
```

This URL can be embedded in KadMap Workspace for seamless CRM access. When clicked, it will automatically:
- Create the user if they don't exist
- Authenticate them
- Redirect them to the CRM

### Custom Redirect (Optional)

You can specify a custom redirect URL:

```
/auto_auth?email=user@example.com&password=YourPassword123&redirect=/specific-crm-page
```

### Using the JavaScript API

For programmatic authentication from KadMap Workspace:

```javascript
// Quick login (simplest method)
crm.auto_auth.quickLogin("user@example.com", "YourPassword123");

// Advanced options
crm.auto_auth.authenticate({
    username: "user@example.com",
    password: "YourPassword123",
    redirectUrl: "/custom-redirect",
    createUser: true,  // Set to false to prevent user creation
    useQueryParams: false,  // Set to true to use URL parameters instead of AJAX
    onSuccess: function(result) {
        console.log("Authentication successful", result);
    },
    onError: function(error) {
        console.error("Authentication failed", error);
    }
});
```

## API Reference

### URL Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `email` or `username` | User's email address | Yes |
| `password` | User's password | Yes |
| `redirect` | URL to redirect after successful authentication (default: `/crm`) | No |

### JavaScript API

#### `crm.auto_auth.authenticate(options)`

Authenticates a user with the provided credentials.

**Options:**
- `username`: User's email address (required)
- `password`: User's password (required)
- `redirectUrl`: URL to redirect after successful authentication (default: `/crm`)
- `createUser`: Whether to create a new user if they don't exist (default: `true`)
- `useQueryParams`: Whether to use URL parameters instead of AJAX (default: `false`)
- `onSuccess`: Callback function on successful authentication
- `onError`: Callback function on authentication failure

**Returns:** `boolean` indicating if the authentication request was initiated

#### `crm.auto_auth.quickLogin(username, password, redirectUrl)`

Simplified method for quick authentication.

**Parameters:**
- `username`: User's email address (required)
- `password`: User's password (required)
- `redirectUrl`: URL to redirect after successful authentication (optional)

**Returns:** `boolean` indicating if the authentication request was initiated

#### `crm.auto_auth.isLoggedIn()`

Checks if the user is currently logged in.

**Returns:** `boolean` indicating if the user is logged in

## Implementation Notes

- Successful authentication redirects users to `/crm` by default
- Errors are displayed on the authentication page with an option to try again
- A loading spinner is shown during authentication
- The timeout for authentication requests is 15 seconds
- Designed for seamless integration with KadMap Workspace

## Troubleshooting

### Common Issues

1. **Authentication Timeout**: If the authentication process takes too long, check network connectivity and server load.

2. **Invalid Credentials**: Ensure the username and password are correct.

3. **User Not Created**: If a new user isn't being created, verify that `createUser` is set to `true`.

4. **Redirect Not Working**: Ensure the redirect URL is valid and accessible to the user.

### Debug Mode

For advanced troubleshooting, you can enable debug mode in the JavaScript API:

```javascript
// Enable debug mode
crm.auto_auth.config = crm.auto_auth.config || {};
crm.auto_auth.config.debug = true;
```

This will output detailed logs to the browser console. 