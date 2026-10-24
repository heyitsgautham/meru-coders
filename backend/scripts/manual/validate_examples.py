import json

# Validate the examples.json file
with open('backend/data/examples.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("✓ Valid JSON file")
print(f"✓ Total meter categories: {len(data)}")

if "दण्डक" in data:
    dandaka = data["दण्डक"]
    print(f"✓ Dandaka section found")
    print(f"  Description: {dandaka['description']}")
    print(f"  Total sub-categories: {len(dandaka['categories'])}")
    
    for category_name, category_data in dandaka['categories'].items():
        example_count = len(category_data['examples'])
        print(f"\n  {category_name}:")
        print(f"    Description: {category_data['description']}")
        print(f"    Examples: {example_count}")
        if example_count > 0:
            print(f"    First example length: {len(category_data['examples'][0])} chars")
else:
    print("✗ Dandaka section NOT found!")
