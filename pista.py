from huggingface_hub import InferenceClient

client = InferenceClient(api_key="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")
game = "Valorant"
messages = [
	{
		"role": "user",
        "content": f"Descripcion simple, muy corta y clara de {game} en español, para intentar adivinarlo, sin mencionar el nombre o nada relevante"
	}
]

completion = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2", 
	messages=messages, 
	max_tokens=50
)

#solo para ver el resultado
print(completion.choices[0].message['content'])

