import subprocess
import difflib


def list_local_ollama_models():
    """Return a list of available local Ollama model names."""
    try:
        output = subprocess.check_output(['ollama', 'list'], text=True)
        lines = output.strip().split('\n')[1:]  # Skip header
        models = [line.split()[0] for line in lines if line]
        return models
    except Exception as e:
        return []


def validate_ollama_model(model_name):
    """
    Validate if the model_name exists locally. If not, suggest closest match.
    Returns (is_valid, valid_model_name, suggestions)
    """
    models = list_local_ollama_models()
    if model_name in models:
        return True, model_name, []
    # Try fuzzy match
    suggestions = difflib.get_close_matches(model_name, models, n=3, cutoff=0.6)
    if suggestions:
        return False, suggestions[0], suggestions
    # Try matching by base name (e.g., 'mistral' for 'mistral:3.2')
    base = model_name.split(':')[0]
    base_matches = [m for m in models if m.startswith(base)]
    if base_matches:
        return False, base_matches[0], base_matches
    return False, None, models


def print_model_validation_result(model_name):
    is_valid, valid_model, suggestions = validate_ollama_model(model_name)
    if is_valid:
        print(f"Model '{model_name}' is available locally.")
    elif valid_model:
        print(f"Model '{model_name}' not found. Did you mean '{valid_model}'?")
        print(f"Suggestions: {suggestions}")
    else:
        print(f"Model '{model_name}' not found. Available models: {suggestions}") 