# Simple syntax check
try:
    from services.github.pulls.get_review_thread_comments import get_review_thread_comments
    print("Import successful")
    
    # Check if function exists and has correct signature
    import inspect
    sig = inspect.signature(get_review_thread_comments)
    print(f"Function signature: {sig}")
except Exception as e:
    print(f"Error: {e}")
