import os
import shutil
import git
from directory_tree import DisplayTree


def clone_repo(repo_url: str, clone_dir: str = "temp_repo") -> str:
    if os.path.exists(clone_dir):   
        shutil.rmtree(clone_dir)
    git.Repo.clone_from(repo_url, clone_dir)
    return clone_dir


def get_project_tree(path: str) -> str:
    return DisplayTree(path, stringRep=True)


def get_all_code_files(root: str, extensions=(".py", ".cpp", ".java", ".js", ".ts", ".ipynb", ".c", ".cs", ".html", ".css")) -> list[dict]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(extensions):
                filepath = os.path.join(dirpath, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        code = file.read()
                    rel_path = os.path.relpath(filepath, root)
                    files.append({"filename": rel_path, "content": code})
                except Exception as e:
                    print(f"Skipping {f}: {e}")
    return files

