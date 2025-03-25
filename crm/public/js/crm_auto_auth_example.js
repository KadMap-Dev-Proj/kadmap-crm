/**
 * Example of how to use auto_auth in a CRM context
 * This can be included in specific CRM pages or functionality
 */

frappe.provide('crm.examples');

// Example function to check if a user is logged in and auto-login if not
crm.examples.ensureAuthenticated = function(opts = {}) {
    // Default options
    const options = Object.assign({
        username: 'demo@crmuser.com',
        password: 'Demo@123',
        redirectUrl: '/app/crm',
        showMessage: true,
        showLoader: true,
        useQueryParams: true, // Default to using query parameters
        onSuccess: null,
        onError: null
    }, opts);

    // Check if user is already logged in
    if (crm.auto_auth.isLoggedIn()) {
        if (options.showMessage) {
            frappe.show_alert({
                message: `Logged in as ${frappe.session.user}`,
                indicator: 'green'
            });
        }

        if (options.onSuccess) {
            options.onSuccess({
                status: 'success',
                message: 'Already logged in',
                user: frappe.session.user
            });
        }

        return true;
    }

    // User is not logged in, authenticate
    crm.auto_auth.authenticate({
        username: options.username,
        password: options.password,
        redirectUrl: options.redirectUrl,
        showLoader: options.showLoader,
        useQueryParams: options.useQueryParams,
        onSuccess: function(data) {
            if (options.showMessage) {
                frappe.show_alert({
                    message: `Successfully logged in as ${data.user}`,
                    indicator: 'green'
                });
            }

            if (options.onSuccess) {
                options.onSuccess(data);
            }
        },
        onError: function(error) {
            if (options.showMessage) {
                frappe.show_alert({
                    message: `Login failed: ${error.message}`,
                    indicator: 'red'
                });
            }

            if (options.onError) {
                options.onError(error);
            }
        }
    });

    return false;
};

// Example of how to create an auto-login link
crm.examples.createAutoLoginLink = function(opts = {}) {
    const options = Object.assign({
        username: 'demo@crmuser.com',
        password: 'Demo@123',
        redirectUrl: '/app/crm',
        linkText: 'Auto Login'
    }, opts);

    const authUrl = crm.auto_auth.generateAuthUrl({
        username: options.username,
        password: options.password,
        redirectUrl: options.redirectUrl
    });

    return `<a href="${authUrl}" class="btn btn-sm btn-primary">${options.linkText}</a>`;
};

// Example of integration in a CRM lead page
$(document).ready(function() {
    // Check if we're on a CRM page
    if (window.location.pathname.indexOf('/app/crm') === 0 ||
        window.location.pathname.indexOf('/crm') === 0) {

        // Add a login button to the page if user is not logged in
        if (!crm.auto_auth.isLoggedIn()) {
            // Only add this in a non-production environment
            if (frappe.boot && frappe.boot.developer_mode) {
                // Add buttons to the page (this is just an example)
                setTimeout(function() {
                    const $header = $('.page-head');
                    if ($header.length) {
                        // Add auto-login button
                        const $loginBtn = $('<button class="btn btn-sm btn-primary mr-2">Auto Login</button>');
                        $loginBtn.click(function() {
                            crm.examples.ensureAuthenticated({
                                showLoader: true,
                                useQueryParams: true // Use query params for login
                            });
                        });

                        // Add auto-login link (direct URL approach)
                        const authLinkHtml = crm.examples.createAutoLoginLink({
                            linkText: 'Login Link'
                        });

                        $header.find('.standard-actions').prepend(authLinkHtml);
                        $header.find('.standard-actions').prepend($loginBtn);
                    }
                }, 1000);
            }
        }
    }
});