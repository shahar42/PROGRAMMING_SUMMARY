#!/usr/bin/env python3
"""
CLI chat interface for your fine-tuned Llama model
Usage: python chat_cli.py
"""

from unsloth import FastLanguageModel
import torch

def load_model(model_path="./final_model"):
    """Load your fine-tuned model"""
    print("🔄 Loading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    print("✅ Model loaded!\n")
    return model, tokenizer

def chat(model, tokenizer, question, system_prompt=None):
    """Ask the model a question"""
    if system_prompt is None:
        system_prompt = "You are an expert programming instructor specializing in C and C++."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")

    outputs = model.generate(
        input_ids=inputs,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract assistant response
    response = response.split("assistant")[-1].strip()
    return response

def main():
    """Interactive CLI chat"""
    print("=" * 60)
    print("  C/C++ Programming Instructor - Fine-tuned Llama 3.1 8B")
    print("=" * 60)

    # Load model (change path if needed)
    model, tokenizer = load_model("/content/drive/MyDrive/llama_finetuning/final_model")

    print("Commands:")
    print("  - Type your question and press Enter")
    print("  - Type 'exit' or 'quit' to exit")
    print("  - Type 'clear' to start new conversation\n")

    while True:
        try:
            question = input("\n🤔 You: ").strip()

            if not question:
                continue

            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break

            if question.lower() == 'clear':
                print("\n🔄 Conversation cleared\n")
                continue

            print("\n💬 Assistant: ", end="", flush=True)
            response = chat(model, tokenizer, question)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
