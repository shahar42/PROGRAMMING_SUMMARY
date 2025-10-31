#!/usr/bin/env python3
"""
C++ Instructor CLI - Simple version for merged models
No LoRA, no Unsloth - just standard transformers
"""

import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def ask_question(model, tokenizer, question):
    """Ask the model a question"""
    messages = [
        {
            "role": "system",
            "content": "You are an expert programming instructor specializing in C and C++. You provide clear, detailed explanations with practical examples from authoritative sources like K&R C, C++ Primer, and Computer Systems: A Programmer's Perspective."
        },
        {
            "role": "user",
            "content": question
        }
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt, return_tensors="pt")

    print("🤔 Thinking...", end="", flush=True)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.15,
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "<|start_header_id|>assistant<|end_header_id|>" in response:
        response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()

    return response

def interactive_mode(model, tokenizer):
    """Interactive chat"""
    print("\n" + "="*70)
    print("🎓 C++ Programming Instructor (Offline)")
    print("="*70)
    print("\nType 'exit' to quit, 'help' for help")
    print("="*70 + "\n")

    while True:
        try:
            question = input("\n💬 You: ").strip()

            if not question:
                continue

            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            if question.lower() == 'help':
                print("\nAsk any C++ programming question!")
                print("Examples: 'Explain pointers', 'What is RAII?'")
                continue

            print("\n🤖 Instructor:")
            answer = ask_question(model, tokenizer, question)
            print(answer)
            print("\n" + "-"*70)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

def main():
    parser = argparse.ArgumentParser(description="C++ Instructor CLI")
    parser.add_argument('--model', '-m', required=True, help='Path to merged model')
    parser.add_argument('--question', '-q', help='Single question (non-interactive)')

    args = parser.parse_args()

    print("Loading model... (this takes 2-5 minutes on CPU)")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )

    print("✅ Model loaded!")
    print("⚠️  CPU inference: 30-60 seconds per response\n")

    if args.question:
        answer = ask_question(model, tokenizer, args.question)
        print(f"\n🤖 Answer:\n{answer}\n")
    else:
        interactive_mode(model, tokenizer)

if __name__ == "__main__":
    main()
