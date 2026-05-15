"""
Praxis command-line interface.

Provides two subcommands:
- analyze: Detect stack from an existing project directory
- plan: Bootstrap from a planning document (Phase 2+)
"""

import argparse
import sys
from pathlib import Path


def analyze_command(args: argparse.Namespace) -> int:
    """
    Handle the 'analyze' subcommand.
    
    Detects the stack from an existing project directory and generates
    tailored Bob IDE configuration files.
    
    Args:
        args: Parsed command-line arguments containing 'path'
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Late imports to avoid loading Granite/env on --help
    from praxis.detect import detect_stack
    from praxis.generate import generate_outputs, _stack_info_to_context
    
    project_path = Path(args.path).resolve()
    
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}", file=sys.stderr)
        return 1
    
    if not project_path.is_dir():
        print(f"Error: Path is not a directory: {project_path}", file=sys.stderr)
        return 1
    
    print(f"Analyzing project at: {project_path}")
    
    try:
        stack_info = detect_stack(project_path)
        print(f"Detected stack: {stack_info.stack_name}")
        if stack_info.frameworks:
            print(f"Frameworks: {', '.join(stack_info.frameworks)}")
        
        print("Generating Bob configuration (this may take 30-60 seconds)...")
        context = _stack_info_to_context(stack_info, project_path)
        output_paths = generate_outputs(project_path, context)
        
        print(f"\nGenerated {len(output_paths)} files in {project_path / 'praxis_output'}:")
        for path in output_paths:
            print(f"  - {path.name}")
        
        return 0
    except NotImplementedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        return 1


def plan_command(args: argparse.Namespace) -> int:
    """
    Handle the 'plan' subcommand.
    
    Parses a planning document and generates Bob IDE configuration for the
    described project.
    
    Args:
        args: Parsed command-line arguments containing 'path'
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Late imports
    from praxis.plan import parse_planning_doc
    from praxis.generate import generate_outputs, _plan_info_to_context
    
    doc_path = Path(args.path).resolve()
    
    if not doc_path.exists():
        print(f"Error: Planning document does not exist: {doc_path}", file=sys.stderr)
        return 1
    
    if not doc_path.is_file():
        print(f"Error: Path is not a file: {doc_path}", file=sys.stderr)
        return 1
    
    print(f"Reading planning document: {doc_path}")
    print("Calling Granite to extract project intent...")
    
    try:
        plan_info = parse_planning_doc(doc_path)
        
        print(f"Inferred stack: {plan_info.inferred_stack}")
        if plan_info.inferred_frameworks:
            print(f"Frameworks: {', '.join(plan_info.inferred_frameworks)}")
        if plan_info.clarifying_questions:
            print(f"Open questions found: {len(plan_info.clarifying_questions)}")
        
        # Output goes in the doc's parent directory
        output_root = doc_path.parent
        context = _plan_info_to_context(plan_info, doc_path)
        
        print("Generating Bob configuration (this may take 30-60 seconds)...")
        output_paths = generate_outputs(output_root, context)
        
        print(f"\nGenerated {len(output_paths)} files in {output_root / 'praxis_output'}:")
        for path in output_paths:
            print(f"  - {path.name}")
        
        if plan_info.clarifying_questions:
            print(f"\n{len(plan_info.clarifying_questions)} clarifying questions surfaced in AGENTS.md")
            print("Bob will ask the developer about these at session start.")
        
        return 0
    except NotImplementedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error during planning: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for the Praxis CLI.
    
    Parses command-line arguments and dispatches to the appropriate subcommand.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        prog="praxis",
        description="A methodology transfer tool for IBM Bob IDE",
        epilog="For more information, see: https://github.com/ContraInfinito/bob-praxis",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )
    
    # 'analyze' subcommand
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze an existing project directory and generate Bob IDE configuration",
        description=(
            "Detects the technology stack from an existing project directory "
            "(Python, Unity, or generic) and generates tailored Bob IDE configuration "
            "files in <project>/praxis_output/."
        ),
    )
    analyze_parser.add_argument(
        "path",
        type=str,
        help="Path to the project directory to analyze",
    )
    analyze_parser.set_defaults(func=analyze_command)
    
    # 'plan' subcommand
    plan_parser = subparsers.add_parser(
        "plan",
        help="Bootstrap from a planning document (Phase 2+)",
        description=(
            "Interprets a planning document (markdown, text, or PDF) and generates "
            "Bob IDE configuration for a new project. This feature is not yet implemented."
        ),
    )
    plan_parser.add_argument(
        "path",
        type=str,
        help="Path to the planning document",
    )
    plan_parser.set_defaults(func=plan_command)
    
    # Parse arguments and dispatch
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

