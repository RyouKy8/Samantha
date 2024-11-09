from subprocess import run

result = run(
    ["python", "-c", "import sys; print(sys.executable)"],
    capture_output=True,
    text=True,
)
print(result.stdout)
