import frappe
import json
import logging
import traceback

no_cache = 1

def get_context(context):
    """
    Debug endpoint for auto_auth functionality
    """
    context.no_cache = 1
    context.debug_mode = True
    
    # Get request information
    context.request_method = frappe.local.request.method
    context.request_path = frappe.request.path
    context.query_params = {k: v for k, v in frappe.form_dict.items() if k != 'password'}
    
    # Get user information
    context.user = frappe.session.user
    context.is_logged_in = context.user != "Guest"
    
    # Get system information
    context.frappe_version = frappe.__version__
    
    # Setup debug action
    action = frappe.form_dict.get('action')
    
    if action == 'test_auth':
        # Test authentication directly
        context.test_results = test_auth()
        
    elif action == 'test_get_context':
        # Test the auto_auth get_context function
        context.test_results = test_get_context()
        
    elif action == 'test_post':
        # Test the auto_auth post function
        context.test_results = test_post()
    
    return context

@frappe.whitelist(allow_guest=True)
def debug_auth():
    """
    AJAX endpoint for debugging auth
    """
    try:
        action = frappe.form_dict.get('action')
        
        if action == 'test_auth':
            result = test_auth()
        elif action == 'test_get_context':
            result = test_get_context()
        elif action == 'test_post':
            result = test_post()
        elif action == 'test_js_auth':
            result = {
                'status': 'success',
                'message': 'Testing JS authentication',
                'timestamp': frappe.utils.now()
            }
        else:
            result = {
                'status': 'error',
                'message': f'Unknown action: {action}'
            }
            
        return result
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        }

def test_auth():
    """
    Test the authentication functionality
    """
    try:
        email = frappe.form_dict.get('email')
        password = frappe.form_dict.get('password')
        
        if not email or not password:
            return {
                'status': 'error',
                'message': 'Email and password are required'
            }
        
        # Import the function from auto_auth.py
        from crm.www.auto_auth import authenticate_user
        
        # Call the authenticate_user function
        result = authenticate_user(email, password)
        
        # Add debug info
        result['debug_info'] = {
            'timestamp': frappe.utils.now(),
            'user_before': frappe.session.user,
            'form_dict': {k: v for k, v in frappe.form_dict.items() if k != 'password'}
        }
        
        return result
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        }

def test_get_context():
    """
    Test the get_context function of auto_auth
    """
    try:
        # Store original form_dict
        original_form_dict = frappe.form_dict.copy()
        
        # Import the function from auto_auth.py
        from crm.www.auto_auth import get_context
        
        # Create a mock context
        context = frappe._dict()
        
        # Call the get_context function
        result = get_context(context)
        
        # Restore original form_dict
        frappe.form_dict = original_form_dict
        
        # Add debug info
        debug_info = {
            'timestamp': frappe.utils.now(),
            'user_before': frappe.session.user,
            'auth_success': result.get('auth_success', False),
            'form_dict': {k: v for k, v in frappe.form_dict.items() if k != 'password'}
        }
        
        return {
            'status': 'success',
            'context_keys': list(result.keys()),
            'auth_success': result.get('auth_success', False),
            'auth_message': result.get('auth_message', ''),
            'debug_info': debug_info
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        }

def test_post():
    """
    Test the post function of auto_auth
    """
    try:
        # Store original form_dict
        original_form_dict = frappe.form_dict.copy()
        original_response = frappe.response.copy()
        
        # Import the function from auto_auth.py
        from crm.www.auto_auth import post
        
        # Call the post function
        post()
        
        # Extract response
        response_data = frappe.response.copy()
        
        # Restore original form_dict and response
        frappe.form_dict = original_form_dict
        frappe.response = original_response
        
        # Add debug info
        debug_info = {
            'timestamp': frappe.utils.now(),
            'user_after': frappe.session.user,
            'form_dict': {k: v for k, v in frappe.form_dict.items() if k != 'password'}
        }
        
        return {
            'status': 'success',
            'response_data': response_data,
            'debug_info': debug_info
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        return {
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        } 