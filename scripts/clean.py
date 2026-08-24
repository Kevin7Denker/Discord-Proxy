import shutil
from pathlib import Path

def clean() -> None:
    root = Path(__file__).resolve().parent.parent
    dirs_to_remove = ["dist", "build", "__pycache__"]
    
    for d in dirs_to_remove:
        path = root / d
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"Removed {d}/")
            
    for p in root.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
        print(f"Removed {p}")
        
    for p in root.glob("*.spec"):
        p.unlink(missing_ok=True)
        print(f"Removed {p}")

    print("Clean complete!")

if __name__ == "__main__":
    clean()
