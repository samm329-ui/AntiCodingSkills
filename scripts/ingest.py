import os
import zipfile
import json
import re

# We will look in the parent directory for all zips
SOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Ensure the resources folder exists
RESOURCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
os.makedirs(RESOURCES_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(RESOURCES_DIR, "module_index.json")

def peek_zip(filepath):
    """
    Open the zip temporarily and categorize the stack and important paths.
    Returns a dict characterizing the files inside.
    """
    info = {
        "filename": os.path.basename(filepath),
        "stack": [],
        "has_package_json": False,
        "has_requirements_txt": False,
        "is_nextjs": False,
        "is_vite": False,
        "is_react": False,
        "is_python": False,
        "app_router": False,
        "pages_router": False,
        "components": [],
        "features": [],
        "routes": []
    }
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            file_list = z.namelist()
            
            # Simple heuristic detection
            for f in file_list:
                fname = os.path.basename(f)
                norm_f = f.lower()
                
                if fname == "package.json":
                    info["has_package_json"] = True
                    try:
                        # Attempt to read package.json to analyze dependencies
                        data = z.read(f).decode('utf-8')
                        pkg = json.loads(data)
                        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                        if "next" in deps:
                            info["is_nextjs"] = True
                            info["stack"].append("nextjs")
                        if "vite" in deps:
                            info["is_vite"] = True
                            info["stack"].append("vite")
                        if "react" in deps:
                            info["is_react"] = True
                            info["stack"].append("react")
                        if "tailwindcss" in deps:
                            info["stack"].append("tailwind")
                    except Exception:
                        pass
                        
                elif fname == "requirements.txt" or fname == "pyproject.toml" or fname == "Pipfile":
                    info["has_requirements_txt"] = True
                    info["is_python"] = True
                    if "python" not in info["stack"]:
                        info["stack"].append("python")
                        
                # Look for Next.js routing patterns (app vs pages)
                if info["is_nextjs"] or "nextjs" in info["stack"]:
                    if "/app/" in norm_f and ("page.tsx" in norm_f or "layout.tsx" in norm_f or "page.js" in norm_f):
                        info["app_router"] = True
                    elif "/pages/" in norm_f and not "/api/" in norm_f:
                        info["pages_router"] = True
                        
                # Identify components/features directory
                if "/components/" in norm_f and (fname.endswith(".js") or fname.endswith(".jsx") or fname.endswith(".tsx") or fname.endswith(".ts") or fname.endswith(".vue") or fname.endswith(".svelte")):
                    if fname not in info["components"]:
                        info["components"].append(fname)
                if "/features/" in norm_f and (fname.endswith(".js") or fname.endswith(".jsx") or fname.endswith(".tsx") or fname.endswith(".ts")):
                    if fname not in info["features"]:
                        info["features"].append(fname)
                        
    except zipfile.BadZipFile:
        info["error"] = "Bad zip file"
    except Exception as e:
        info["error"] = str(e)
        
    return info


def main():
    print(f"Scanning directory: {SOURCE_DIR}")
    zip_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.zip')]
    print(f"Found {len(zip_files)} zip files.")
    
    index = []
    
    for zfile in zip_files:
        full_path = os.path.join(SOURCE_DIR, zfile)
        print(f"Analyzing {zfile}...")
        meta = peek_zip(full_path)
        
        # Deduplicate components/features lists to limit size, keep top 100 for brevity if huge
        meta["components"] = sorted(list(set(meta["components"])))[:100]
        meta["features"] = sorted(list(set(meta["features"])))[:100]
        
        index.append(meta)
        
    # Write output summary
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
        
    print(f"Successfully generated module index at: {OUTPUT_FILE}")
    print(f"Total structured ingested: {len(index)}")

if __name__ == "__main__":
    main()
