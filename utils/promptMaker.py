import json
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

outputNum = 20

def getIdentity(identityPath):  
    with open(identityPath, "r", encoding="utf-8") as f:
        identityContext = f.read()
    return {"role": "user", "content": identityContext}
    
    
def get_message_length(msg):
    return sum(len(part.get("text", "")) for part in msg["parts"])
    
# def getPrompt():
#     total_len = 0
#     prompt = []
#     prompt.append(getIdentity("characterConfig/Pina/identity.txt"))
#     prompt.append({"role": "system", "content": f"Below is conversation history.\n"})

    # Prompt maker using OpenAI
    # with open("conversation.json", "r", encoding="utf-8") as f:
    #     data = json.load(f)
    # history = data["history"]
    # for message in history[:-1]:
    #     prompt.append(message)

    # prompt.append(
    #     {
    #         "role": "system",
    #         "content": f"Here is the latest conversation.\n*Make sure your response is within {outputNum} characters!\n",
    #     }
    # )

    # prompt.append(converted_history[-1])

    # prompt.append(history[-1])

    # total_len = sum(len(d['content']) for d in prompt)
    
    # while total_len > 4000:
    #     try:
    #         # print(total_len)
    #         # print(len(prompt))
    #         prompt.pop(2)
    #         total_len = sum(len(d['content']) for d in prompt)
    #     except:
    #         print("Error: Prompt too long!")

    # # total_characters = sum(len(d['content']) for d in prompt)
    # # print(f"Total characters: {total_characters}")

    # return prompt

def getPrompt(outputNum=500):
    with open("conversation.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    # ✅ Convert every message to Gemini format
    converted_history = [
        {
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]  # 👈 each part is a dict
        }
        for msg in history
    ]

    if not converted_history:
        # fallback if conversation.json is empty
        return [
            {"role": "user", "parts": [{"text": "Hello!"}]}
        ]

    # ✅ Always include system instruction
    prompt = [
        {
            "role": "model",
            "parts": [{"text": f"Here is the latest conversation.\n*Make sure your response is within {outputNum} characters!*"}]
        }
    ]

    # ✅ Add conversation history
    prompt.extend(converted_history)
    
    total_len = sum(get_message_length(d) for d in prompt)

    while total_len > 4000:
        try:
            prompt.pop(2)
            total_len = sum(get_message_length(d) for d in prompt)
        except:
            print("Error: Prompt too long!")

    return prompt
    
if __name__ == "__main__":
    prompt = getPrompt()
    print(prompt)
    print(len(prompt))