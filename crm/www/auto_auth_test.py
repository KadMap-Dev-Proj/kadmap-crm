import frappe
import json
import logging
from frappe.utils import get_request_site_address

def get_context(context):
    """
    Load context for auto_auth_test page
    """
    # Setup logging
    logger = logging.getLogger("auto_auth_test")
    logger.setLevel(logging.DEBUG)
    
    # Get request information
    context.request_method = frappe.local.request.method
    context.request_path = frappe.request.path
    context.query_params = {k: v for k, v in frappe.form_dict.items()}
    
    # Get user information
    context.user = frappe.session.user
    context.is_logged_in = context.user != "Guest"
    context.session_data = {
        "user": frappe.session.user,
        "sid": frappe.session.sid
    }
    
    # Auto_auth information
    context.auto_auth_exists = hasattr(frappe.get_hooks(), "auto_auth")
    context.site_url = get_request_site_address()
    
    # Log diagnostic information
    log_info = {
        "timestamp": frappe.utils.now(),
        "user": frappe.session.user,
        "request_path": frappe.request.path,
        "query_params": context.query_params,
        "user_agent": frappe.request.headers.get("User-Agent", "Not available")
    }
    logger.info(f"Auto Auth Test Page loaded: {json.dumps(log_info)}")
    
    return context

@frappe.whitelist(allow_guest=True)
def test_auto_auth():
    """
    Test the auto_auth functionality directly from Python
    """
    try:
        logger = logging.getLogger("auto_auth_test")
        logger.setLevel(logging.DEBUG)
        
        # Get parameters from request
        email = frappe.form_dict.get("email")
        password = frappe.form_dict.get("password")
        redirect = frappe.form_dict.get("redirect")
        
        if not email or not password:
            return {
                "success": False,
                "message": "Email and password are required",
                "request_data": {
                    "method": frappe.local.request.method,
                    "params": {k: v for k, v in frappe.form_dict.items() if k != "password"}
                }
            }
        
        # Test auto_auth directly
        logger.info(f"Testing auto_auth for email: {email}")
        
        # Check if user exists
        user_exists = frappe.db.exists("User", {"email": email})
        
        if not user_exists:
            # Create new user
            logger.info(f"Creating new user with email: {email}")
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": "Auto Auth",
                "last_name": "Test User",
                "send_welcome_email": 0,
                "enabled": 1,
                "new_password": password,
                "user_type": "Website User"
            })
            user.insert(ignore_permissions=True)
            logger.info(f"New user created: {email}")
        
        # Try to authenticate
        try:
            frappe.local.login_manager.authenticate(email, password)
            frappe.local.login_manager.post_login()
            
            logger.info(f"Authentication successful for: {email}")
            
            result = {
                "success": True,
                "message": "Authentication successful",
                "user": frappe.session.user,
                "is_new_user": not user_exists,
                "redirect": redirect if redirect else "/"
            }
        except frappe.AuthenticationError as e:
            logger.error(f"Authentication failed for {email}: {str(e)}")
            result = {
                "success": False,
                "message": f"Authentication failed: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            result = {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Auto Auth Test Error: {str(e)}", "Auto Auth Test")
        return {
            "success": False,
            "message": f"Internal server error: {str(e)}",
            "error": str(e)
        } 