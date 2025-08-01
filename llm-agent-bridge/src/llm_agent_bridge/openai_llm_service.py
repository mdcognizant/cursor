from openai import OpenAI
import grpc
from concurrent import futures
import os

# Import the generated proto files (now in the same directory)
import agent_service_pb2
import agent_service_pb2_grpc

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY_HERE"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class OpenAIAgentService(agent_service_pb2_grpc.AgentCommunicationServiceServicer):
    def SendMessage(self, request, context):
        prompt = request.message.content
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            llm_reply = response.choices[0].message.content
            return agent_service_pb2.SendMessageResponse(
                message_id="openai-llm-1",
                response=agent_service_pb2.Message(
                    id="llm-msg-1",
                    content=llm_reply,
                    type=agent_service_pb2.MessageType.MESSAGE_TYPE_TEXT,
                    format="text"
                ),
                status=agent_service_pb2.MessageStatus.MESSAGE_STATUS_COMPLETED
            )
        except Exception as e:
            return agent_service_pb2.SendMessageResponse(
                message_id="openai-llm-err",
                response=agent_service_pb2.Message(
                    id="llm-msg-err",
                    content=f"OpenAI API error: {str(e)}",
                    type=agent_service_pb2.MessageType.MESSAGE_TYPE_ERROR,
                    format="text"
                ),
                status=agent_service_pb2.MessageStatus.MESSAGE_STATUS_FAILED
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_service_pb2_grpc.add_AgentCommunicationServiceServicer_to_server(OpenAIAgentService(), server)
    server.add_insecure_port('[::]:50051')
    print("[OpenAI LLM gRPC] Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve() 