import importlib.util
import sys

required_packages = [
    'streamlit',
    'pandas',
    'plotly',
    'ccxt',
    'numpy',
    'websockets',
    'pycoingecko',
    'sklearn',
    'scipy',
    'seaborn'
]

def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"[MISSING] {package_name}")
        return False
    else:
        print(f"[OK] {package_name}")
        return True

def main():
    missing_packages = []
    print("Checking required packages...")
    for package in required_packages:
        if not check_package(package):
            missing_packages.append(package)
    
    if missing_packages:
        print("\nMissing packages:")
        print("Run this command to install them:")
        print(f"pip install {' '.join(missing_packages)}")
    else:
        print("\nAll required packages are installed!")

if __name__ == "__main__":
    main()
