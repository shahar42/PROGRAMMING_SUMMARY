#!/usr/bin/env python3
"""
C++ Programming Instructor CLI (Quantized version)
Optimized for systems with limited RAM (14GB)
Uses 4-bit quantization to reduce memory usage from ~30GB to <10GB
"""

import sys
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

class CPPInstructor:
    def __init__(self, model_path, max_tokens=512, use_4bit=True):
        """Initialize the model with 4-bit quantization"""
        print("🔧 Initializing C++ Instructor...")
        print(f"📊 Available RAM: {torch.cuda.is_available() and 'GPU' or 'CPU only'}")

        # Load tokenizer first (small, fast)
        print("📝 Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        if use_4bit:
            print("🗜️  Loading model with 4-bit quantization (memory efficient)...")
            print("   This will take 2-5 minutes from external drive...")

            # Configure 4-bit quantization
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

            # Load model with quantization
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
        else:
            print("⚠️  Loading model in float16 (uses more memory)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )

        self.max_tokens = max_tokens
        self.system_prompt = """You are an expert programming instructor specializing in C and C++. You provide clear, detailed explanations with practical examples from authoritative sources like K&R C, C++ Primer, and Computer Systems: A Programmer's Perspective."""

        print("✅ Model loaded successfully!")
        print(f"💾 Memory usage: ~{self._estimate_memory()}GB")
        print()

    def _estimate_memory(self):
        """Estimate current memory usage"""
        import psutil
        process = psutil.Process()
        return round(process.memory_info().rss / 1024**3, 1)

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

        print("🤔 Thinking...", end="", flush=True)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract assistant response
        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()

        print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
        return response

    def interactive_mode(self):
        """Start interactive chat mode"""
        print("="*70)
        print("🎓 C++ Programming Instructor CLI (Quantized)")
        print("="*70)
        print("\nType your C++ questions. Commands:")
        print("  - 'exit' or 'quit' to exit")
        print("  - 'help' for help")
        print("  - 'memory' to check memory usage")
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

                if question.lower() == 'memory':
                    print(f"\n💾 Current memory usage: ~{self._estimate_memory()}GB\n")
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
                import traceback
                traceback.print_exc()

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
  - "What's the difference between stack and heap?"

Commands:
  - exit, quit, q  : Exit the program
  - help           : Show this help message
  - memory         : Check current memory usage

Note: First response may take 30-60 seconds (model warmup).
        """)
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="C++ Programming Instructor CLI (Quantized)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python cpp_instructor_quantized.py

  # Single question
  python cpp_instructor_quantized.py --question "Explain pointers"

  # Use 8-bit instead of 4-bit (slightly better quality, more memory)
  python cpp_instructor_quantized.py --no-4bit

  # Custom model path
  python cpp_instructor_quantized.py --model /path/to/model
        """
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='/mnt/external/models/cpp-instructor',
        help='Path to fine-tuned model (default: /mnt/external/models/cpp-instructor)'
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

    parser.add_argument(
        '--no-4bit',
        action='store_true',
        help='Disable 4-bit quantization (uses more memory)'
    )

    args = parser.parse_args()

    # Initialize instructor
    try:
        instructor = CPPInstructor(
            args.model,
            args.max_tokens,
            use_4bit=not args.no_4bit
        )
    except Exception as e:
        print(f"\n❌ Failed to load model: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure external drive is mounted: ls /mnt/external/models/")
        print("  2. Check model path exists: ls /mnt/external/models/cpp-instructor/")
        print("  3. Verify you have ~10GB free RAM: free -h")
        sys.exit(1)

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
