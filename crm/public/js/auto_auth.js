/**
 * Auto Authentication for Frappe CRM
 * 
 * This script provides functions to automatically authenticate users in the CRM system.
 * It can:
 * - Check if a user is logged in
 * - Automatically log in a user or create one if needed
 * - Redirect after successful authentication
 */

frappe.provide('crm.auto_auth');

/**
 * Auto Auth module for CRM application
 * Provides utility functions for automatic authentication
 */
(function() {
    // Configuration
    var config = {
        debug: true, // Set to true for verbose logging
        authEndpoint: '/api/method/crm.www.auto_auth.post',
        defaultRedirect: '/app/crm',
        loaderTimeout: 30000, // 30 seconds timeout for loader
        retryAttempts: 2 // Number of retry attempts
    };

    // Private variables
    var _isAuthenticating = false;
    var _loaderTimeoutId = null;
    var _retryCount = 0;

    /**
     * Private logging function
     */
    function _log(message, level) {
        if (!config.debug) return;

        var prefix = '[CRM Auto Auth]';
        level = level || 'info';

        switch (level) {
            case 'error':
                console.error(prefix, message);
                break;
            case 'warn':
                console.warn(prefix, message);
                break;
            case 'debug':
                console.debug(prefix, message);
                break;
            default:
                console.log(prefix, message);
        }
    }

    /**
     * Check if the user is currently logged in
     */
    function isLoggedIn() {
        var isLoggedIn = frappe.session.user && frappe.session.user !== 'Guest';
        _log('Checking login status: ' + (isLoggedIn ? 'Logged in as ' + frappe.session.user : 'Not logged in'));
        return isLoggedIn;
    }

    /**
     * Show authentication loader
     */
    function _showLoader(message) {
        _log('Showing loader: ' + (message || 'Authenticating...'));

        var loader = document.getElementById('auth-loader');
        if (loader) {
            // Update message if provided
            if (message) {
                var messageEl = loader.querySelector('p');
                if (messageEl) messageEl.textContent = message;
            }

            loader.style.display = 'block';

            // Set timeout to prevent infinite loading
            _loaderTimeoutId = setTimeout(function() {
                _log('Loader timeout reached!', 'warn');
                _hideLoader();
                _showError('Authentication timed out. Please try again.');
            }, config.loaderTimeout);
        } else {
            _log('Loader element not found', 'warn');
        }
    }

    /**
     * Hide authentication loader
     */
    function _hideLoader() {
        _log('Hiding loader');

        // Clear timeout if exists
        if (_loaderTimeoutId) {
            clearTimeout(_loaderTimeoutId);
            _loaderTimeoutId = null;
        }

        var loader = document.getElementById('auth-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    function _showError(message) {
        _log('Showing error: ' + message, 'error');

        var messageEl = document.getElementById('auth-message');
        if (messageEl) {
            messageEl.innerHTML = '<div class="alert alert-danger">' + message + '</div>';
            messageEl.style.display = 'block';
        }

        // Show form after error
        var formEl = document.getElementById('auth-form');
        if (formEl) {
            setTimeout(function() {
                formEl.style.display = 'block';
            }, 2000);
        }
    }

    /**
     * Show success message
     */
    function _showSuccess(message) {
        _log('Showing success: ' + message);

        var messageEl = document.getElementById('auth-message');
        if (messageEl) {
            messageEl.innerHTML = '<div class="alert alert-success">' + message + '</div>';
            messageEl.style.display = 'block';
        }
    }

    /**
     * Redirect to specified URL
     */
    function _redirect(url) {
        _log('Redirecting to: ' + url);
        setTimeout(function() {
            window.location.href = url;
        }, 1000);
    }

    /**
     * Authenticate user with credentials
     * 
     * Options:
     * - username: User email or username
     * - password: User password
     * - redirectUrl: URL to redirect after successful authentication
     * - createUser: Whether to create user if not exists (default: true)
     * - useQueryParams: Whether to use query parameters instead of POST (default: false)
     * - onSuccess: Success callback function
     * - onError: Error callback function
     */
    function authenticate(options) {
        options = options || {};

        _log('Authentication requested with options:', 'debug');
        _log({
            username: options.username ? '[REDACTED]' : 'Not provided',
            password: options.password ? '[EXISTS]' : 'Not provided',
            redirectUrl: options.redirectUrl,
            createUser: options.createUser !== false,
            useQueryParams: !!options.useQueryParams
        }, 'debug');

        // Validate required fields
        if (!options.username || !options.password) {
            var error = 'Username and password are required';
            _log(error, 'error');

            if (options.onError) {
                options.onError({ message: error });
            }

            return false;
        }

        // Don't authenticate again if already in progress
        if (_isAuthenticating) {
            _log('Authentication already in progress', 'warn');
            return false;
        }

        _isAuthenticating = true;

        var redirectUrl = options.redirectUrl || config.defaultRedirect;
        var createUser = options.createUser !== false;

        _showLoader();

        // Use query parameters for authentication if specified
        if (options.useQueryParams) {
            _log('Using query parameters for authentication');

            var authUrl = generateAuthUrl({
                username: options.username,
                password: options.password,
                redirectUrl: redirectUrl
            });

            window.location.href = authUrl;
            return true;
        }

        // Use AJAX POST for authentication
        _log('Using AJAX POST for authentication');

        $.ajax({
            url: config.authEndpoint,
            type: 'POST',
            data: {
                email: options.username,
                password: options.password,
                create_user: createUser ? 1 : 0,
                redirect: redirectUrl
            },
            dataType: 'json',
            beforeSend: function(xhr) {
                // Ensure CSRF token is set for guest users
                if (frappe.csrf_token && frappe.csrf_token !== "None") {
                    xhr.setRequestHeader('X-Frappe-CSRF-Token', frappe.csrf_token);
                }
            },
            success: function(data) {
                _log('Authentication response received', 'debug');
                _log(data, 'debug');

                _isAuthenticating = false;
                _hideLoader();

                // Check for valid response
                if (!data || !data.message) {
                    var errorMsg = 'Invalid response from server';
                    _log(errorMsg, 'error');

                    _showError(errorMsg);

                    if (options.onError) {
                        options.onError({ message: errorMsg });
                    }
                    return;
                }

                var result = data.message;

                if (result.success || result.status === 'success') {
                    _log('Authentication successful');

                    _showSuccess(result.message || 'Authentication successful!');

                    if (options.onSuccess) {
                        options.onSuccess(result);
                    }

                    _redirect(result.redirect || redirectUrl);
                } else {
                    var errorMsg = result.message || result.error || 'Authentication failed';
                    _log('Authentication failed: ' + errorMsg, 'error');

                    _showError(errorMsg);

                    if (options.onError) {
                        options.onError(result);
                    }
                }
            },
            error: function(xhr, status, error) {
                _log('Authentication request error: ' + error, 'error');
                _log(xhr.responseText, 'debug');

                _isAuthenticating = false;
                _hideLoader();

                var errorMsg = 'Error during authentication';

                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response && response.message) {
                        if (typeof response.message === 'string') {
                            errorMsg = response.message;
                        } else if (response.message.message) {
                            errorMsg = response.message.message;
                        } else if (response.message.error) {
                            errorMsg = response.message.error;
                        }
                    }
                } catch (e) {
                    _log('Could not parse error response', 'error');
                }

                _showError(errorMsg);

                if (options.onError) {
                    options.onError({ message: errorMsg, originalError: error });
                }

                // Retry logic if needed
                if (_retryCount < config.retryAttempts) {
                    _retryCount++;
                    _log('Retrying authentication (attempt ' + _retryCount + ')', 'warn');

                    setTimeout(function() {
                        authenticate(options);
                    }, 1000);
                } else {
                    _retryCount = 0;
                }
            }
        });

        return true;
    }

    /**
     * Quick login utility - for direct login from other pages
     */
    function quickLogin(username, password, redirectUrl) {
        _log(`Quick login requested for user: ${username ? '[REDACTED]' : 'Not provided'} with redirect to: ${redirectUrl || config.defaultRedirect}`);

        return authenticate({
            username: username,
            password: password,
            redirectUrl: redirectUrl,
            createUser: true
        });
    }

    /**
     * Generate authentication URL with credentials as query parameters
     */
    function generateAuthUrl(options) {
        options = options || {};

        _log('Generating auth URL with options:', 'debug');
        _log({
            username: options.username ? '[REDACTED]' : 'Not provided',
            redirectUrl: options.redirectUrl
        }, 'debug');

        var params = new URLSearchParams();

        if (options.username) {
            params.append('email', options.username);
        }

        if (options.password) {
            params.append('password', options.password);
        }

        if (options.redirectUrl) {
            params.append('redirect', options.redirectUrl);
        }

        var url = '/auto_auth?' + params.toString();
        _log('Generated URL: ' + url.replace(/password=.*?(&|$)/, 'password=[REDACTED]$1'));

        return url;
    }

    // Public API
    crm.auto_auth = {
        authenticate: authenticate,
        quickLogin: quickLogin,
        isLoggedIn: isLoggedIn,
        generateAuthUrl: generateAuthUrl
    };
})();