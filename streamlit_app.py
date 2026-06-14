import os

# This is a simple wrapper to keep Streamlit Cloud working seamlessly.
# It points Streamlit to the actual dashboard file inside the package.

if __name__ == "__main__":
    dashboard_path = os.path.join(os.path.dirname(__file__), "github_traffic", "dashboard.py")
    os.system(f"streamlit run \"{dashboard_path}\"")
