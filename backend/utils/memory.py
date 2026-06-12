from strands.session.file_session_manager import FileSessionManager

def get_session_manager():
    session_manager = FileSessionManager(
        session_id="user-123",
        storage_dir="tmp/sessions"  # Optional, defaults to a temp directory
    )
    return session_manager