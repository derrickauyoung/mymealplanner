"""
Utility functions for running sessions and returning the final response.
"""
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def run_session(
    runner_instance: Runner,
    session_service: InMemorySessionService,
    user_queries: str,
    app_name: str = "agents",
    user_id: str = "default_user",
    session_id: str = "default"
) -> str:
    """Helper function to run queries in a session and return the final response.
    
    Args:
        runner_instance: The runner instance to use.
        session_service: The session service to use.
        user_queries: The user queries to run.
        app_name: The app name to use.
        user_id: The user id to use.
        session_id: The session id to use.

    Returns:
        The final response text.
    """
    print(f"\n### Session: {session_id}")

    try:
        # Create or retrieve session
        try:
            session = await session_service.create_session(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
        except Exception as e:
            try:
                session = await session_service.get_session(
                    app_name=app_name, user_id=user_id, session_id=session_id
                )
            except Exception:
                session = await session_service.create_session(
                    app_name=app_name, user_id=user_id, session_id=session_id
                )

        # Convert to query content
        query_content = types.Content(role="user", parts=[types.Part(text=user_queries)])

        # Stream agent response and collect final response
        final_response_text = ""
        async for event in runner_instance.run_async(
            user_id=user_id, session_id=session.id, new_message=query_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    final_response_text = text
                    print(f"Model: > {text}")
        
        return final_response_text if final_response_text else "No response generated"
        
    except Exception as e:
        print(f"Error in run_session: {e}")
        raise
    finally:
        # Give asyncio time to clean up connections
        await asyncio.sleep(0.1)