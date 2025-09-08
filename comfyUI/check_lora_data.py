import glob
from safetensors.torch import safe_open

# Prompt user for wildcard pattern
user_input = input("Enter wildcard pattern for LoRA files (e.g., *.safetensors or tsubasa*.safetensors): ").strip()
pattern = f"models/loras/{user_input}"

# Find matching files
lora_files = glob.glob(pattern)

if not lora_files:
    print("No matching LoRA files found.")
else:
    if len(lora_files) > 1:
        print("\nMultiple LoRA files found:")
        for idx, path in enumerate(lora_files):
            print(f"{idx + 1}. {path}")

        selection = input("\nEnter the number of the LoRA to view (leave blank to view all): ").strip()

        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(lora_files):
                lora_files = [lora_files[index]]
            else:
                print("Invalid selection. Showing all metadata.")
        elif selection != "":
            print("Invalid input. Showing all metadata.")

    for file_path in lora_files:
        print(f"\n--- Metadata for: {file_path} ---")
        try:
            with safe_open(file_path, framework="pt") as f:
                metadata = f.metadata()
                if metadata:
                    for key, value in metadata.items():
                        print(f"{key}: {value}")
                else:
                    print("No metadata found.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

