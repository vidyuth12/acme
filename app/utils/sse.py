import json
from flask import Response

class SSEHelper:
    
    @staticmethod
    def format_sse(data: dict, event: str = None) -> str:
        message = f"data: {json.dumps(data)}\n\n"
        if event:
            message = f"event: {event}\n{message}"
        return message
    
    @staticmethod
    def create_stream(generator):
        return Response(
            generator,
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
