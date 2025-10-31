#!/usr/bin/env python3
"""
C++ Programming Instructor CLI (LoRA version)
For models trained with LoRA/QLoRA adapters
"""

import sys
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

class CPPInstructor:
    def __init__(self, base_model_path, adapter_path, max_tokens=512):
        """Initialize the model with LoRA adapter"""
        print("Loading base model... (this may take a few minutes)")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(adapter_path)

        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map="cpu",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )

        print("Loading LoRA adapter...")
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(self.model, adapter_path)

        # Merge adapter for faster inference
        print("Merging adapter with base model...")
        self.model = self.model.merge_and_unload()

        self.max_tokens = max_tokens
        self.system_prompt = """You are an expert programming instructor specializing in C and C++. You provide clear, detailed explanations with practical examples from authoritative sources like K&R C, C++ Primer, and Computer Systems: A Programmer's Perspective."""

        print("✅ Model loaded successfully!")
        print("⚠️  Note: CPU inference is slow. First response will take 30-60 seconds.\n")

    def ask(self, question):
        """Ask the model a question"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question}
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt")

        print("🤔 Thinking...", end="", flush=True)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            do_sample=False,
            repetition_penalty=1.15,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()

        return response

    def interactive_mode(self):
        """Start interactive chat mode"""
        print("="*70)
        print("🎓 C++ Programming Instructor CLI (Offline Mode)")
        print("="*70)
        print("\nType your C++ questions. Commands:")
        print("  - 'exit' or 'quit' to exit")
        print("  - 'help' for help")
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
                    self.show_help()
                    continue

                print("\n🤖 Instructor: ", end="", flush=True)
                response = self.ask(question)
                print(response)
                print("\n" + "-"*70)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    def show_help(self):
        """Show help message"""
        print("\n" + "="*70)
        print("📖 HELP")
        print("="*70)
        print("""
This CLI provides an offline C++ programming instructor.

Example questions:
  - "Explain smart pointers in C++"
  - "What is RAII?"
  - "Show me an example of templates"

Commands:
  - exit, quit, q  : Exit the program
  - help           : Show this help message

Note: Responses take 30-60 seconds on CPU (this is normal).
        """)
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="C++ Programming Instructor CLI (LoRA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cpp_instructor_cli_lora.py \\
    --base-model ~/models/llama-3.1-8b \\
    --adapter ~/models/checkpoint-4698

  # Single question
  python cpp_instructor_cli_lora.py \\
    --base-model ~/models/llama-3.1-8b \\
    --adapter ~/models/checkpoint-4698 \\
    --question "Explain pointers"
        """
    )

    parser.add_argument(
        '--base-model', '-b',
        type=str,
        required=True,
        help='Path to base Llama 3.1 8B model'
    )

    parser.add_argument(
        '--adapter', '-a',
        type=str,
        required=True,
        help='Path to your fine-tuned adapter (checkpoint-4698)'
    )

    parser.add_argument(
        '--question', '-q',
        type=str,
        help='Single question to ask (non-interactive mode)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=512,
        help='Maximum tokens to generate (default: 512)'
    )

    args = parser.parse_args()

    # Initialize instructor
    instructor = CPPInstructor(args.base_model, args.adapter, args.max_tokens)

    # Single question or interactive
    if args.question:
        print(f"\n💬 Question: {args.question}\n")
        print("="*70)
        response = instructor.ask(args.question)
        print(f"\n🤖 Answer:\n{response}\n")
        print("="*70 + "\n")
    else:
        instructor.interactive_mode()


if __name__ == "__main__":
    main()
