{ lib, python312Packages }:

let
  runtimePython = python312Packages.python.withPackages (pythonPackages: [
    pythonPackages.jsonschema
    pythonPackages.pyyaml
  ]);
in
python312Packages.buildPythonPackage {
  pname = "modolia";
  version = "0.1.0";
  pyproject = true;
  src = ../.;

  build-system = [
    python312Packages.setuptools
    python312Packages.wheel
  ];

  postInstall = ''
    mkdir -p $out/bin
    cat > $out/bin/modolia <<EOF
    #!${runtimePython}/bin/python
    import runpy

    runpy.run_path("${../.}/scripts/resolve_route.py", run_name="__main__")
    EOF
    chmod +x $out/bin/modolia
  '';

  # Preserve the original import path during the Modolia rename.
  pythonImportsCheck = [ "model_router" ];

  meta = {
    description = "Deterministic, host-independent model-surface resolution";
    license = lib.licenses.asl20;
    mainProgram = "modolia";
  };
}
