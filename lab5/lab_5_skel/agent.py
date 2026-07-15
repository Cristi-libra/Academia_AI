"""Core agent orchestration.
The agent coordinates communication between
the conversation context and the language model."""


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}

    def _handle_tool_calls(self, tool_calls):
        results = []
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            arguments = tc["function"]["arguments"]
            tool_id = tc["id"]

            tool = self.tools.get(tool_name)
            if tool:
                result = tool.callback(**arguments)
            else:
                result = f"Tool '{tool_name}' not found"

            results.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": str(result)
            })
        return results

    def process_message(self, user_message):
        self.context.add_message({
            "role": "user",
            "content": user_message
        })

        response = self.llm_client.generate_response(
            self.context.get_history(),
            tools=list(self.tools.values())
        )

        message = response["message"]
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            self.context.add_message(message)

            tool_results = self._handle_tool_calls(tool_calls)
            for result in tool_results:
                self.context.add_message(result)

            response = self.llm_client.generate_response(
                self.context.get_history()
            )
            message = response["message"]

        self.context.add_message(message)
        return message.get("content", "")
