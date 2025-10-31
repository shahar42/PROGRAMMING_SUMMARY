#!/usr/bin/env python3
"""
POSIX to Programming Concepts Converter
Converts POSIX manpage JSON files to programming concepts format for integration
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import hashlib
from datetime import datetime

class PosixToConceptsConverter:
    def __init__(self, posix_dir: str, output_dir: str):
        self.posix_dir = Path(posix_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def convert_syscall_to_concept(self, syscall_data: Dict) -> Dict:
        """Convert a POSIX syscall JSON to programming concept format"""

        name = syscall_data.get('name', 'unknown')
        description = syscall_data.get('description', '')
        synopsis = syscall_data.get('synopsis', [])
        parameters = syscall_data.get('parameters', [])
        examples = syscall_data.get('examples', [])
        errors = syscall_data.get('errors', [])
        related_calls = syscall_data.get('related_calls', [])

        # Create topic name
        topic = f"{name}() System Call"

        # Build comprehensive explanation
        explanation_parts = [description]

        # Add parameter details
        if parameters:
            explanation_parts.append("\n**Parameters:**")
            for param in parameters:
                param_name = param.get('name', '')
                param_type = param.get('type', '')
                param_desc = param.get('description', '')
                explanation_parts.append(f"- `{param_name}` ({param_type}): {param_desc}")

        # Add error information
        if errors:
            explanation_parts.append("\n**Common Errors:**")
            for error in errors[:5]:  # Limit to first 5 errors
                error_code = error.get('code', '')
                error_desc = error.get('description', '')
                explanation_parts.append(f"- `{error_code}`: {error_desc}")

        # Add related calls
        if related_calls:
            related_str = ", ".join([f"`{call}()`" for call in related_calls[:8]])
            explanation_parts.append(f"\n**Related System Calls:** {related_str}")

        explanation = "\n".join(explanation_parts)

        # Create syntax from synopsis
        syntax = ""
        if synopsis:
            # Find the main function declaration
            for line in synopsis:
                if name in line and '(' in line:
                    syntax = line.strip()
                    break
            if not syntax and synopsis:
                syntax = synopsis[0].strip()

        # Create code example
        code_example = []
        if examples:
            code_example = examples if isinstance(examples, list) else [examples]
        else:
            # Generate a basic example
            code_example = [
                f"#include <unistd.h>  // or appropriate header",
                f"",
                f"int result = {name}(...);  // Call the system call",
                f"if (result == -1) {{",
                f"    perror(\"{name}\");",
                f"    exit(EXIT_FAILURE);",
                f"}}"
            ]

        # Create example explanation
        example_explanation = f"This example demonstrates the basic usage of the {name}() system call. "
        if parameters:
            example_explanation += f"The function takes {len(parameters)} parameter(s) and "
        example_explanation += "returns 0 on success or -1 on error with errno set appropriately."

        # Generate unique ID
        content_for_id = f"{name}_{description[:50]}"
        concept_id = hashlib.md5(content_for_id.encode()).hexdigest()[:6]

        # Build concept
        concept = {
            "topic": topic,
            "explanation": explanation,
            "syntax": syntax,
            "code_example": code_example,
            "example_explanation": example_explanation,
            "extraction_metadata": {
                "source": "POSIX System Call Manual",
                "extraction_date": datetime.now().isoformat(),
                "syscall_name": name,
                "converted_from": "posix_manpage",
                "original_file": f"unix_{name}.json",
                "concept_id": f"posix_sys_{name}_{concept_id}"
            }
        }

        return concept

    def convert_all_syscalls(self):
        """Convert all POSIX syscalls to programming concepts"""

        unix_files = list(self.posix_dir.glob("unix_*.json"))
        converted_count = 0

        print(f"Found {len(unix_files)} POSIX syscall files to convert...")

        for unix_file in unix_files:
            try:
                with open(unix_file, 'r') as f:
                    syscall_data = json.load(f)

                concept = self.convert_syscall_to_concept(syscall_data)

                # Create output filename
                syscall_name = syscall_data.get('name', 'unknown')
                concept_id = concept['extraction_metadata']['concept_id']
                output_file = self.output_dir / f"{concept_id}.json"

                # Save converted concept
                with open(output_file, 'w') as f:
                    json.dump(concept, f, indent=2)

                converted_count += 1

                if converted_count % 50 == 0:
                    print(f"Converted {converted_count} syscalls...")

            except Exception as e:
                print(f"Error converting {unix_file}: {e}")
                continue

        print(f"✅ Successfully converted {converted_count} POSIX syscalls to programming concepts")
        return converted_count

def main():
    # Paths
    posix_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/posix_manpages"
    output_dir = "/home/shahar42/Suumerizing_C_holy_grale_book/outputs/posix_manpages_concepts"

    # Convert
    converter = PosixToConceptsConverter(posix_dir, output_dir)
    converted_count = converter.convert_all_syscalls()

    print(f"\nConversion complete! {converted_count} concepts created in {output_dir}")

if __name__ == "__main__":
    main()