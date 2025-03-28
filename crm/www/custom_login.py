import frappe

no_cache = 1

def get_context(context):
    """
    Redirect /login to /auto_auth
    
    This function is called when the /login route is accessed,
    and immediately redirects the user to the /auto_auth page.
    """
    context.no_cache = 1
    return {"redirect": "/auto_auth"} 