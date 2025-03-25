import frappe
from frappe import _
import json
import logging

no_cache = 1

# Set up logger
logger = logging.getLogger(__name__)

def get_context(context):
    """Get context for auto_auth page
    
    This checks for query parameters and attempts to authenticate
    if username/email and password are provided.
    """
    context.no_cache = 1
    
    # Log that we're handling a GET request
    logger.info("Auto Auth: Processing GET request")
    
    # Check if we have credentials in query parameters
    email = frappe.form_dict.get("email") or frappe.form_dict.get("username")
    password = frappe.form_dict.get("password")
    
    # Always set redirect to /crm
    redirect = frappe.form_dict.get("redirect", "/crm")
    
    # Log the parameters (excluding sensitive data)
    logger.info(f"Auto Auth: Received parameters: email={'[REDACTED]' if email else 'None'}, password={'[EXISTS]' if password else 'None'}")
    
    context.auth_success = False
    context.auth_message = ""
    context.show_form = False
    context.redirect_url = redirect
    
    if email and password:
        # Try to authenticate with the provided credentials
        try:
            logger.info(f"Auto Auth: Attempting to authenticate user: {email}")
            result = authenticate_user(email, password)
            context.auth_success = result.get("status") == "success"
            context.username = email
            
            logger.info(f"Auto Auth: Authentication result: {result.get('status')}")
            
            # Always redirect to /crm if authentication was successful
            if context.auth_success:
                logger.info(f"Auto Auth: Will redirect to: {redirect}")
        except Exception as e:
            logger.error(f"Error during auto_auth: {str(e)}", exc_info=True)
            context.auth_success = False
    else:
        # No credentials provided, show the form
        logger.info("Auto Auth: No credentials in parameters, showing form")
        context.show_form = True
        
    return context

@frappe.whitelist(allow_guest=True)
def post():
    """Handle POST requests for auto_auth"""
    try:
        # Log that we're handling a POST request
        logger.info("Auto Auth: Processing POST request")
        
        # Get data from request
        data = frappe.form_dict
        username = data.get("username") or data.get("email")
        password = data.get("password")
        redirect = data.get("redirect", "/crm")  # Default redirect to /crm
        create_user = data.get("create_user", "1") == "1"
        
        # Log the parameters (excluding sensitive data)
        logger.info(f"Auto Auth POST: Received parameters: email={'[REDACTED]' if username else 'None'}, password={'[EXISTS]' if password else 'None'}, redirect={redirect}, create_user={create_user}")
        
        if not username or not password:
            logger.warning("Auto Auth POST: Missing username or password")
            frappe.response["message"] = {
                "status": "error",
                "message": _("Username and password are required."),
                "success": False
            }
            return
            
        result = authenticate_user(username, password, create_user)
        
        # Add success flag for compatibility with frontend
        if "success" not in result:
            result["success"] = result.get("status") == "success"
            
        # Always set redirect to /crm
        if result.get("status") == "success":
            result["redirect"] = redirect
            
        frappe.response["message"] = result
            
        logger.info(f"Auto Auth POST: Authentication result: {result.get('status')}")
    except Exception as e:
        error_msg = f"Auto Auth Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        frappe.log_error(error_msg, "Auto Auth")
        frappe.response["message"] = {
            "status": "error",
            "message": _("An error occurred during authentication."),
            "error": str(e),
            "success": False
        }

def authenticate_user(username, password, create_user=True):
    """Authenticate a user with the given credentials
    
    If the user doesn't exist and create_user is True, a new one will be created.
    
    Args:
        username (str): Email of the user
        password (str): Password for authentication
        create_user (bool): Whether to create the user if they don't exist
        
    Returns:
        dict: Result with status and message
    """
    # Log authentication attempt
    logger.info(f"Auto auth attempt for user: {username}")
    
    if not username or not password:
        logger.warning(f"Auto auth failed: Missing username or password")
        return {"status": "error", "message": _("Username and password are required.")}
    
    # Check if user exists
    user_exists = frappe.db.exists("User", {"email": username})
    
    if not user_exists and create_user:
        logger.info(f"Creating new user: {username}")
        try:
            # Create new user
            user = frappe.get_doc({
                "doctype": "User",
                "email": username,
                "first_name": username.split("@")[0] if "@" in username else username,
                "enabled": 1,
                "new_password": password,
                "user_type": "Website User",
                "send_welcome_email": 0
            })
            user.flags.ignore_permissions = True
            user.flags.ignore_password_policy = True
            user.insert()
            
            # Set default roles for the user
            user.add_roles("Customer")
            
            frappe.db.commit()
            
            # Log in as the new user
            try:
                frappe.local.login_manager.login_as(username)
                frappe.local.login_manager.resume = True
                frappe.db.commit()
                
                logger.info(f"New user created and logged in successfully: {username}")
                return {
                    "status": "success", 
                    "message": _("User created and logged in successfully."),
                    "user": username,
                    "is_new_user": True
                }
            except Exception as e:
                logger.error(f"Error logging in as new user: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "message": _("User created but login failed: {0}").format(str(e))
                }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": _("Failed to create user: {0}").format(str(e))
            }
    
    # Attempt to log in
    try:
        frappe.flags.in_auto_auth = True  # Set a flag to indicate we're in auto_auth
        frappe.local.login_manager.authenticate(username, password)
        frappe.local.login_manager.post_login()
        frappe.flags.in_auto_auth = False  # Reset the flag
        
        # Make sure the session is saved to the database
        frappe.db.commit()
        
        logger.info(f"User logged in successfully: {username}")
        return {
            "status": "success", 
            "message": _("Logged in successfully."),
            "user": username,
            "is_new_user": False
        }
    except frappe.AuthenticationError as e:
        logger.warning(f"Authentication failed for user: {username}")
        return {
            "status": "error", 
            "message": _("Invalid credentials."),
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": _("An error occurred during login: {0}").format(str(e)),
            "error": str(e)
        } 