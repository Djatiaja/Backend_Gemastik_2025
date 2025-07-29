def base_response(code, status, message, data=None, error=None):
    """
    Create a standardized API response.
    
    Args:
        code (int): HTTP status code
        status (str): Status of the response (e.g., 'success', 'error')
        message (str): Descriptive message about the response
        data (dict, optional): Response data payload
        error (dict, optional): Error details if any
        
    Returns:
        dict: Standardized response dictionary
    """
    response = {
        'code': code,
        'status': status,
        'message': message,
        'data': data if data is not None else {},
        'error': error if error is not None else {}
    }
    return response