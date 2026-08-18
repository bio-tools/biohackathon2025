"""
Auto-generates Pydantic models for the bio.tools schema from the JSON schema at
https://raw.githubusercontent.com/bio-tools/biotoolsSchema/refs/heads/main/jsonschema/biotoolsj.json.

Previously:
https://raw.githubusercontent.com/bio-tools/biotoolsSchema/refs/heads/v4-dev/biotools.schema.json.

Run via:
    poetry run gen-biotools-models
"""

import json
import re
import urllib.request
from pathlib import Path

from datamodel_code_generator import DataModelType, InputFileType, generate


def download_schema(download_from: str, save_to: Path):
    """Download the JSON schema from the specified URL."""
    print(f"Downloading schema from {download_from}")
    save_to.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(download_from, save_to)
    print(f"Saved schema to {save_to}")


def extract_tool_definition(schema_path: Path, extracted_path: Path):
    """Extract the root 'tool' definition from the full JSON schema."""
    print("Extracting root object from definitions")
    raw_schema = json.loads(schema_path.read_text())
    extracted = {
        "$schema": raw_schema.get("$schema", "http://json-schema.org/draft-04/schema#"),
        "title": "Tool",
        "type": "object",
        "$ref": "#/definitions/tool",
        "definitions": raw_schema.get("definitions", {}),
    }
    extracted_path.write_text(json.dumps(extracted, indent=2))
    print(f"Extracted root to {extracted_path}")


def generate_models(schema_path: Path, output_file: Path):
    """Generate Pydantic models from the extracted JSON schema."""
    print(f"Generating Pydantic models into {output_file}")
    if output_file.exists():
        output_file.unlink()

    kwargs = {
        "input_": schema_path,
        "input_file_type": InputFileType.JsonSchema,
        "output": output_file,
        "output_model_type": DataModelType.PydanticV2BaseModel,
        "reuse_model": True,
    }

    generate(**kwargs)

    print("Model generation complete.")


def add_docstring(docstring: str, output_file: Path):
    """Prepend a docstring to the generated models file."""
    content = output_file.read_text()

    # prepend only if the file doesn't already contain the docstring
    if not content.lstrip().startswith('"""Auto-generated'):
        output_file.write_text(docstring + "\n" + content)

    print("Docstring prepended.")


def relax_extra_field_validation(output_file: Path):
    """Allow extra fields in generated Pydantic models by patching model_config."""
    content = output_file.read_text()

    # handle both quoting styles
    content = re.sub(r"ConfigDict\(\s*extra=['\"]forbid['\"]\s*\)", "ConfigDict(extra='ignore')", content)
    content = re.sub(r"extra\s*=\s*['\"]forbid['\"]", "extra='ignore'", content)

    output_file.write_text(content)
    print(f"Relaxed Pydantic model config in {output_file.name} to extra='ignore'.")


def patch_publication_type_enum(output_file: Path):
    """
    Add 'Preprint' as an allowed publication type.

    Workaround: the bio.tools API returns 'Preprint' as a publication type
    for some entries, but the official JSON schema does not list it as a
    valid value. Without this patch, entries with a preprint publication
    fail Pydantic validation. Remove this patch once the upstream schema
    is fixed to include 'Preprint':
    https://github.com/bio-tools/biotoolsSchema
    """
    content = output_file.read_text()

    # match the generated enum by its known members rather than its class
    # name, since datamodel-code-generator may rename it (e.g. TypeEnum2 ->
    # TypeEnum3) if the upstream schema's definition order changes. The
    # quote character is also captured rather than hard-coded, since it
    # varies across datamodel-code-generator versions/configs.
    pattern = re.compile(
        r"(class \w+\(Enum\):\n"
        r"    Primary = (['\"])Primary\2\n"
        r"    Benchmarking_study = \2Benchmarking study\2\n"
        r"    Method = \2Method\2\n"
        r"    Usage = \2Usage\2\n)"
        r"(    Review = \2Review\2\n)"
    )

    new_content, count = pattern.subn(r"\1    Preprint = \2Preprint\2\n\3", content)
    if count != 1:
        raise RuntimeError(
            "Could not locate the publication type enum to patch with 'Preprint' "
            "(expected exactly one match, found "
            f"{count}). The generated model shape may have changed — update "
            "patch_publication_type_enum() in scripts/gen_models.py accordingly."
        )

    output_file.write_text(new_content)
    print(f"Patched publication type enum in {output_file.name} to include 'Preprint'.")


def generate_biotools_models():
    """Generate bio.tools Pydantic models."""
    schema_url = "https://raw.githubusercontent.com/bio-tools/biotoolsSchema/refs/heads/main/jsonschema/biotoolsj.json"
    schema_path = Path("schemas/biotools.json")
    extracted_schema_path = Path("schemas/tool_root.json")
    filename = "biotools.py"
    output_file = Path("src/bridge/core/") / filename

    docstring = f'''"""
Auto-generated Pydantic models for the bio.tools schema.
Do not edit this file manually — it is generated by `scripts/gen_models.py`
from the JSON schema at {schema_url}.
"""\n'''

    download_schema(download_from=schema_url, save_to=schema_path)
    extract_tool_definition(schema_path=schema_path, extracted_path=extracted_schema_path)
    generate_models(schema_path=extracted_schema_path, output_file=output_file)
    add_docstring(docstring=docstring, output_file=output_file)
    relax_extra_field_validation(output_file=output_file)
    patch_publication_type_enum(output_file=output_file)


def generate_github_models():
    """Generate GitHub Pydantic models."""
    schema_path = Path("schemas/github_repo.json")
    filename = "github_repo.py"
    output_file = Path("src/bridge/core/") / filename

    docstring = f'''"""
Auto-generated Pydantic models for the GitHub repository schema.
Do not edit this file manually — it is generated by `scripts/gen_models.py`
from the JSON schema at {schema_path}.
"""\n'''

    generate_models(schema_path=schema_path, output_file=output_file)
    add_docstring(docstring=docstring, output_file=output_file)
    relax_extra_field_validation(output_file=output_file)

    schema_path = Path("schemas/github_latest_release.json")
    filename = "github_latest_release.py"
    output_file = Path("src/bridge/core/") / filename

    docstring = f'''"""
Auto-generated Pydantic models for the GitHub latest release schema.
Do not edit this file manually — it is generated by `scripts/gen_models.py`
from the JSON schema at {schema_path}.
"""\n'''

    generate_models(schema_path=schema_path, output_file=output_file)
    add_docstring(docstring=docstring, output_file=output_file)
    relax_extra_field_validation(output_file=output_file)

    schema_path = Path("schemas/github_languages.json")
    filename = "github_languages.py"
    output_file = Path("src/bridge/core/") / filename

    docstring = f'''"""
Auto-generated Pydantic models for the GitHub languages schema.
Do not edit this file manually — it is generated by `scripts/gen_models.py`
from the JSON schema at {schema_path}.
"""\n'''

    generate_models(schema_path=schema_path, output_file=output_file)
    add_docstring(docstring=docstring, output_file=output_file)
    relax_extra_field_validation(output_file=output_file)
