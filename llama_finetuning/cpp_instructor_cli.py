#!/usr/bin/env python3
"""
C++ Programming Instructor CLI
Interactive command-line interface for your fine-tuned Llama 3.1 8B model
"""

import sys
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class CPPInstructor:
    def __init__(self, model_path, max_tokens=512):
        """Initialize the model"""
        print("Loading model... (this may take a minute)")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.float16,
        )

        self.max_tokens = max_tokens
        self.system_prompt = """You are an expert programming instructor specializing in C and C++. You provide clear, detailed explanations with practical examples from authoritative sources like K&R C, C++ Primer, and Computer Systems: A Programmer's Perspective."""

        print("✅ Model loaded successfully!\n")

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

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            do_sample=False,
            repetition_penalty=1.15,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract assistant response
        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()

        return response

    def interactive_mode(self):
        """Start interactive chat mode"""
        print("="*70)
        print("🎓 C++ Programming Instructor CLI")
        print("="*70)
        print("\nType your C++ questions. Commands:")
        print("  - 'exit' or 'quit' to exit")
        print("  - 'help' for help")
        print("  - 'clear' to clear screen")
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

                if question.lower() == 'clear':
                    print("\033[H\033[J")  # Clear screen
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
This CLI provides an interactive C++ programming instructor powered by
your fine-tuned Llama 3.1 8B model.

Example questions:
  - "Explain smart pointers in C++"
  - "What is RAII?"
  - "Show me an example of templates"
  - "What's the difference between stack and heap?"
  - "How do virtual functions work?"

Commands:
  - exit, quit, q  : Exit the program
  - help           : Show this help message
  - clear          : Clear the screen

Tips:
  - Be specific in your questions
  - Ask for examples if you want code
  - Follow up with clarifying questions
        """)
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="C++ Programming Instructor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cpp_instructor_cli.py --model /path/to/model

  # Single question
  python cpp_instructor_cli.py --model /path/to/model --question "Explain pointers"

  # Longer responses
  python cpp_instructor_cli.py --model /path/to/model --max-tokens 800
        """
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        required=True,
        help='Path to the fine-tuned model directory'
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
        help='Maximum number of tokens to generate (default: 512)'
    )

    args = parser.parse_args()

    # Initialize instructor
    instructor = CPPInstructor(args.model, args.max_tokens)

    # Single question mode or interactive mode
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
